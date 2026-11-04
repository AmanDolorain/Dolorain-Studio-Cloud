"""Local-only Dolorain Studio bridge. Python standard library; no credentials stored."""
import workflow_files
import node_manager
import threading
import base64
import hmac
import sys
import argparse
import json
import mimetypes
import os
import subprocess
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlencode, parse_qs

ROOT = Path(__file__).resolve().parent.parent
# Source checkout: reuse the experimental pipeline. A standalone Windows
# package without the optional pipeline still starts normally.
PIPELINE = ROOT.parent / 'pipeline'
if PIPELINE.is_dir():
    sys.path.insert(0, str(PIPELINE))
try:
    import box_engine
    import box_adapter
except ModuleNotFoundError as exc:
    if exc.name not in ('box_engine', 'box_adapter', 'bounded_flow', 'gpu_policy'):
        raise
    box_engine = None
    box_adapter = None
MAX_JSON = 5 * 1024 * 1024

def request_comfy(base, path, method='GET', body=None, content_type='application/json'):
    data = None if body is None else (json.dumps(body).encode() if content_type == 'application/json' else body)
    req = Request(base + path, data=data, method=method, headers={'Content-Type': content_type})
    with urlopen(req, timeout=25) as response:
        return response.read(), response.headers.get('Content-Type', 'application/json')

def build_prompt(workflow, schemas):
    """Build ComfyUI API prompt using actual installed node schemas, never guessed widget ordering."""
    nodes = {n['id']: n for n in workflow['nodes']}
    prompt = {}
    errors = []
    edges = {}
    for link in workflow['links']:
        target = (link[3], link[4])
        if target in edges:
            errors.append(f"Node #{link[3]} input slot {link[4]} has multiple wires")
        edges[target] = link
    dynamic_types = {'COMFY_AUTOGROW_V3', 'COMFY_DYNAMICCOMBO_V3',
                     'COMFY_DYNAMICGROUP_V3', 'COMFY_DYNAMICSLOT_V3'}
    for n in workflow['nodes']:
        if n.get('mode', 0) in (2, 4):
            continue  # muted/bypassed: refuse links to them below
        spec = schemas.get(n['type'])
        if not spec:
            errors.append(f"Node #{n['id']}: type {n['type']} not installed in the engine")
            continue
        schema = spec.get('input', {})
        declared = {**schema.get('required', {}), **schema.get('optional', {})}
        named = n.get('widgets_values_named') or {}
        values = n.get('widgets_values') or []
        # Widgets in UI JSON are not guaranteed to align with schema order;
        # prefer named widget values. Positional fallback only if unambiguous.
        widget_keys = [key for key, value in declared.items() if isinstance(value, (list, tuple)) and
                       value and (isinstance(value[0], list) or value[0] in ('INT', 'FLOAT', 'STRING', 'BOOLEAN', 'COMBO'))]
        positional_safe = len(values) == len(widget_keys)
        # Use the same graph edges as the canvas. Imported per-socket link IDs may be stale.
        wired = {}
        for i, port in enumerate(n.get('inputs', [])):
            edge = edges.get((n['id'], i))
            if edge is None:
                continue
            name = port['name']
            alias = (port.get('widget') or {}).get('name')
            if name not in declared and alias in declared:
                name = alias
            wired[name] = edge
        keys = list(declared)
        for key in dict.fromkeys([*wired, *named]):
            parent, dot, _ = key.partition('.')
            desc = declared.get(parent)
            if dot and key not in declared and desc and isinstance(desc[0], str) and desc[0] in dynamic_types:
                keys.append(key)
        params = {}
        for key in keys:
            link = wired.get(key)
            if link is not None:
                if link[1] not in nodes or nodes[link[1]].get('mode', 0) in (2, 4):
                    # Unavailable optional sockets do not invalidate the entire graph.
                    # A required socket must still be supplied before generation.
                    if key in schema.get('required', {}):
                        errors.append(f"Node #{n['id']} input {key}: disconnected or muted source")
                else:
                    params[key] = [str(link[1]), link[2]]
            elif key in named:
                params[key] = named[key]
            elif positional_safe and key in widget_keys:
                params[key] = values[widget_keys.index(key)]
            elif key in schema.get('required', {}) and not (declared[key][0] == 'COMFY_AUTOGROW_V3' and any(k.startswith(key + '.') for k in wired)):
                errors.append(f"Node #{n['id']} input {key}: missing required value; check node widgets")
        prompt[str(n['id'])] = {'class_type': n['type'], 'inputs': params}
    # ComfyUI may have additional validation constraints; its /prompt response is authoritative.
    return prompt, errors

class Handler(BaseHTTPRequestHandler):
    def send(self, code, obj, content_type='application/json'):
        data = json.dumps(obj, ensure_ascii=False).encode() if content_type == 'application/json' else obj
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length < 0 or length > MAX_JSON:
            raise ValueError('Request too large')
        return json.loads(self.rfile.read(length))

    def require_access(self, write=False):
        """Require browser credentials on the RunPod HTTP proxy.

        Only enabled when server.auth_secret is set. The proxy must provide HTTPS.
        ComfyUI remains on loopback. Never log or echo the password.
        """
        secret = getattr(self.server, 'auth_secret', None)
        if secret is None:
            return True
        supplied = self.headers.get('Authorization', '')
        if not hmac.compare_digest(supplied.encode('utf-8'), secret):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Dolorain Studio", charset="UTF-8"')
            self.send_header('Content-Length', '0')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return False
        if write:
            host = self.headers.get('Host', '')
            origin = self.headers.get('Origin', '')
            # Browser POST must originate from this exact HTTPS RunPod proxy host.
            if (not host or origin != 'https://' + host
                    or self.headers.get_content_type() != 'application/json'):
                self.send(403, {'error': 'HTTPS same-origin JSON requests only'})
                return False
        return True

    def do_GET(self):
        if not self.require_access():
            return
        try:
            url = urlsplit(self.path)
            if url.path in ('/', '/index.html'):
                return self.send(200, (ROOT/'index.html').read_bytes(), 'text/html; charset=utf-8')
            if url.path == '/brand/d-logo.svg':
                return self.send(200,(ROOT/'brand'/'d-logo.svg').read_bytes(),'image/svg+xml; charset=utf-8')
            if url.path in ('/manager_catalog.js', '/node_fields.js', '/canvas_size.js'):
                return self.send(200,(ROOT/url.path[1:]).read_bytes(),'application/javascript; charset=utf-8')
            if url.path == '/api/box/status':
                if box_engine is None:
                    return self.send(503, {'error':'Box Engine pipeline not installed in this deployment.'})
                return self.send(200, box_adapter.status())
            if url.path == '/api/workflows':
                return self.send(200,{'files':workflow_files.list_files(self.server.comfy, request_comfy)})
            if url.path == '/api/workflow':
                route=workflow_files.file_route(parse_qs(url.query).get('name',[''])[0])
                raw,_=request_comfy(self.server.comfy,route)
                return self.send(200,json.loads(raw))
            if url.path == '/api/packs':
                return self.send(200, {'packs': node_manager.catalog(self.server, updates=url.query=='updates=1')})
            if url.path.startswith('/api/install-status/'):
                job = node_manager.install_status(url.path.rsplit('/',1)[-1])
                return self.send(200 if job else 404, job or {'error':'Install job unavailable. Check the engine log.'})
            if url.path == '/api/status':
                try:
                    data, _ = request_comfy(self.server.comfy, '/system_stats')
                    metrics = {}
                    try:
                        result = subprocess.run(['nvidia-smi','--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total','--format=csv,noheader,nounits'], capture_output=True,text=True,timeout=2,check=True)
                        parts = [x.strip() for x in result.stdout.splitlines()[0].split(',')]
                        if len(parts) == 5:
                            metrics = {'name':parts[0], 'utilization_pct':int(parts[1]),'temperature_c':int(parts[2]),'memory_used_bytes':int(parts[3])*1024*1024,'memory_total_bytes':int(parts[4])*1024*1024}
                    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
                        pass
                    return self.send(200, {'connected': True, 'stats': json.loads(data), 'gpu_metrics': metrics})
                except (URLError, TimeoutError, HTTPError) as exc:
                    return self.send(200, {'connected': False, 'message': str(exc)})
            if url.path == '/api/history':
                data, _ = request_comfy(self.server.comfy, '/history')
                return self.send(200, json.loads(data))
            if url.path == '/api/schema':
                data, _ = request_comfy(self.server.comfy, '/object_info')
                return self.send(200, json.loads(data))
            if url.path == '/api/view':
                # Allow only ComfyUI's known view parameters, never arbitrary upstream URLs.
                q = parse_qs(url.query)
                clean = {k: q[k][0] for k in ('filename','subfolder','type') if k in q}
                if 'filename' not in clean or clean.get('type', 'output') not in ('output','temp','input'):
                    return self.send(400, {'error':'Invalid file request'})
                data, typ = request_comfy(self.server.comfy, '/view?' + urlencode(clean))
                return self.send(200, data, typ)
            self.send(404, {'error': 'Not found'})
        except Exception as exc:
            self.send(502, {'error': str(exc)})

    def do_POST(self):
        if not self.require_access(write=True):
            return
        try:
            if self.path in ('/api/install-pack','/api/reload-nodes','/api/workflow/save','/api/workflow/delete'):
                host = self.headers.get('Host','')
                origin = self.headers.get('Origin','')
                remote_auth = getattr(self.server, 'auth_secret', None) is not None
                local_only_operation = self.path in ('/api/install-pack', '/api/reload-nodes')
                if (self.headers.get_content_type() != 'application/json'
                        or (local_only_operation and (remote_auth
                             or urlsplit('//' + host).hostname not in ('127.0.0.1','localhost','::1')
                             or origin != 'http://' + host))
                        or (not remote_auth and
                            (urlsplit('//' + host).hostname not in ('127.0.0.1','localhost','::1')
                             or origin != 'http://' + host))):
                    return self.send(403, {'error':'Operation not permitted from this connection.'})
                data = self.body()
                with self.server.engine_lock:
                    if self.path.startswith('/api/workflow/'):
                        route=workflow_files.file_route(data.get('name'))
                        if self.path.endswith('/delete'):
                            request_comfy(self.server.comfy,route,'DELETE')
                        else:
                            doc=data.get('data')
                            if not isinstance(doc,dict) or not isinstance(doc.get('nodes'),list) or not isinstance(doc.get('links'),list):
                                raise ValueError('Expected a workflow graph.')
                            overwrite='true' if data.get('overwrite') is True else 'false'
                            request_comfy(self.server.comfy,route+'?overwrite='+overwrite,'POST',doc)
                        return self.send(200,{'ok':True})
                    if self.path == '/api/install-pack':
                        return self.send(202, node_manager.install(self.server,data))
                    job = node_manager.JOBS.get(data.get('job'),{})
                    if job.get('state') != 'done':
                        return self.send(409, {'error':'Install has not finished.'})
                    if job.get('reloaded'):
                        return self.send(200, {'ready':True})
                    if not hasattr(self.server,'reload_engine'):
                        return self.send(200, {'ready':False,'message':'Restart your GPU engine, then click Refresh.'})
                    result=self.server.reload_engine()
                    job['reloaded']=result['ready']
                    return self.send(200,result)
            if self.path == '/api/box/inspect':
                if box_engine is None:
                    return self.send(503, {'error':'Box Engine pipeline not installed in this deployment.'})
                return self.send(200, box_adapter.inspect_workflow(self.body()))
            if self.path == '/api/queue':
                workflow = self.body()
                schemas_raw, _ = request_comfy(self.server.comfy, '/object_info')
                prompt, errors = build_prompt(workflow, json.loads(schemas_raw))
                if errors:
                    return self.send(422, {'errors': errors, 'message':'Workflow requires correction before running'})
                with self.server.engine_lock:
                    data, _ = request_comfy(self.server.comfy, '/prompt', 'POST', {'prompt': prompt, 'client_id':'dolorain-studio'})
                return self.send(200, json.loads(data))
            if self.path == '/api/validate':
                workflow = self.body()
                schemas_raw, _ = request_comfy(self.server.comfy, '/object_info')
                prompt, errors = build_prompt(workflow, json.loads(schemas_raw))
                return self.send(200, {'valid':not errors,'errors':errors,'node_count':len(prompt)})
            self.send(404, {'error':'Not found'})
        except (HTTPError, URLError) as exc:
            details = exc.read().decode(errors='replace') if isinstance(exc, HTTPError) else str(exc)
            self.send(502, {'error':'GPU engine request failed','details':details[:4000]})
        except Exception as exc:
            self.send(400, {'error':str(exc)})

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--comfy',default='http://127.0.0.1:8188')
    parser.add_argument('--host',default='127.0.0.1',help='Bind local only by default; use SSH tunneling for remote access')
    args=parser.parse_args()
    if not (args.comfy.startswith('http://127.0.0.1:') or args.comfy.startswith('http://localhost:')):
        parser.error('ComfyUI URL must be loopback for this local-only bridge')
    password = os.environ.get('DSC_STUDIO_PASSWORD', '')
    if args.host not in ('127.0.0.1', 'localhost', '::1') and len(password) < 20:
        parser.error('Public Studio listener requires DSC_STUDIO_PASSWORD (20+ characters)')
    server=ThreadingHTTPServer((args.host,args.port),Handler)
    server.auth_secret = ('Basic ' + base64.b64encode(
        ('studio:' + password).encode('utf-8')).decode('ascii')).encode('ascii') if password else None
    server.engine_lock=threading.RLock()
    server.comfy=args.comfy
    print(f'Dolorain Studio: http://{args.host}:{args.port}  ->  {args.comfy}',flush=True)
    server.serve_forever()
