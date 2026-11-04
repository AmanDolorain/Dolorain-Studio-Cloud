"""Start ComfyUI and observe its native registry archive writes."""
import hashlib
import json
import os
import runpy
import sys
from pathlib import Path

def metric_path(directory, node_id):
    return Path(directory) / hashlib.sha256(node_id.lower().encode()).hexdigest()

def observe(directory):
    def hook(event, args):
        if event not in ('open', 'os.remove') or not isinstance(args[0], str):
            return
        path = args[0]
        if 'CNR_temp_' not in path or not path.endswith('.zip'):
            return
        if event == 'open' and args[1] != 'w':
            return
        try:
            frame = sys._getframe(1)
            total = None
            while frame:
                if frame.f_code.co_name == '_urlretrieve':
                    total = getattr(frame.f_locals.get('response'), 'length', None)
                if (frame.f_code.co_name == 'cnr_install' and
                        frame.f_globals.get('__name__', '').endswith('manager_core') and
                        frame.f_locals.get('download_path') == path):
                    record = metric_path(directory, frame.f_locals['node_id'])
                    if event == 'open':
                        data = dict(archive=path, total=total)
                    elif record.exists() and os.path.isfile(path):
                        data = json.loads(record.read_text())
                        if data['archive'] != path:
                            return
                        data['received'] = os.path.getsize(path)
                        data['finished'] = True
                    else:
                        return
                    tmp = record.with_suffix('.tmp')
                    tmp.write_text(json.dumps(data))
                    tmp.replace(record)
                    return
                frame = frame.f_back
        except (OSError, ValueError, KeyError, TypeError):
            pass
    sys.addaudithook(hook)

if __name__ == '__main__':
    observe(os.environ['DOLORAIN_PROGRESS_DIR'])
    sys.path.insert(0, os.getcwd())
    sys.argv[0] = 'main.py'
    runpy.run_path('main.py', run_name='__main__')
