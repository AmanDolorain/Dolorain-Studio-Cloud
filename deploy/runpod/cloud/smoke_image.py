"""Build-time check of the packaged browser services using CPU and no model weights."""
import base64
import secrets
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
env = dict(os.environ)
for key in ('PUBLIC_KEY','DSC_STUDIO_PASSWORD','DSC_JUPYTER_TOKEN','JUPYTER_TOKEN','JUPYTER_PASSWORD'):
    env.pop(key, None)

env['DSC_STUDIO_PASSWORD'] = secrets.token_hex(24)
env['JUPYTER_PASSWORD'] = secrets.token_hex(24)

def read(port, path):
    auth = ('Basic ' + base64.b64encode(('studio:' + env['DSC_STUDIO_PASSWORD']).encode()).decode()
            if port == 8765 else 'token ' + env['JUPYTER_PASSWORD'])
    req = Request(f'http://127.0.0.1:{port}' + path, headers={'Authorization':auth})
    with urlopen(req, timeout=6) as response:
        if '/login' in response.geturl():
            raise RuntimeError('Unexpected login page')
        return response.read()


if __name__ == '__main__':
    children = []
    try:
        children.append(subprocess.Popen(['bash', str(ROOT/'deploy/runpod/entrypoint.sh')], env=env))
        # The normal preflight detects the absence of a GPU on a standard image builder.
        # Exercise the actual pinned frontend and node plugins with a separate CPU engine.
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
                player = next(path for path in extensions if path.endswith('/audio.js') and 'h3-audio-controller' in path.lower())
                assert b'createPlayer' in read(8765, player)
                assert 'H3AudioController' in json.loads(read(8765,'/object_info/H3AudioController'))
                break
            except (OSError, ValueError, AssertionError, StopIteration):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(1)
        print('PASS: native editor, original audio extension, Studio and Jupyter HTTP access')
    finally:
        for p in children:
            p.terminate()
        for p in children:
            try:
                p.wait(timeout=12)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
