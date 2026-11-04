from pathlib import PureWindowsPath
from urllib.parse import quote
from urllib.error import HTTPError
import json

def file_route(name):
    if not isinstance(name,str) or not name.lower().endswith('.json'):
        raise ValueError('Choose a workflow JSON file.')
    if any(c in name for c in '<>:"\\|?*') or any(ord(c)<32 for c in name):
        raise ValueError('Invalid workflow name.')
    if any(p in ('','.','..') or p.endswith((' ','.')) or PureWindowsPath(p).is_reserved() for p in name.split('/')):
        raise ValueError('Invalid workflow path.')
    return '/userdata/' + quote('workflows/'+name,safe='')

def list_files(base,request):
    try:
        data,_=request(base,'/userdata?dir=workflows&recurse=true')
    except HTTPError as exc:
        if exc.code==404:return []
        raise
    return sorted(p for p in json.loads(data) if isinstance(p,str) and p.lower().endswith('.json'))
