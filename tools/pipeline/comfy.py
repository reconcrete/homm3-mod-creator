"""ComfyUI client for the art pipeline: workflows live in ComfyUI, scripts run them.

Workflows are saved in ComfyUI's own workflow list under the folder `homm3/` (UI format, so
they open and can be edited at the ComfyUI page) and copied to tools/pipeline/workflows/.
A run fetches the live version from ComfyUI, converts it to the API format, fills inputs by
node title, queues it and downloads the outputs.

Server: COMFY_URL in the environment, else "comfy_url" in tools/pipeline/local.json
(git-ignored), else http://127.0.0.1:8188.

    python3 tools/pipeline/comfy.py push            # repo copies -> ComfyUI
    python3 tools/pipeline/comfy.py pull            # ComfyUI (maybe edited in the UI) -> repo
    python3 tools/pipeline/comfy.py list
"""
import hashlib, json, os, pathlib, sys, time, urllib.parse, uuid

import requests

HERE = pathlib.Path(__file__).resolve().parent
WORKFLOWS = HERE / 'workflows'
FOLDER = 'homm3'

def config():
    local = HERE / 'local.json'
    data = json.loads(local.read_text()) if local.exists() else {}
    return data

URL = (os.environ.get('COMFY_URL') or config().get('comfy_url') or 'http://127.0.0.1:8188').rstrip('/')

# ---------------------------------------------------------------- HTTP

def get(path, **params):
    r = requests.get(URL + path, params=params, timeout=60)
    r.raise_for_status()
    return r

_object_info = None
def object_info():
    global _object_info
    if _object_info is None:
        _object_info = get('/object_info').json()
    return _object_info

def upload(path, subfolder=FOLDER):
    """Upload an image to ComfyUI's input folder; returns the name LoadImage takes. The name carries
    a hash of the content: jobs running side by side all upload 'front.png' and must not overwrite
    each other's inputs."""
    path = pathlib.Path(path)
    data = path.read_bytes()
    name = f'{hashlib.sha1(data).hexdigest()[:12]}-{path.name}'
    r = requests.post(URL + '/upload/image', files={'image': (name, data, 'image/png')},
                      data={'subfolder': subfolder, 'overwrite': 'true'}, timeout=120)
    r.raise_for_status()
    d = r.json()
    return f"{d['subfolder']}/{d['name']}" if d.get('subfolder') else d['name']

def userdata_path(name):
    return '/userdata/' + urllib.parse.quote(f'workflows/{FOLDER}/{name}.json', safe='')

def fetch_workflow(name):
    return get(userdata_path(name)).json()

def save_workflow(name, ui):
    r = requests.post(URL + userdata_path(name), params={'overwrite': 'true'},
                      data=json.dumps(ui, indent=1), headers={'Content-Type': 'application/json'}, timeout=60)
    r.raise_for_status()

def list_workflows():
    files = get('/userdata', dir='workflows', recurse='true', split='false').json()
    return sorted(f[len(FOLDER) + 1:-5] for f in files if f.startswith(FOLDER + '/') and f.endswith('.json'))

def queue(api_graph):
    r = requests.post(URL + '/prompt', json={'prompt': api_graph, 'client_id': str(uuid.uuid4())}, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f'ComfyUI refused the graph: {r.text[:2000]}')
    return r.json()['prompt_id']

def wait(prompt_id, timeout=3600, poll=3, quiet=False):
    """Wait for a queued prompt; returns its history entry, raises on an execution error."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = get(f'/history/{prompt_id}').json().get(prompt_id)
        if h:
            status = h.get('status', {})
            if status.get('status_str') == 'error':
                msgs = [m for m in status.get('messages', []) if m[0] == 'execution_error']
                detail = msgs[0][1] if msgs else status
                if isinstance(detail, dict):
                    detail = f"{detail.get('node_type')} (node {detail.get('node_id')}): {detail.get('exception_message', '').strip()}"
                raise RuntimeError(f'ComfyUI run failed: {detail}')
            if status.get('completed'):
                if not quiet:
                    print(f'  done in {time.time() - t0:.0f} s', flush=True)
                return h
        time.sleep(poll)
    raise TimeoutError(f'prompt {prompt_id} still running after {timeout} s')

def download(history, out_dir):
    """Save every file a run produced (images, 3D files) into out_dir; returns {node title or id: [paths]}."""
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = {}
    for node_id, outputs in history.get('outputs', {}).items():
        for kind, items in outputs.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict) or 'filename' not in item or item.get('type') == 'temp':
                    continue
                data = get('/view', filename=item['filename'], subfolder=item.get('subfolder', ''),
                           type=item.get('type', 'output')).content
                dest = out_dir / item['filename']
                dest.write_bytes(data)
                saved.setdefault(node_id, []).append(dest)
    return saved

# ---------------------------------------------------------------- UI <-> API format

UI_ONLY = {'Note', 'MarkdownNote', 'Preview3D', 'Preview3DAdvanced', 'PreviewAny'}
# consumers get the node's first input instead (the previews pass their image on in recent ComfyUI)
PASS_THROUGH = {'Reroute', 'SaveImageAdvanced', 'PreviewImage', 'MaskPreview'}
WIDGET_TYPES = {'INT', 'FLOAT', 'STRING', 'BOOLEAN', 'COMBO', 'COLOR', 'BOUNDING_BOX', 'COMFY_DYNAMICCOMBO_V3'}

def spec_inputs(class_type):
    info = object_info()[class_type]['input']
    return list((info.get('required') or {}).items()) + list((info.get('optional') or {}).items())

def is_widget(spec):
    kind, opts = spec[0], (spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {})
    if opts.get('forceInput'):
        return False
    return isinstance(kind, list) or kind in WIDGET_TYPES or bool(opts.get('socketless'))

def has_control(spec):
    opts = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
    return spec[0] == 'INT' and bool(opts.get('control_after_generate'))

def dynamic_inputs(spec, key):
    """Widget inputs of the chosen option of a COMFY_DYNAMICCOMBO_V3 input (named '<input>.<sub>' in API)."""
    option = next((o for o in spec[1]['options'] if o['key'] == key), None)
    if option is None:
        return []
    ins = option.get('inputs') or {}
    return [(n, s) for n, s in list((ins.get('required') or {}).items()) + list((ins.get('optional') or {}).items()) if is_widget(s)]

def ui_to_api(ui):
    """A flat UI-format workflow (no subgraphs) -> API format, with node titles kept in _meta."""
    nodes = {n['id']: n for n in ui['nodes']}
    links = {l[0]: l for l in ui['links']}

    def source(link_id):   # follow pass-through and bypassed nodes back to a real output
        _, src, slot = links[link_id][:3]
        n = nodes[src]
        while n['type'] in PASS_THROUGH or n.get('mode') == 4:
            nxt = next((i['link'] for i in n.get('inputs', []) if i.get('link') is not None), None)
            if nxt is None:
                return None
            _, src, slot = links[nxt][:3]
            n = nodes[src]
        return [str(src), slot]

    api = {}
    for n in ui['nodes']:
        t = n['type']
        if t in UI_ONLY or t in PASS_THROUGH or n.get('mode') in (2, 4):
            continue
        if t == 'Save3DAdvanced':
            link = next(i['link'] for i in n['inputs'] if i['name'] == 'model_3d')
            api[str(n['id'])] = {'class_type': 'SaveGLB', 'inputs': {
                'mesh': source(link), 'filename_prefix': n['widgets_values'][0] or '3d/ComfyUI'},
                '_meta': {'title': n.get('title') or t}}
            continue
        if t not in object_info():
            raise ValueError(f'node type {t} (node {n["id"]}) is not installed in ComfyUI')
        inputs = {}
        values = n.get('widgets_values', [])
        if isinstance(values, dict):
            inputs.update(values)
        else:
            vi = 0
            for name, spec in spec_inputs(t):
                if spec[0] == 'COMFY_AUTOGROW_V3' or not is_widget(spec):
                    continue
                if vi < len(values):
                    inputs[name] = values[vi]
                vi += 1 + has_control(spec)
                if spec[0] == 'COMFY_DYNAMICCOMBO_V3':   # the chosen option's own widgets follow its key
                    for sub, sub_spec in dynamic_inputs(spec, inputs.get(name)):
                        if vi < len(values):
                            inputs[f'{name}.{sub}'] = values[vi]
                        vi += 1 + has_control(sub_spec)
        for i in n.get('inputs', []):
            if i.get('link') is not None:
                src = source(i['link'])
                if src is not None:
                    inputs[i['name']] = src
        api[str(n['id'])] = {'class_type': t, 'inputs': inputs, '_meta': {'title': n.get('title') or t}}
    return api

def api_to_ui(api, titles=None, columns=None):
    """API format -> a flat UI-format workflow with a simple left-to-right layout, so a graph
    written in code opens in ComfyUI. titles: {node id: title}."""
    titles = titles or {}
    ids = list(api)
    num = {k: i + 1 for i, k in enumerate(ids)}
    depth = {}
    def d(k):
        if k not in depth:
            depth[k] = 0
            ups = [v[0] for v in api[k]['inputs'].values() if isinstance(v, list) and len(v) == 2 and v[0] in api]
            depth[k] = 1 + max((d(u) for u in ups), default=-1)
        return depth[k]
    for k in ids:
        d(k)
    links, nodes, rows = [], [], {}
    out_links = {}
    for k in ids:
        for name, v in api[k]['inputs'].items():
            if isinstance(v, list) and len(v) == 2 and v[0] in api:
                links.append([len(links) + 1, num[v[0]], v[1], num[k], name])
                out_links.setdefault((v[0], v[1]), []).append(len(links))
    link_of = {(l[3], l[4]): l[0] for l in links}
    for k in ids:
        node, t = api[k], api[k]['class_type']
        info = object_info()[t]
        col = depth[k]
        row = rows.get(col, 0)
        inputs, widgets = [], []
        specs = spec_inputs(t)
        for name, spec in specs:
            if spec[0] == 'COMFY_AUTOGROW_V3':
                for iname in sorted((n for n in node['inputs'] if n.startswith(name + '.')), key=lambda s: int(s.rsplit('_', 1)[-1])):
                    inputs.append({'name': iname, 'type': spec[1]['template']['input']['required']['image'][0],
                                   'link': link_of.get((num[k], iname))})
                continue
            v = node['inputs'].get(name)
            linked = isinstance(v, list) and len(v) == 2 and v[0] in api
            if is_widget(spec):
                default = spec[1].get('default') if len(spec) > 1 and isinstance(spec[1], dict) else None
                if default is None and isinstance(spec[0], list) and spec[0]:
                    default = spec[0][0]
                if spec[0] == 'COMFY_DYNAMICCOMBO_V3' and default is None:
                    default = spec[1]['options'][0]['key']
                widgets.append(default if linked or v is None else v)
                if has_control(spec):
                    widgets.append('fixed')
                if spec[0] == 'COMFY_DYNAMICCOMBO_V3':
                    for sub, sub_spec in dynamic_inputs(spec, widgets[-1]):
                        sv = node['inputs'].get(f'{name}.{sub}')
                        widgets.append(sub_spec[1].get('default') if sv is None else sv)
                        if has_control(sub_spec):
                            widgets.append('fixed')
                if linked:
                    inputs.append({'name': name, 'type': spec[0] if isinstance(spec[0], str) else 'COMBO',
                                   'widget': {'name': name}, 'link': link_of[(num[k], name)]})
            else:
                inputs.append({'name': name, 'type': spec[0], 'link': link_of.get((num[k], name))})
        outputs = [{'name': oname, 'type': otype, 'slot_index': s, 'links': out_links.get((k, s), [])}
                   for s, (otype, oname) in enumerate(zip(info['output'], info.get('output_name', info['output'])))]
        h = 60 + 26 * (len(inputs) + len(widgets))
        nodes.append({'id': num[k], 'type': t, 'pos': [40 + col * 380, 40 + row], 'size': [340, h],
                      'flags': {}, 'order': len(nodes), 'mode': 0, 'inputs': inputs, 'outputs': outputs,
                      'properties': {'Node name for S&R': t}, 'widgets_values': widgets,
                      **({'title': titles[k]} if k in titles else {})})
        rows[col] = row + h + 40
    for l in links:   # UI links carry the type of the output they come from
        src = next(n for n in nodes if n['id'] == l[1])
        l.append(src['outputs'][l[2]]['type'])
        l[4] = next(i for i, inp in enumerate(next(n for n in nodes if n['id'] == l[3])['inputs']) if inp['name'] == l[4])
    return {'last_node_id': len(nodes), 'last_link_id': len(links), 'nodes': nodes, 'links': links,
            'groups': [], 'config': {}, 'extra': {}, 'version': 0.4}

# ---------------------------------------------------------------- running a workflow

def node_by_title(api, title):
    hits = [k for k, n in api.items() if n.get('_meta', {}).get('title') == title]
    if len(hits) != 1:
        raise KeyError(f'expected one node titled {title!r}, found {len(hits)}')
    return api[hits[0]]

def run(name, inputs, out_dir, timeout=3600):
    """Run workflow homm3/<name> from ComfyUI. inputs: {(node title, input name): value};
    a value that is a local file path for a LoadImage 'image' input is uploaded first."""
    api = ui_to_api(fetch_workflow(name))
    for (title, field), value in inputs.items():
        node = node_by_title(api, title)
        if node['class_type'] == 'LoadImage' and field == 'image' and os.path.exists(str(value)):
            value = upload(value)
        node['inputs'][field] = value
    print(f'{name}: queued', flush=True)
    history = wait(queue(api), timeout=timeout)
    return download(history, out_dir)

def push():
    for f in sorted(WORKFLOWS.glob('*.json')):
        save_workflow(f.stem, json.loads(f.read_text()))
        print('pushed', f'{FOLDER}/{f.stem}')

def pull():
    WORKFLOWS.mkdir(exist_ok=True)
    for name in list_workflows():
        (WORKFLOWS / f'{name}.json').write_text(json.dumps(fetch_workflow(name), indent=1) + '\n')
        print('pulled', f'{FOLDER}/{name}')

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'list'
    if cmd == 'push':
        push()
    elif cmd == 'pull':
        pull()
    elif cmd == 'list':
        print('\n'.join(list_workflows()) or '(no workflows in homm3/)')
    else:
        sys.exit(__doc__)
