#!/usr/bin/env bash
set -Eeuo pipefail
# No network access, package installation, model download or source update on startup.
# Studio web UI is protected with a long password over RunPod's HTTPS proxy.
# SSH is optional, not needed for one-click browser access.
if [[ -z "${DSC_STUDIO_PASSWORD:-}" || ${#DSC_STUDIO_PASSWORD} -lt 20 ]]; then
  echo '[FAILED] DSC_STUDIO_PASSWORD must be at least 20 characters.'
  exit 42
fi
ssh_pid=""
if [[ -n "${PUBLIC_KEY:-}" ]]; then
  if [[ ! "$PUBLIC_KEY" =~ ^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp256)[[:space:]] ]]; then
    echo '[FAILED] Invalid SSH public key format.'
    exit 41
  fi
  install -d -m 700 /root/.ssh
  printf '%s\n' "$PUBLIC_KEY" > /root/.ssh/authorized_keys
  chmod 600 /root/.ssh/authorized_keys
  ssh-keygen -A >/dev/null
  /usr/sbin/sshd -D -e &
  ssh_pid=$!
fi
# Jupyter exposes a full shell: require a distinct, long token.
# RunPod can inject JUPYTER_PASSWORD; operator may set DSC_JUPYTER_TOKEN instead.
export JUPYTER_TOKEN="${DSC_JUPYTER_TOKEN:-${JUPYTER_PASSWORD:-}}"
if [[ ${#JUPYTER_TOKEN} -lt 20 ]]; then
  echo '[FAILED] Set JUPYTER_PASSWORD or DSC_JUPYTER_TOKEN (20+ characters) for JupyterLab.'
  exit 43
fi
python /opt/dolorain/src/deploy/runpod/preflight.py
# Models / inputs / outputs persist ONLY if the provider has mounted /workspace.
# Avoid mistaking ephemeral storage for permanent storage.
if [[ "$(stat -c %m /workspace)" == "/" ]]; then
  echo "[WARNING] /workspace may not be a separate persistent volume; verify RunPod volume before storing models."
fi
mkdir -p /workspace/dolorain/models /workspace/dolorain/input /workspace/dolorain/output /workspace/dolorain/user
finish() {
  trap - EXIT INT TERM
  [[ -z "$jupyter_pid" ]] || kill "$jupyter_pid" 2>/dev/null || true
  [[ -z "$ssh_pid" ]] || kill "$ssh_pid" 2>/dev/null || true
  [[ -z "$studio_pid" ]] || kill "$studio_pid" 2>/dev/null || true
  [[ -z "$engine_pid" ]] || kill "$engine_pid" 2>/dev/null || true
}
engine_pid=""; studio_pid=""; ssh_pid=""; jupyter_pid=""
trap finish EXIT INT TERM
(
 cd /opt/dolorain/comfy
 exec python main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch --models-directory /workspace/dolorain/models --input-directory /workspace/dolorain/input --output-directory /workspace/dolorain/output --user-directory /workspace/dolorain/user
) &
engine_pid=$!
python /opt/dolorain/src/studio/backend/server.py --host 0.0.0.0 --port 8765 --comfy http://127.0.0.1:8188 &
studio_pid=$!
# RunPod HTTPS proxy -> authenticated Jupyter terminal; XSRF remains enabled.
python -m jupyterlab --ip=0.0.0.0 --port=8888 --no-browser --allow-root \
  --ServerApp.root_dir=/workspace \
  --ServerApp.allow_remote_access=True \
  --ServerApp.trust_xheaders=True \
  --ServerApp.terminals_enabled=True &
jupyter_pid=$!
echo "[INFO] JupyterLab: HTTP 8888 via RunPod HTTPS proxy (token-protected)"
echo "[INFO] Dolorain Studio: HTTP 8765 via RunPod HTTPS proxy (password-protected)"
echo "[INFO] Headless backend: 127.0.0.1:8188 (not publicly exposed)"
if [[ -n "$ssh_pid" ]]; then
  wait -n "$engine_pid" "$studio_pid" "$jupyter_pid" "$ssh_pid"
else
  wait -n "$engine_pid" "$studio_pid" "$jupyter_pid"
fi
echo "[STOP] One process exited; stopping remaining process."
exit 1
