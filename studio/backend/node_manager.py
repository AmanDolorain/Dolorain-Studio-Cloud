"""A narrow bridge to the bundled ComfyUI Manager's catalog and install APIs."""
from pathlib import Path
from engine_progress import metric_path
import json
import html
import re
import threading
import time
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

GITHUB = re.compile(r'https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+/?')
LOCK = threading.Lock()
JOBS = {}
ACTIVE = {}

def upstream(base, path, payload=None, plain=False, timeout=90):
    body = None if payload is None else (payload.encode() if plain else json.dumps(payload).encode())
    req = Request(base + path, data=body, headers={'Content-Type': 'text/plain' if plain else 'application/json'})
    try:
        with urlopen(req, timeout=timeout) as r:
            raw = r.read()
    except HTTPError as exc:
        if exc.code == 403 and plain:
            raise ValueError("GitHub installs are disabled by this Manager. Enable allow_git_url_install in its local config and restart.") from exc
        detail = exc.read(800).decode(errors='replace')
        raise ValueError(f"Manager HTTP {exc.code}. {detail}") from exc
    return json.loads(raw) if raw.strip() else {}

def catalog(server, updates=False):
    packs = upstream(server.comfy, '/v2/customnode/getlist?mode=cache&skip_update='+('false' if updates else 'true'))
    mapping = upstream(server.comfy, '/v2/customnode/getmappings?mode=cache')
    server.catalog_snapshot = packs
    result = []
    for key, row in packs['node_packs'].items():
        repo = row.get('repository') or next(iter(row.get('files') or []), '')
        keys = [key, row.get('id'), repo]
        types = sorted({name for k in keys if k in mapping for name in mapping[k][0]})
        result.append(dict(key=key, id=row.get('id') or key, name=row.get('title') or key,
                           author=row.get('author'), version=row.get('version'), state=row.get('state'),
                           description=html.unescape(re.sub(r'<[^>]+>', ' ', row.get('description') or '')).strip(),
                           updateAvailable=str(row.get('update-state','')).lower()=='true', updated=row.get('last_update'), stars=row.get('stars'), installType=row.get('install_type'),
                           repository=repo, types=types, failed=bool(row.get('import-fail'))))
    return result

def install_status(job):
    with LOCK:
        item = JOBS.get(job)
        if item is None:
            return None
        result = dict(item)
    record = result.pop('_record', None)
    roots = result.pop('_roots', [])
    if result['state'] != 'working':
        return result
    try:
        if record and record.exists():
            data = json.loads(record.read_text())
            size = data['received'] if data.get('finished') else Path(data['archive']).stat().st_size
            result.update(received=size, total=data.get('total'), message=(
                'Download complete · finishing installation' if data.get('finished') else 'Downloading node pack'))
            return result
        for root in roots:
            objects = root / '.git' / 'objects'
            if objects.is_dir():
                size = sum(f.stat().st_size for f in objects.glob('*/*') if f.is_file())
                result.update(diskBytes=size, message='Installing Git repository')
                break
    except (OSError, ValueError, KeyError):
        pass
    return result

def install(server, data):
    action = data.get('action','install')
    if action not in ('install','update','uninstall'):
        raise ValueError('Unknown pack operation.')
    repo = data.get('github')
    if repo is not None and action != 'install':
        raise ValueError('Choose the installed pack in the catalog.')
    if repo is not None:
        if not isinstance(repo,str) or not GITHUB.fullmatch(repo) or repo.rstrip('/').split('/')[-1] in ('.','..'):
            raise ValueError('Enter an HTTPS GitHub repository URL with an owner and repository name.')
        repo = repo.rstrip('/').removesuffix('.git')
        identity = repo.lower()
    else:
        key = data.get('key')
        snapshot = getattr(server,'catalog_snapshot',{})
        row = snapshot.get('node_packs',{}).get(key)
        if not row:
            raise ValueError('Refresh the catalog and select a pack.')
        if action=='install' and row.get('state') in ('enabled','installed'):
            raise ValueError('This pack is already installed.')
        if action!='install' and row.get('state') not in ('enabled','installed','disabled'):
            raise ValueError('This pack is not installed. Refresh the catalog.')
        if action=='update' and str(row.get('update-state','')).lower()!='true':
            raise ValueError('No update reported. Refresh the catalog.')
        identity = (row.get('repository') or next(iter(row.get('files') or []),key)).lower().rstrip('/').removesuffix('.git')
    with LOCK:
        if identity in ACTIVE:
            return {'job':ACTIVE[identity]}
        job = uuid.uuid4().hex
        ACTIVE[identity] = job
        directory = getattr(server, 'progress_dir', None)
        node_id = (row.get('id') or key) if repo is None else identity.split('/')[-1]
        record = metric_path(directory, node_id) if directory else None
        if record:
            record.unlink(missing_ok=True)
        custom = Path(__file__).resolve().parents[1] / 'engine' / 'ComfyUI' / 'custom_nodes'
        names = {node_id, (repo or identity).rstrip('/').split('/')[-1]}
        roots = [custom / n for n in names if re.fullmatch(r'[\w.-]+', n) and n not in ('.','..')]
        JOBS[job] = dict(state='working', message={'install':'Preparing node pack','uninstall':'Removing node pack','update':'Updating node pack'}[action],
                         _record=record, _roots=roots if directory and action == 'install' else [])
    def work():
        try:
            if repo is not None:
                upstream(server.comfy,'/v2/customnode/install/git_url',repo,plain=True,timeout=1800)
            else:
                pack = dict(row, id=row.get('id') or key, ui_id=job, channel=snapshot.get('channel','default'),
                            mode='cache',selected_version='unknown' if row.get('version')=='unknown' else 'latest')
                resp = upstream(server.comfy,'/v2/manager/queue/batch',{'batch_id':job,action:[pack]})
                if resp.get('failed'):
                    raise ValueError('Manager declined the install. Check its permissions and engine log.')
                for _ in range(900):
                    time.sleep(2)
                    histories=upstream(server.comfy,'/v2/manager/queue/history_list')
                    if job in histories['ids']:
                        history=upstream(server.comfy,'/v2/manager/queue/history?id='+job)
                        outcome=history['nodepack_result'].get(job)
                        if outcome not in ('success','skip'):
                            raise ValueError(str(outcome or 'Manager did not report a successful install.'))
                        break
                else:
                    raise ValueError('Manager has not confirmed completion. Check the engine log before retrying.')
            status = install_status(job)
            status.update(state='done', message=action.capitalize()+' complete')
        except Exception as exc:
            status={'state':'error','message':str(exc)}
        with LOCK:
            JOBS[job]=status
            ACTIVE.pop(identity,None)
    threading.Thread(target=work,daemon=True).start()
    return {'job':job}
