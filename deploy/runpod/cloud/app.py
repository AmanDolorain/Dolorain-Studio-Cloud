"""RunPod HTTP entry point. The original node frontend and its extension APIs share one origin."""
import asyncio
import base64
from collections import deque
from datetime import datetime, timezone
import hmac
import json
import os
from pathlib import Path
import re
import sys
import threading
from http.server import ThreadingHTTPServer
from urllib.parse import quote, urlencode, urlsplit

from aiohttp import ClientSession, ClientTimeout, DummyCookieJar, WSMsgType, web

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / 'studio'
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT.parent / 'pipeline')]
ENGINE = 'http://127.0.0.1:8188'
HOP = {'host','connection','upgrade','keep-alive','transfer-encoding','proxy-connection',
       'proxy-authorization','te','trailer','sec-websocket-key',
       'sec-websocket-version','sec-websocket-extensions','sec-websocket-protocol'}
EVENTS = deque(maxlen=120)
SECRET = re.compile(r'(?i)(?:password|token|authorization|api[_ -]?key|bearer|://[^ /]+@)')


def note(stage, message):
    clean = re.sub(r'\x1b\[[0-9;]*m', '', str(message)).strip()
    if SECRET.search(clean):
        clean = '[credential-bearing line omitted]'
    EVENTS.append(f'{datetime.now(timezone.utc):%H:%M:%S} UTC  {stage}  {clean[:450]}')


@web.middleware
async def access(req, handler):
    password = os.getenv('DSC_STUDIO_PASSWORD', '')
    if len(password) < 20:
        raise web.HTTPServiceUnavailable(text='Studio credentials are not configured')
    if password:
        expected = 'Basic ' + base64.b64encode(('studio:' + password).encode()).decode()
        if not hmac.compare_digest(req.headers.get('Authorization','').encode(), expected.encode()):
            raise web.HTTPUnauthorized(headers={'WWW-Authenticate':'Basic realm="Dolorain Studio"'})
    origin = req.headers.get('Origin')
    if origin and urlsplit(origin).netloc != req.host:
        raise web.HTTPForbidden()
    if req.headers.get('Sec-Fetch-Site') == 'cross-site' and req.method not in ('GET','HEAD'):
        raise web.HTTPForbidden()
    return await handler(req)


async def engine_ready(client):
    try:
        async with client.get(ENGINE + '/system_stats', timeout=2) as r:
            return r.status == 200 and 'devices' in await r.json()
    except Exception:
        return False


async def diagnostics(req):
    result = {}
    if req.method == 'POST':
        try:
            from box_adapter import inspect_workflow
            graph = await req.json()
            check = await asyncio.to_thread(inspect_workflow, graph)
            result['Studio adapter'] = (f"{check['node_count']} nodes, {check['checked_connections']} links. "
                                       + ('PASS' if check['valid_structure'] else str(check['warnings'])))
            types = sorted({n['type'] for n in graph['nodes'] if isinstance(n.get('type'), str)})
            if types:
                # Look up only registered node names, never fetch workflows, prompts or models.
                semaphore = asyncio.Semaphore(6)
                async def registered(name):
                    async with semaphore:
                        path = '/object_info/' + quote(name, safe='')
                        async with req.app['client'].get(ENGINE + path, timeout=4) as response:
                            if response.status != 200:
                                raise RuntimeError('node registry unavailable')
                            return name if name not in await response.json() else None
                checked = await asyncio.gather(*(registered(name) for name in types[:128]), return_exceptions=True)
                missing = [name for name in checked if isinstance(name, str)]
                if any(isinstance(value, Exception) for value in checked):
                    result['Installed node types'] = 'Unable to read the complete backend registry'
                else:
                    result['Installed node types'] = ('MISSING: ' + ', '.join(missing) if missing else 'All checked types registered')
                if len(types) > 128:
                    result['Installed node types'] += ' (first 128 types checked)'
        except Exception as e:
            result['Studio adapter'] = 'FAIL: ' + str(e)[:250]
    else:
        result['Studio adapter'] = 'No active graph supplied for inspection'
    try:
        from box_engine import BoxEngine, Packet
        received = []
        stats = await asyncio.to_thread(BoxEngine().transfer, [Packet(b'DSC',3)], lambda p: received.append(p.payload))
        result['Bounded transport'] = ('PASS: 3-byte test packet delivered' if stats.consumed == 1 and received == [b'DSC']
                                       else 'FAIL: packet acknowledgement mismatch')
    except Exception as e:
        result['Bounded transport'] = 'FAIL: ' + str(e)[:250]
    result['Backend adapter'] = 'NOT CONNECTED: Box transport is not wired into H3 inference'
    result['ComfyUI backend'] = 'READY: system_stats responded' if await engine_ready(req.app['client']) else 'UNAVAILABLE'
    return web.json_response({'layers': result, 'events': list(EVENTS)}, headers={'Cache-Control':'no-store'})


async def relay(src, dst):
    async for msg in src:
        if msg.type == WSMsgType.TEXT:
            await dst.send_str(msg.data)
        elif msg.type == WSMsgType.BINARY:
            await dst.send_bytes(msg.data)


async def handle(req):
    path = req.path
    if path == '/' and 'studio_canvas' not in req.query and req.headers.get('Sec-Fetch-Dest') != 'iframe':
        return web.FileResponse(HERE / 'studio.html', headers={'Cache-Control':'no-store'})
    if path == '/_studio/open-jupyter':
        import server as dashboard
        destination = dashboard.jupyter_proxy_url(type('PublicStudio', (), {'auth_secret': True}))
        if not destination:
            raise web.HTTPNotFound(text='Single login is not enabled for this Pod.')
        raise web.HTTPFound(destination + '?' + urlencode({'token':os.environ['JUPYTER_TOKEN']}),
                            headers={'Cache-Control':'no-store', 'Referrer-Policy':'no-referrer'})
    if path == '/_studio/workflow':
        return web.FileResponse(ROOT / 'H3_Workflow_Fast_FaceDetail5.json')
    if path == '/_studio/ready':
        return web.json_response({'ready': await engine_ready(req.app['client']), 'single_login': os.getenv('DSC_JUPYTER_SINGLE_LOGIN') == '1' and bool(os.getenv('RUNPOD_POD_ID'))})
    if path == '/_studio/diagnostics':
        return await diagnostics(req)
    legacy = path.startswith('/_studio/dashboard/')
    target = 'http://127.0.0.1:18766' if legacy else ENGINE
    route = req.raw_path[len('/_studio/dashboard'):] if legacy else req.raw_path
    if legacy and req.method != 'GET':
        # The dashboard bridge has privileged desktop-only maintenance endpoints.
        if req.path not in {'/_studio/dashboard/api/' + part for part in
                            ('workflow/save','workflow/delete','queue','validate','box/inspect')}:
            raise web.HTTPForbidden()
    headers = {k:v for k,v in req.headers.items() if k.lower() not in HOP}
    if os.getenv('DSC_STUDIO_PASSWORD') or legacy:
        headers = {k:v for k,v in headers.items() if k.lower() != 'authorization'}
    if 'Origin' in headers:
        headers['Origin'] = target
    client = req.app['client']
    url = target + route
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
        if legacy and path == '/_studio/dashboard/' and upstream.status == 200:
            # Scope the existing dashboard API to its own namespace.
            html = (await upstream.text()).replace("'/api/", "'/_studio/dashboard/api/")
            return web.Response(text=html, content_type='text/html')
        await out.prepare(req)
        async for chunk in upstream.content.iter_chunked(65536):
            await out.write(chunk)
        return out


async def run_child(stage, command, cwd=None):
    note(stage, 'Starting')
    proc = await asyncio.create_subprocess_exec(*command, cwd=cwd, stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.STDOUT)
    pending = bytearray()
    def publish(line):
        message = line.decode(errors='replace')
        print(message, flush=True)
        if re.search(r'\[OK\]|\[FAILED\]|error|exception|traceback|warning|cannot import|starting server|'
                     r'got prompt|prompt executed|failed to validate|not in list|return type mismatch|'
                     r'required input is missing|out of memory|device: cuda', message, re.I):
            note(stage, message)
    try:
        while chunk := await proc.stdout.read(8192):
            pending.extend(chunk)
            while b'\n' in pending:
                line, _, pending = pending.partition(b'\n')
                publish(line)
            if len(pending) > 32768:
                publish(pending[:2048])
                pending.clear()
        if pending:
            publish(pending)
        code = await proc.wait()
        note(stage, f'Process exited with status {code}')
        return code
    finally:
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), 5)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()


async def engine():
    try:
        if await run_child('GPU preflight', [sys.executable, str(HERE.parent / 'preflight.py')]):
            return
        workspace = Path('/workspace/dolorain')
        args = [sys.executable, 'main.py', '--listen', '127.0.0.1', '--port', '8188','--disable-auto-launch']
        for flag, directory in [('models','models'),('input','input'),('output','output'),('user','user')]:
            args.extend(['--' + flag + '-directory', str(workspace / directory)])
        await run_child('ComfyUI', args, cwd='/opt/dolorain/comfy')
    except OSError as e:
        note('Startup', f'FAIL: {e}')


async def services(app):
    import server as studio
    async with ClientSession(auto_decompress=False, cookie_jar=DummyCookieJar(),
                             timeout=ClientTimeout(total=None,sock_connect=10)) as client:
        app['client'] = client
        dashboard = ThreadingHTTPServer(('127.0.0.1',18766), studio.Handler)
        dashboard.comfy = ENGINE
        dashboard.engine_lock = threading.RLock()
        dashboard.auth_secret = None
        threading.Thread(target=dashboard.serve_forever, daemon=True).start()
        task = asyncio.create_task(engine())
        try:
            yield
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            await asyncio.to_thread(dashboard.shutdown)
            dashboard.server_close()


if __name__ == '__main__':
    app = web.Application(middlewares=[access], client_max_size=4*1024*1024)
    app.cleanup_ctx.append(services)
    app.router.add_route('*','/{path:.*}',handle)
    web.run_app(app, host='0.0.0.0', port=8765, access_log=None)
