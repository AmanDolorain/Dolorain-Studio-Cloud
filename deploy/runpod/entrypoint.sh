#!/usr/bin/env bash
set -Eeuo pipefail
# No network access, package installation, model download or source update on startup.
# Keep the established authentication boundary on public RunPod proxies.
export JUPYTER_TOKEN="${DSC_JUPYTER_TOKEN:-${JUPYTER_PASSWORD:-${JUPYTER_TOKEN:-}}}"
if [[ ${#JUPYTER_TOKEN} -lt 20 || -z "${DSC_STUDIO_PASSWORD:-}" || ${#DSC_STUDIO_PASSWORD} -lt 20 ]]; then
  echo '[FAILED] Configure Studio password and Jupyter token (20+ characters each).'
  exit 42
fi
studio_pid=""; jupyter_pid=""; ssh_pid=""
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
mkdir -p /workspace/dolorain/{models,input,output,user}
finish() {
  trap - EXIT INT TERM
  for pid in "$studio_pid" "$jupyter_pid" "$ssh_pid"; do
    if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi
  done
}
trap finish EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
python /opt/dolorain/src/deploy/runpod/cloud/app.py &
studio_pid=$!
python -m jupyterlab --ip=0.0.0.0 --port=8888 --no-browser --allow-root \
  --ServerApp.port_retries=0 --ServerApp.default_url=/lab --ServerApp.root_dir=/workspace \
  --ServerApp.allow_remote_access=True --ServerApp.trust_xheaders=True \
  --ServerApp.terminals_enabled=True &
jupyter_pid=$!
echo '[INFO] Studio HTTP 8765 · JupyterLab HTTP 8888 · native engine on loopback'
wait -n "$studio_pid" "$jupyter_pid"
echo '[STOP] A web service exited'
exit 1
