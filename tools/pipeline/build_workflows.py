"""Write the pipeline's ComfyUI workflows to tools/pipeline/workflows/ (then `comfy.py push`).

Scripts find a workflow's inputs by node title, so keep the titles when editing in ComfyUI:

unit-views         Qwen Image 2.1 Turbo, one reference image -> one image.
                   titles: 'reference' (LoadImage), 'prompt' (TextEncodeQwenImage21),
                   'seed' (RandomNoise), 'size' (EmptyLatentImage), 'save' (SaveImage)
model-from-views   Pixal3D multi-view (ComfyUI's "Pixal3D: Multi Views to 3D" template) with four
                   separate views instead of a cropped turnaround sheet, at the template's
                   quality settings (they fit 12 GB for one character). titles: 'front', 'left', 'back',
                   'right' (LoadImage), 'save model' (Save3DAdvanced; SaveGLB in API runs).
                   'left' is the character facing the right edge of the picture, 'right' facing
                   the left edge, as in the template's sample sheet.
"""
import copy, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comfy

OUT = comfy.WORKFLOWS
SIGMAS = '1.0, 0.978453, 0.95418, 0.926626, 0.89508, 0.845148, 0.704534, 0.414568, 0'   # Qwen 2.1 Turbo, as in its template

def unit_views():
    api = {
        'unet': {'class_type': 'UNETLoader', 'inputs': {'unet_name': 'qwen_image_2.1_turbo_int8_convrot.safetensors', 'weight_dtype': 'default'}},
        'cache': {'class_type': 'QwenImage21Cache', 'inputs': {'model': ['unet', 0], 'device': 'auto', 'dtype': 'default'}},
        'clip': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': 'qwen3vl_8b_int8_convrot.safetensors', 'type': 'qwen_image', 'device': 'default'}},
        'vae': {'class_type': 'VAELoader', 'inputs': {'vae_name': 'qwen_image_2.1_vae_bf16.safetensors'}},
        'ref': {'class_type': 'LoadImage', 'inputs': {'image': 'example.png'}},
        'encode': {'class_type': 'TextEncodeQwenImage21', 'inputs': {
            'clip': ['clip', 0], 'vae': ['vae', 0], 'prompt': '', 'negative_prompt': '', 'resolution': 1024,
            'images.image_1': ['ref', 0]}},
        'latent': {'class_type': 'EmptyLatentImage', 'inputs': {'width': 1024, 'height': 1024, 'batch_size': 1}},
        'noise': {'class_type': 'RandomNoise', 'inputs': {'noise_seed': 1}},
        'sampler': {'class_type': 'KSamplerSelect', 'inputs': {'sampler_name': 'euler'}},
        'sigmas': {'class_type': 'ManualSigmas', 'inputs': {'sigmas': SIGMAS}},
        'guider': {'class_type': 'CFGGuider', 'inputs': {'cfg': 1.0, 'model': ['cache', 0], 'positive': ['encode', 0], 'negative': ['encode', 1]}},
        'sample': {'class_type': 'SamplerCustomAdvanced', 'inputs': {
            'noise': ['noise', 0], 'guider': ['guider', 0], 'sampler': ['sampler', 0], 'sigmas': ['sigmas', 0], 'latent_image': ['latent', 0]}},
        'decode': {'class_type': 'VAEDecode', 'inputs': {'samples': ['sample', 0], 'vae': ['vae', 0]}},
        'save': {'class_type': 'SaveImage', 'inputs': {'images': ['decode', 0], 'filename_prefix': 'homm3/view'}},
    }
    return comfy.api_to_ui(api, titles={'ref': 'reference', 'encode': 'prompt', 'noise': 'seed', 'latent': 'size', 'save': 'save'})

def model_from_views():
    ui = comfy.get('/templates/3d_pixal3d_multi_views.json').json()
    ui = copy.deepcopy(ui)
    nodes = {n['id']: n for n in ui['nodes']}
    sheet = next(n for n in ui['nodes'] if n['type'] == 'LoadImage')
    crops = [n for n in ui['nodes'] if n['type'] == 'ImageCropV2']
    mv = next(n for n in ui['nodes'] if n['type'] == 'Pixal3DMultiViewConditioning')
    links = {l[0]: l for l in ui['links']}
    # which crop feeds which view: follow each view input of the conditioning node upstream
    def upstream_crop(link_id):
        seen = set()
        stack = [links[link_id][1]]
        while stack:
            nid = stack.pop()
            if nid in seen:
                continue
            seen.add(nid)
            if nodes[nid]['type'] == 'ImageCropV2':
                return nodes[nid]
            stack += [links[i['link']][1] for i in nodes[nid].get('inputs', []) if i.get('link') is not None]
    view_of = {upstream_crop(i['link'])['id']: i['name'] for i in mv['inputs'] if i['name'] in ('front', 'left', 'back', 'right') and i.get('link') is not None}
    assert sorted(view_of.values()) == ['back', 'front', 'left', 'right'], view_of
    drop_links = {i['link'] for c in crops for i in c['inputs'] if i.get('link') is not None}
    ui['links'] = [l for l in ui['links'] if l[0] not in drop_links]
    for c in crops:   # each crop of the sheet becomes a LoadImage of one view (same id, same output slot 0)
        c['type'] = 'LoadImage'
        c['title'] = view_of[c['id']]
        c['inputs'] = []
        c['widgets_values'] = ['example.png', 'image']
        c['properties'] = {'Node name for S&R': 'LoadImage'}
        c['outputs'] = [{**c['outputs'][0], 'name': 'IMAGE', 'type': 'IMAGE', 'slot_index': 0},
                        {'name': 'MASK', 'type': 'MASK', 'slot_index': 1, 'links': []}]
    ui['nodes'] = [n for n in ui['nodes'] if n['id'] != sheet['id'] and n['type'] != 'MarkdownNote']
    # Pixal3D's baked metallic map is ~1.0 everywhere (cloth, skin and hair as metal), which renders
    # nearly black under the battle lighting; leave it out so the model is non-metallic like Tripo's.
    apply = next(n for n in ui['nodes'] if n['type'] == 'ApplyTextureToMesh')
    metal = next(i for i in apply['inputs'] if i['name'] == 'metallic')
    if metal.get('link') is not None:
        lid = metal['link']
        ui['links'] = [l for l in ui['links'] if l[0] != lid]
        for n in ui['nodes']:
            for o in n.get('outputs', []):
                if o.get('links') and lid in o['links']:
                    o['links'].remove(lid)
        metal['link'] = None
    for n in ui['nodes']:
        # The template's quality (upsample 1536, texture 4096) fits the RTX 5070's 12 GB for one
        # character (68 s). The lower 12 GB settings (1024 / 2048) smeared Fan Master's face.
        if n['type'] == 'Save3DAdvanced':
            n['title'] = 'save model'
            n['widgets_values'][0] = 'homm3/model'
    ui['nodes'].append({'id': max(n['id'] for n in ui['nodes']) + 1, 'type': 'MarkdownNote', 'pos': [-900, -300],
                        'size': [500, 220], 'flags': {}, 'order': 0, 'mode': 0, 'inputs': [], 'outputs': [],
                        'properties': {}, 'widgets_values': [
        '## homm3/model-from-views\n\nPixal3D multi-view: four square views of one character, same scale, '
        'on black or with alpha. **left** = the character facing the right edge of the picture, **right** = '
        'facing the left edge. Template quality (upsample 1536, texture 4096) fits 12 GB for one character.\n\nRun by '
        '`tools/pipeline/` in the homm3-mod-creator repo, which finds inputs by node title: keep the titles '
        '`front`, `left`, `back`, `right`, `save model`.']})
    return ui

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    for name, build in (('unit-views', unit_views), ('model-from-views', model_from_views)):
        ui = build()
        comfy.ui_to_api(ui)   # must convert back cleanly
        (OUT / f'{name}.json').write_text(json.dumps(ui, indent=1) + '\n')
        print('wrote', OUT / f'{name}.json')
