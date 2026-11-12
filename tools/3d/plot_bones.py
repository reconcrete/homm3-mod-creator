"""Draw a rig's bones over its mesh (top and front views) to tell legs, pincers and tails apart.
Run: python3 tools/3d/plot_bones.py BONES.json OUT.png   (BONES.json from bone_map.py)"""
import json, sys, colorsys
from PIL import Image, ImageDraw
d = json.load(open(sys.argv[1])); S = 1400; im = Image.new('RGB', (2 * S // 2 * 2, S), 'white'); dr = ImageDraw.Draw(im)
xs = [v[0] for v in d['v']]; ys = [v[1] for v in d['v']]; zs = [v[2] for v in d['v']]
lo, hi = min(xs + ys + zs), max(xs + ys + zs); f = lambda c: int((c - lo) / (hi - lo) * (S - 80) + 40)
for v in d['v']:
    dr.point((f(v[0]), S - f(v[1])), fill=(200, 200, 200)); dr.point((S + f(v[0]), S - f(v[2])), fill=(200, 200, 200))
for i, (n, (h, t)) in enumerate(d['b'].items()):
    col = tuple(int(255 * c) for c in colorsys.hsv_to_rgb((i * 0.137) % 1, 0.9, 0.75)); n = n.replace('tripo::', '')
    dr.line((f(h[0]), S - f(h[1]), f(t[0]), S - f(t[1])), fill=col, width=4); dr.text((f(t[0]) + 3, S - f(t[1])), n, fill=col)
    dr.line((S + f(h[0]), S - f(h[2]), S + f(t[0]), S - f(t[2])), fill=col, width=4); dr.text((S + f(t[0]) + 3, S - f(t[2])), n, fill=col)
dr.text((10, 10), 'TOP (x right, y up)', fill='black'); dr.text((S + 10, 10), 'FRONT (x right, z up)', fill='black')
im.save(sys.argv[2])
