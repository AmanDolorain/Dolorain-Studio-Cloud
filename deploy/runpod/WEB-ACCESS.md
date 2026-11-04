# RunPod browser access

Build the current main branch before deploying the template. Use the image entrypoint with no custom container start command. Mount the persistent volume at `/workspace`.

| RunPod HTTP port | Opens |
| --- | --- |
| 8765 | Dolorain Studio with the native node editor |
| 8888 | JupyterLab at `/lab` |

Studio uses username `studio` and `DSC_STUDIO_PASSWORD`. JupyterLab uses `DSC_JUPYTER_TOKEN` or `JUPYTER_PASSWORD`. Both secrets must be at least 20 characters. With `DSC_JUPYTER_SINGLE_LOGIN=1`, use the JupyterLab button inside the authenticated Studio session to open the lab without entering a second password. SSH is optional. Only the two HTTP service ports need to be exposed.

Use **Open H3 workflow** for the bundled example or import an existing graph in the native editor. Node plugins provide their own widgets, hooks and serialization. Missing plugins and model files must be provisioned independently. The Studio dashboard is also available for existing management features.

Open **Logs · Diagnostics**, then **Refresh** and **Copy report**. The panel checks the active graph through the Studio adapter, sends a three-byte CPU probe through the bounded transport, and reports the Box backend adapter integration separately from ComfyUI availability. It retains the latest 120 selected engine messages for this session and up to 80 browser execution events. Container Logs include earlier container or Jupyter startup failures.

A source commit does not update a running Pod. A successful image build and a deployment using the new image are required.
