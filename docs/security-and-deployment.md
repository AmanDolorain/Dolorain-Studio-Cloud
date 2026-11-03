# Deployment and security checklist

## Before renting a GPU
1. Choose a supported CUDA/PyTorch image. Confirm its exact Python version and startup behavior.
2. Keep GPU instances **off** until the scripts and model sources are verified.
3. Use persistent storage for model weights; verify provider storage billing.
4. Review the provider's Jupyter/SSH defaults; avoid running duplicate ComfyUI services.
5. ComfyUI port 8188 must be protected by provider authentication or a properly configured reverse proxy. **H3_PASSWORD is not recognized by ComfyUI automatically.** Merely setting this variable does not secure the service.
6. Never put access tokens, passwords, or private signed model links in this public repository.
7. Pin tested revisions before production. Fetching a moving `main` branch means new instances may receive untested changes.
8. After launch, run `scripts/check-platform.sh`, `scripts/smoke-test.sh`, and `scripts/check-h3-models.sh`.
9. Stop and delete idle instances when appropriate; inspect persistent volume charges separately.

## Current limitations
- No official H3 download URLs have been verified.
- H3 custom node GitHub URLs/tags are not yet verified.
- No provider-specific authenticated web proxy has been configured.
- No actual GPU generation has been tested.
