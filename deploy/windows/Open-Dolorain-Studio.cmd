@echo off
setlocal
set "DOLORAIN_LAUNCHER=%~f0"
powershell.exe -NoProfile -Command "$s=[IO.File]::ReadAllText($env:DOLORAIN_LAUNCHER);$p=$s -split '(?m)^#==POWERSHELL==\r?$',2;$q=$p[1] -split '(?m)^#==PYTHON==\r?$',2;& ([ScriptBlock]::Create($q[0]))"
exit /b %errorlevel%
#==POWERSHELL==
$ErrorActionPreference = 'Stop'
$dir = Join-Path $env:LOCALAPPDATA 'DolorainStudio'
$config = Join-Path $dir 'last-pod-ssh.txt'
function Open-Pod($line) {
    if ($line -notmatch '(?:^|\s)(root@[A-Za-z0-9.-]+)(?:\s|$)') { throw 'Paste the SSH over exposed TCP command from RunPod Connect.' }
    $target = $Matches[1]
    if ($target -like '*@ssh.runpod.io') { throw 'Choose SSH over exposed TCP, which supports port forwarding.' }
    if ($line -notmatch '(?:^|\s)-p\s+(\d+)(?:\s|$)') { throw 'The TCP port is missing.' }
    $port = [int]$Matches[1]
    if ($port -lt 1 -or $port -gt 65535) { throw 'Invalid TCP port.' }
    $sshArgs = @('-tt','-o','ExitOnForwardFailure=yes','-o','ConnectTimeout=10','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2','-p',"$port")
    if ($line -match '(?:^|\s)-i\s+(?:"([^"]+)"|''([^'']+)''|(\S+))') {
        $key = @($Matches[1],$Matches[2],$Matches[3]) | Where-Object { $_ } | Select-Object -First 1
        if ($key.StartsWith('~/') -or $key.StartsWith('~\')) { $key = Join-Path $env:USERPROFILE $key.Substring(2) }
        $sshArgs += @('-i',$key)
    }
    $source = [IO.File]::ReadAllText($env:DOLORAIN_LAUNCHER) -split '(?m)^#==PYTHON==\r?$',2
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($source[1]))
    $remote = "exec /opt/dolorain/venv/bin/python -c `"import base64;exec(compile(base64.b64decode('$encoded'),'<studio-session>','exec'))`""
    $sshArgs += @('-L','127.0.0.1:18765:127.0.0.1:18765','-L','127.0.0.1:18766:127.0.0.1:18766','-L','127.0.0.1:18888:127.0.0.1:8888',$target,$remote)
    & ssh.exe @sshArgs | ForEach-Object {
        if ($_.Trim() -eq 'DOLORAIN_READY') {
            [void][IO.Directory]::CreateDirectory($dir)
            [IO.File]::WriteAllText($config,$line)
            Start-Process 'http://127.0.0.1:18765/_studio/'
            Start-Process 'http://127.0.0.1:18765/_studio/jupyter'
            Write-Host 'Studio and Jupyter opened. Keep this window open while working.'
        } else { Write-Host $_ }
    }
    if ($LASTEXITCODE -ne 0) { throw 'SSH session ended. Check that the Pod is running and the TCP address and key are correct.' }
}
try {
    $line = if (Test-Path $config) { [IO.File]::ReadAllText($config) } else { '' }
    if ($line) {
        try { Open-Pod $line; return } catch { Write-Host $_.Exception.Message }
    }
    $line = Read-Host 'RunPod > Connect > SSH over exposed TCP. Paste the SSH command'
    Open-Pod $line
} catch { Write-Host $_.Exception.Message; [void](Read-Host 'Press Enter to close') }

#==PYTHON==
"""Private Studio session for one SSH connection. No installs or model downloads."""
import asyncio
import json
import os
import threading
from http.server import ThreadingHTTPServer
import sys
from pathlib import Path
from urllib.parse import urlencode

from aiohttp import ClientSession, ClientTimeout, DummyCookieJar, WSMsgType, web

ENGINE = 'http://127.0.0.1:8188'
ORIGIN = 'http://127.0.0.1:18765'
ROOT = Path('/opt/dolorain/src/studio')
PAGE = """<!doctype html><meta charset="utf-8"><title>Dolorain Studio</title>
<style>html,body{margin:0;height:100%;font:14px system-ui;background:#1b1e21;color:#e9eaec}
body{display:flex;flex-direction:column}header{display:flex;align-items:center;gap:14px;padding:7px 12px;border-bottom:1px solid #43484e}
button,a{font:inherit;color:inherit;background:#303438;border:1px solid #616970;border-radius:5px;padding:5px 9px;text-decoration:none;cursor:pointer}
iframe{flex:1;width:100%;border:0}#msg{font-size:12px}</style>
<header><strong>Dolorain Studio</strong><button id="example">Open H3 workflow</button>
<a href="http://127.0.0.1:18766/" target="_blank" rel="noreferrer">Studio dashboard · Box Engine</a><button id="theme">Light / Dark</button><a href="/_studio/jupyter" target="_blank" rel="noreferrer">JupyterLab</a>
<span id="msg"></span></header><iframe title="Original node editor" src="/?studio_canvas=1"></iframe>
<script type="module">
const frame=document.querySelector('iframe'),msg=document.querySelector('#msg');
async function app(){const win=frame.contentWindow;const module=await win.Function('return import("/scripts/app.js")')();
if(!module.app.graph)throw Error('Editor is still starting.');return module.app}
document.querySelector('#example').onclick=async()=>{try{
const editor=await app();if(!confirm('Open the H3 example in the editor? Save current edits first.'))return;
const r=await fetch('/_studio/workflow');if(!r.ok)throw Error('H3 example unavailable.');
await editor.loadGraphData(await r.json());msg.textContent='H3 workflow opened';
}catch(e){msg.textContent=e.message}};
document.querySelector('#theme').onclick=async()=>{try{const settings=(await app()).ui.settings;
const next=settings.getSettingValue('Comfy.ColorPalette')==='light'?'dark':'light';
await settings.setSettingValue('Comfy.ColorPalette',next);
document.body.style.background=next==='light'?'#f5f6f7':'#1b1e21';
document.body.style.color=next==='light'?'#25292d':'#e9eaec';
}catch(e){msg.textContent=e.message}};
</script>"""
HOP = {'host','connection','upgrade','keep-alive','transfer-encoding','proxy-connection',
       'proxy-authorization','te','trailer','authorization','sec-websocket-key',
       'sec-websocket-version','sec-websocket-extensions','sec-websocket-protocol'}


def jupyter_url():
    from jupyter_server.serverapp import list_running_servers
    for server in list_running_servers():
        if server.get('port') == 8888:
            token = server.get('token') or os.getenv('JUPYTER_TOKEN') or os.getenv('DSC_JUPYTER_TOKEN') or os.getenv('JUPYTER_PASSWORD')
            base = 'http://127.0.0.1:18888/lab'
            return base + ('?' + urlencode({'token': token}) if token else '')
    raise web.HTTPServiceUnavailable(text='Jupyter has not started on port 8888.')


async def relay(src, dst):
    async for msg in src:
        if msg.type == WSMsgType.TEXT:
            await dst.send_str(msg.data)
        elif msg.type == WSMsgType.BINARY:
            await dst.send_bytes(msg.data)


async def handle(req):
    if req.host != '127.0.0.1:18765' or req.headers.get('Origin', ORIGIN) != ORIGIN:
        raise web.HTTPForbidden()
    if req.headers.get('Sec-Fetch-Site') == 'cross-site' and req.path != '/':
        raise web.HTTPForbidden()
    if req.path == '/_studio/':
        return web.Response(text=PAGE, content_type='text/html')
    if req.path == '/_studio/workflow':
        return web.FileResponse(ROOT / 'H3_Workflow_Fast_FaceDetail5.json')
    if req.path == '/_studio/jupyter':
        raise web.HTTPFound(jupyter_url(), headers={'Cache-Control':'no-store','Referrer-Policy':'no-referrer'})
    headers = {k:v for k,v in req.headers.items() if k.lower() not in HOP}
    if 'Origin' in headers:
        headers['Origin'] = ENGINE
    client = req.app['client']
    url = ENGINE + req.raw_path
    if req.headers.get('Upgrade','').lower() == 'websocket':
        async with client.ws_connect(url, headers=headers, max_msg_size=0) as upstream:
            ws = web.WebSocketResponse(max_msg_size=0)
            await ws.prepare(req)
            tasks = [asyncio.create_task(relay(ws, upstream)), asyncio.create_task(relay(upstream, ws))]
            try:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                await ws.close()
            return ws
    async with client.request(req.method, url, headers=headers, allow_redirects=False,
                              data=req.content if req.can_read_body else None) as upstream:
        out = web.StreamResponse(status=upstream.status)
        for key,val in upstream.headers.items():
            if key.lower() not in HOP:
                out.headers.add(key,val)
        await out.prepare(req)
        async for chunk in upstream.content.iter_chunked(65536):
            await out.write(chunk)
        return out


def dashboard():
    sys.path.insert(0, str(ROOT / 'backend'))
    import server as studio
    server = ThreadingHTTPServer(('127.0.0.1', 18766), studio.Handler)
    server.comfy = ENGINE
    server.auth_secret = None  # Private loopback server behind the user's SSH tunnel.
    server.engine_lock = threading.RLock()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


async def main():
    async with ClientSession(auto_decompress=False, cookie_jar=DummyCookieJar(),
                             timeout=ClientTimeout(total=None,sock_connect=12)) as client:
        app = web.Application()
        app['client'] = client
        app.router.add_route('*','/{path:.*}',handle)
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        try:
            await web.TCPSite(runner, '127.0.0.1', 18765).start()
            studio = dashboard()
            print('DOLORAIN_READY', flush=True)
            try:
                await asyncio.Event().wait()
            finally:
                studio.shutdown()
                studio.server_close()
        finally:
            await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
