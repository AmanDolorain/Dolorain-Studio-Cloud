"""Install Studio colors using ComfyUI's native user settings before startup."""
import json
from pathlib import Path
from tempfile import NamedTemporaryFile


def palette(light):
    mode = 'light' if light else 'dark'
    bg, card, header, text, border, accent = (
        ('#f5f6f7','#ffffff','#e9ecef','#24272b','#c7cdd3','#536d82') if light else
        ('#111315','#1b1e21','#262a2e','#e9eaec','#43484e','#a7b9c7'))
    return {'id':'dolorain-' + mode, 'name':'Dolorain Studio ' + mode.title(), 'light_theme':light,
            'colors':{'node_slot':{}, 'comfy_base':{'fg-color':text,'bg-color':bg,'comfy-menu-bg':card},
                      'litegraph_base':{'CLEAR_BACKGROUND_COLOR':bg,'NODE_TITLE_COLOR':text,
                                        'NODE_DEFAULT_COLOR':header,'NODE_DEFAULT_BGCOLOR':card,
                                        'NODE_TEXT_COLOR':text,'WIDGET_BGCOLOR':header,
                                        'WIDGET_TEXT_COLOR':text,'WIDGET_OUTLINE_COLOR':border},
                      'theme':{'background':bg,'foreground':text,'card':card,'node':card,
                               'node-foreground':text,'node-header':header,'node-border':border,
                               'border':border,'ring':accent}}}


def install(user_dir):
    path = Path(user_dir) / 'default' / 'comfy.settings.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    settings = json.loads(path.read_text()) if path.exists() else {}
    before = dict(settings)
    palettes = dict(settings.get('Comfy.CustomColorPalettes', {}))
    for light in (False, True):
        entry = palette(light)
        palettes.setdefault(entry['id'], entry)
    settings['Comfy.CustomColorPalettes'] = palettes
    key = 'Comfy.ColorPalette'
    if settings.get(key, 'light') in ('light','dark'):
        settings[key] = 'dolorain-' + settings.get(key, 'light')
    if settings != before:
        with NamedTemporaryFile(mode='w',dir=path.parent,delete=False) as output:
            json.dump(settings, output, ensure_ascii=False)
        Path(output.name).replace(path)
