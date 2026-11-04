# Dolorain Studio — RunPod direct-click services

**Candidate only until a new Docker image build passes and an authorized Pod test succeeds.**

## One-click launch from RunPod Connect

- HTTP port **8765**, label **Dolorain Studio**. Browser Basic authentication user: `studio`; password: `DSC_STUDIO_PASSWORD`.
- HTTP port **8888**, label **JupyterLab Terminal**. Authenticate using `DSC_JUPYTER_TOKEN` (or `JUPYTER_PASSWORD`). JupyterLab can execute arbitrary terminal commands as root inside the container. Never use an empty or shared token. Jupyter authentication remains enabled, including XSRF protections.
- TCP port **22**, label **SSH**, optional; public key `PUBLIC_KEY` enables SSH login.
- **8188 must stay unexposed** (headless inference backend binds loopback).
- Image entrypoint launches three services: headless ComfyUI on loopback, password-protected Studio, token-protected JupyterLab. No model downloads or installs at Pod boot.
- RunPod HTTP proxy provides HTTPS externally. Neither the password nor Jupyter token should be placed in GitHub source, logs or shared screenshots.

## Existing RTX 3090 — do not release GPU automatically

Updating this GitHub repository, publishing a new Docker image, or editing the template **does not retrofit an already running Pod**. Do not stop/terminate an RTX 3090 merely for a web-button change if preserving the scarce price matters. Stop/redeploy may release the GPU to other customers, and the existing Pod may not permit new HTTP ports without restart. Paying for an idle Running Pod still incurs hourly charges.

**First finish image build while preserving existing Pod**. Then inspect RunPod's actual edit/redeploy options to decide whether an in-place update is supported. Do not assume. Until then, old-image SSH remains the available management route.

## Required environment variables for new image

`DSC_STUDIO_PASSWORD` = strong unique password of 20+ characters. Required.

`DSC_JUPYTER_TOKEN` = different unique token of 20+ characters, or use `JUPYTER_PASSWORD`. Required.

`PUBLIC_KEY` = optional SSH public key when SSH is needed. No private key.

A successful build does not establish security in production. Validate RunPod proxy behavior, authentication denial paths, same-origin POST rules, Jupyter terminals, GPU preflight and workflow operations on an approved Pod.

## Future direction

JupyterLab is a **temporary operator/dev tool**, not the customer-facing product. Dolorain Studio remains the primary UI. As the native inference engine stabilizes, production images should omit Jupyter and optional SSH by default and expose them only in diagnostic/developer variants.
