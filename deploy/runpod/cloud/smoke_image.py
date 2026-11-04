"""Build-time check of the packaged browser services using CPU and no model weights."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[3]
env = dict(os.environ)
for key in ('PUBLIC_KEY','DSC_STUDIO_PASSWORD','DSC_JUPYTER_TOKEN','JUPYTER_TOKEN','JUPYTER_PASSWORD'):
    env.pop(key, None)

env['DSC_PUBLIC_TEST'] = '1'

def read(port, path):
    with urlopen(f'http://127.0.0.1:{port}' + path, timeout=6) as response:
        if '/login' in response.geturl():
            raise RuntimeError('Unexpected login page')
        return response.read()


if __name__ == '__main__':
    children = []
    try:
        children.append(subprocess.Popen(['bash', str(ROOT/'deploy/runpod/entrypoint.sh')], env=env))
        # The normal preflight detects the absence of a GPU on a standard image builder.
        # Exercise the pinned native frontend and core nodes with a separate CPU engine.
        children.append(subprocess.Popen([sys.executable,'main.py','--cpu','--listen','127.0.0.1',
                                          '--port','8188','--disable-auto-launch'], cwd='/opt/dolorain/comfy', env=env))
        deadline = time.monotonic() + 140
        while True:
            if any(p.poll() is not None for p in children):
                raise RuntimeError('A packaged service exited during startup')
            try:
                assert b'Dolorain Studio' in read(8765,'/')
                assert isinstance(json.loads(read(8888,'/api/sessions')), list)
                assert b'jupyter' in read(8888,'/lab').lower()
                assert json.loads(read(8765,'/_studio/ready'))['ready']
                assert b'<html' in read(8765,'/?studio_canvas=1').lower()
                assert b'app' in read(8765,'/scripts/app.js')
                extensions = json.loads(read(8765,'/extensions'))
                # Core ComfyUI can register extensions even without custom nodes;\n                # every extension it advertises must be reachable via Studio.
                for path in extensions:
                    parsed = urlsplit(path)
                    assert not parsed.netloc and parsed.path.startswith('/extensions/')
                    assert read(8765, path), f'Empty frontend extension: {path}'
                registry = json.loads(read(8765, '/object_info'))
                workflow = json.loads(read(8765, '/_studio/workflow'))
                required = {node['type'] for node in workflow['nodes']}
                missing = sorted(required - registry.keys())
                print(f'Native frontend: {len(extensions)} extension files. '
                      f'H3 workflow: {len(required) - len(missing)}/{len(required)} node types registered. '
                      f'Missing: {missing}', flush=True)
                core = {'LoadImage', 'SaveImage', 'CreateVideo', 'SaveVideo'}\n                assert core <= registry.keys(), f'Missing built-in ComfyUI nodes: {sorted(core - registry.keys())}'\n                # Third-party types in example workflows are intentionally optional.\n                # Native ComfyUI graph loading must display them as missing nodes,\n                # not reject the entire graph or silently replace their widgets.
                break
            except (OSError, ValueError, AssertionError, StopIteration):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(1)
        print('PASS: native editor, core nodes, reachable frontend extensions, Studio and Jupyter HTTP access')
    finally:
        for p in children:
            p.terminate()
        for p in children:
            try:
                p.wait(timeout=12)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
