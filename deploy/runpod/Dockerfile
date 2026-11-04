# Dolorain Studio / CUDA 13.2 compatibility-stage image. Not yet hardware-verified.
# Own packaging and UI. CUDA, PyTorch and temporary headless inference remain third-party.
FROM nvidia/cuda:13.2.1-cudnn-runtime-ubuntu24.04
LABEL org.opencontainers.image.title="Dolorain Studio" org.opencontainers.image.source="https://github.com/AmanDolorain/Dolorain-Studio-Cloud"
ARG DEBIAN_FRONTEND=noninteractive
ARG COMFY_REF=56f179f6c50dad0c4c860ae4da427415c8e86415
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PATH="/opt/dolorain/venv/bin:/usr/local/cuda/bin:$PATH"
ENV DSC_COMFY_DIR=/opt/dolorain/comfy DSC_REPO_DIR=/opt/dolorain/src DSC_ROOT=/workspace/dolorain
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git python3 python3-venv python3-pip ffmpeg tini openssh-server && rm -rf /var/lib/apt/lists/* && python3 -m venv /opt/dolorain/venv
# Restrict torch to the CUDA 13.2 wheel index, not CUDA 12.x.
RUN python -m pip install --no-cache-dir torch==2.13.0 torchvision==0.28.0 --index-url https://download.pytorch.org/whl/cu132 && python -c "import torch; assert torch.version.cuda=='13.2'"
# Pinned inference engine and native node frontend, hosted through Studio.
RUN git clone --filter=blob:none https://github.com/Comfy-Org/ComfyUI.git /opt/dolorain/comfy && git -C /opt/dolorain/comfy checkout --detach "$COMFY_REF" && test "$(git -C /opt/dolorain/comfy rev-parse HEAD)" = "$COMFY_REF"
# Install the pinned checkout's requirements.
RUN python -m pip install --no-cache-dir -r /opt/dolorain/comfy/requirements.txt && python -c "import torch, pydantic, pydantic_settings; assert torch.version.cuda=='13.2'" && python -m pip check
WORKDIR /opt/dolorain/src
COPY . /opt/dolorain/src/
# Preserve original developer widgets: install the node packages used by the shipped graph.
# Third-party Pixaroma is pinned to the exact commit recorded by the H3 workflow.
# No unknown H3 Connector or model dependencies are silently added.
RUN git clone https://github.com/AmanDolorain/H3-Video-Controller.git /opt/dolorain/comfy/custom_nodes/H3-Video-Controller && \
    git -C /opt/dolorain/comfy/custom_nodes/H3-Video-Controller checkout --detach 01e132b11c0df35c3d204fac1d1ea21dd904d314 && \
    git clone https://github.com/AmanDolorain/H3-Simple-Prompt.git /opt/dolorain/comfy/custom_nodes/H3-Simple-Prompt && \
    git -C /opt/dolorain/comfy/custom_nodes/H3-Simple-Prompt checkout --detach e2273850988fb3aef8f86a445fa0091794e343cc && \
    git clone https://github.com/AmanDolorain/H3-Audio-Controller.git /opt/dolorain/comfy/custom_nodes/H3-Audio-Controller && \
    git -C /opt/dolorain/comfy/custom_nodes/H3-Audio-Controller checkout --detach 0ea2c755feef485c51f4226c5f753686a362e8ee
# PixaromaLoadVideo and its playable widget come from the real Pixaroma extension,
# not a replacement HTML input. Keep all developer frontend assets registered.
RUN git clone --filter=blob:none https://github.com/pixaroma/ComfyUI-Pixaroma.git /opt/dolorain/comfy/custom_nodes/ComfyUI-Pixaroma && \
    git -C /opt/dolorain/comfy/custom_nodes/ComfyUI-Pixaroma checkout --detach 99202b56db46b3a9194f9449464fa76e5af9c1cb && \
    test "$(git -C /opt/dolorain/comfy/custom_nodes/ComfyUI-Pixaroma rev-parse HEAD)" = "99202b56db46b3a9194f9449464fa76e5af9c1cb" && \
    python -m pip install --no-cache-dir -r /opt/dolorain/comfy/custom_nodes/ComfyUI-Pixaroma/requirements.txt && python -m pip check
# Optional SSH uses public keys.
RUN mkdir -p /run/sshd && printf 'PermitRootLogin prohibit-password\nPasswordAuthentication no\nKbdInteractiveAuthentication no\nAllowTcpForwarding local\nGatewayPorts no\nX11Forwarding no\nPermitTunnel no\n' > /etc/ssh/sshd_config.d/dolorain.conf

# JupyterLab Terminal for operator diagnostics (no extensions or auto-update).
RUN python -m pip install --no-cache-dir jupyterlab==4.4.10 && python -m pip check
RUN python -m unittest discover -s studio/tests -p 'test_*.py' -v
RUN chmod +x deploy/runpod/entrypoint.sh && mkdir -p /workspace
RUN python -m unittest discover -s deploy/runpod/cloud -v
RUN --mount=type=tmpfs,target=/workspace --mount=type=tmpfs,target=/root/.local python deploy/runpod/cloud/smoke_image.py
# Studio HTTP is exposed through the RunPod HTTPS proxy; SSH remains optional.
EXPOSE 8765 8888 22
ENTRYPOINT ["/usr/bin/tini","-s","--","/bin/bash","/opt/dolorain/src/deploy/runpod/entrypoint.sh"]
