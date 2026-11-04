#!/usr/bin/env bash
set -Eeuo pipefail
# No network access, package installation, model download or source update on startup.
# Require the operator's existing SSH public key; refuse unprotected deployment.
if [[ -z "$PUBLIC_KEY" || ! "$PUBLIC_KEY" =~ ^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp256)[[:space:]] ]]; then
  echo "[FAILED] Set PUBLIC_KEY to your SSH public key. No unauthenticated Studio port will open."
  exit 41
fi
install -d -m 700 /root/.ssh
printf '%s\n' "$PUBLIC_KEY" > /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
ssh-keygen -A >/dev/null
/usr/sbin/sshd -D -e &
ssh_pid=$!
python /opt/dolorain/src/deploy/runpod/preflight.py
# Models / inputs / outputs persist ONLY if the provider has mounted /workspace.
# Avoid mistaking ephemeral storage for permanent storage.
if [[ "$(stat -c %m /workspace)" == "/" ]]; then
  echo "[WARNING] /workspace may not be a separate persistent volume; verify RunPod volume before storing models."
fi
mkdir -p /workspace/dolorain/models /workspace/dolorain/input /workspace/dolorain/output /workspace/dolorain/user
finish() {
  trap - EXIT INT TERM
  [[ -z "$ssh_pid" ]] || kill "$ssh_pid" 2>/dev/null || true\n  [[ -z "$studio_pid" ]] || kill "$studio_pid" 2>/dev/null || true
  [[ -z "$engine_pid" ]] || kill "$engine_pid" 2>/dev/null || true
}
engine_pid=""; studio_pid=""; ssh_pid=""
trap finish EXIT INT TERM
(
 cd /opt/dolorain/comfy
 exec python main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch --models-directory /workspace/dolorain/models --input-directory /workspace/dolorain/input --output-directory /workspace/dolorain/output --user-directory /workspace/dolorain/user
) &
engine_pid=$!
python /opt/dolorain/src/studio/backend/server.py --host 127.0.0.1 --port 8765 --comfy http://127.0.0.1:8188 &
studio_pid=$!
echo "[INFO] Dolorain Studio: 127.0.0.1:8765 (SSH tunnel only)"
echo "[INFO] Headless backend: 127.0.0.1:8188 (not publicly exposed)"
wait -n "$engine_pid" "$studio_pid" "$ssh_pid"
echo "[STOP] One process exited; stopping remaining process."
exit 1
