"""Launch the local editor with its managed CPU engine, or use an existing engine."""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import venv
import webbrowser
from pathlib import Path
from urllib.request import urlopen
from http.server import ThreadingHTTPServer

from server import Handler
import node_manager

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine" / "ComfyUI"
ENV = ROOT / "engine" / ".venv"
PYTHON = ENV / "Scripts" / "python.exe"
READY = ENV / "ready-2.6-cpu"
BASE = "http://127.0.0.1:8188"
STUDIO = "http://127.0.0.1:8765"

def engine_api(path):
    with urlopen(BASE + path, timeout=3) as response:
        return json.load(response)

def online():
    try:
        return "system" in engine_api("/system_stats")
    except (OSError, ValueError):
        return False

def install():
    if READY.exists() and PYTHON.exists():
        return
    if sys.version_info[:2] != (3,12) or struct.calcsize("P") != 8:
        raise RuntimeError("This Windows package needs 64-bit Python 3.12.")
    if not shutil.which("git"):
        raise RuntimeError("Install Git for Windows and run start-local.bat again.")
    wheels = ROOT / "engine" / "windows-wheels"
    files = []
    for name, expected in json.loads((wheels / "sha256.json").read_text()).items():
        path = wheels / name
        with path.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual != expected:
            raise RuntimeError(f"Bundled wheel failed verification: {name}. Extract a fresh copy of the ZIP.")
        files.append(str(path))
    if not PYTHON.exists():
        venv.create(ENV, with_pip=True)
    log = ROOT / "setup.log"
    pip = [str(PYTHON), "-m", "pip", "--disable-pip-version-check", "--log", str(log),
           "install", "--no-cache-dir", "--retries", "4", "--timeout", "90", "--index-url", "https://pypi.org/simple"]
    # Resolve all requirements together so the resolver must respect the verified local wheels.
    args = pip + files + ["-r", "requirements.txt", "-r", "manager_requirements.txt"]
    for attempt in range(2):
        bad_hash = False
        with subprocess.Popen(args,cwd=ENGINE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                              text=True,errors="replace") as proc:
            for line in proc.stdout:
                print(line,end="",flush=True)
                bad_hash |= "DO NOT MATCH THE HASHES" in line.upper()
        if proc.returncode == 0:
            READY.touch()
            return
        if not bad_hash or attempt:
            raise RuntimeError(f"Installation stopped. See {log} for the package and download URL.")
        print("Hash mismatch. Retrying the download once without cache. Hash verification remains enabled.")

def start_engine(progress_dir):
    process = subprocess.Popen([str(PYTHON),str(ROOT / "backend" / "engine_progress.py"),"--cpu","--enable-manager-legacy-ui",
                                "--listen","127.0.0.1","--port","8188"],cwd=ENGINE, env=dict(os.environ, DOLORAIN_PROGRESS_DIR=progress_dir))
    try:
        for _ in range(240):
            if process.poll() is not None:
                raise RuntimeError("ComfyUI stopped during startup. See the engine log above.")
            if online():
                return process
            time.sleep(1)
        raise RuntimeError("ComfyUI did not start on port 8188.")
    except BaseException:
        if process.poll() is None:
            process.terminate()
            process.wait()
        raise

def main():
    engine = None
    with tempfile.TemporaryDirectory(prefix="dolorain-progress-") as progress_dir, ThreadingHTTPServer(("127.0.0.1",8765), Handler) as server:
        server.comfy = BASE
        server.progress_dir = progress_dir
        server.engine_lock = threading.RLock()
        def reload_engine():
            nonlocal engine
            if engine is None:
                return {"ready":False,"message":"Restart your separately launched ComfyUI and click Refresh."}
            queue = engine_api("/queue")
            if queue.get("queue_running") or queue.get("queue_pending") or node_manager.ACTIVE:
                return {"ready":False,"message":"Engine is busy. Restart after its queue finishes, then click Refresh."}
            if engine.poll() is None:
                engine.terminate()
                engine.wait(timeout=30)
            engine = start_engine(progress_dir)
            return {"ready":True}
        server.reload_engine = reload_engine
        try:
            if not online():
                install()
                config = ENGINE / "user" / "__manager" / "config.ini"
                config.parent.mkdir(parents=True, exist_ok=True)
                if not config.exists():
                    config.write_text("[default]\nallow_git_url_install = true\n",encoding="utf-8")
                engine = start_engine(progress_dir)
            print("Dolorain Studio is ready at " + STUDIO + ". Press Ctrl+C to stop.",flush=True)
            webbrowser.open(STUDIO)
            server.serve_forever()
        finally:
            if engine and engine.poll() is None:
                engine.terminate()
                engine.wait()
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        sys.exit(str(exc))
