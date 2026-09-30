"""Decode Heroes 3 .def sprite archives (from a .lod) into Pillow RGBA frames.
python3 tools/h3def.py LOD DEFNAME OUT.png [cols]   contact sheet of all frames, labeled group:frame"""
import struct, sys, os
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from lod import read

def decode(data):
    typ, W, H, nblocks = struct.unpack_from('<IIII', data, 0)
    pal = data[16:16 + 768]
    pos = 16 + 768
    groups = {}
    for _ in range(nblocks):
        gid, n, _u1, _u2 = struct.unpack_from('<IIII', data, pos); pos += 16
        names = [data[pos + 13 * i: pos + 13 * i + 13].split(b'\0')[0].decode('latin1') for i in range(n)]; pos += 13 * n
        offs = struct.unpack_from('<%dI' % n, data, pos); pos += 4 * n
        groups[gid] = [(names[i], frame(data, offs[i], pal)) for i in range(n)]
    return groups

def frame(data, off, pal):
    size, fmt, fw, fh, w, h, lm, tm = struct.unpack_from('<IIIIIIii', data, off)
    base = off + 32
    idx = bytearray(fw * fh)  # palette indices on the full canvas, 0 = transparent
    if fmt == 0:
        for y in range(h):
            idx[(tm + y) * fw + lm:(tm + y) * fw + lm + w] = data[base + y * w: base + y * w + w]
    elif fmt == 1:
        lines = struct.unpack_from('<%dI' % h, data, base)
        for y in range(h):
            p = base + lines[y]; x = 0
            while x < w:
                code, ln = data[p], data[p + 1] + 1; p += 2
                for i in range(ln):
                    idx[(tm + y) * fw + lm + x + i] = code if code == 0xFF and False else (data[p + i] if code == 0xFF else code)
                if code == 0xFF: p += ln
                x += ln
    else:  # 2 and 3: segment-compressed
        for y in range(h):
            if fmt == 2:
                p = base + struct.unpack_from('<H', data, base + 2 * y)[0]
            else:
                p = base + struct.unpack_from('<H', data, base + 2 * (y * (w // 32)))[0]
            x = 0
            while x < w:
                b = data[p]; p += 1
                code, ln = b >> 5, (b & 31) + 1
                for i in range(ln):
                    idx[(tm + y) * fw + lm + x + i] = data[p + i] if code == 7 else code
                if code == 7: p += ln
                x += ln
    img = Image.frombytes('P', (fw, fh), bytes(idx)); img.putpalette(pal)
    rgba = img.convert('RGBA'); px = rgba.load(); src = img.load()
    for y in range(fh):
        for x in range(fw):
            if src[x, y] in (0, 1, 4): px[x, y] = (0, 0, 0, 0)          # transparent + shadow
            elif src[x, y] in (5, 6, 7): px[x, y] = (0, 0, 0, 0)        # selection / flag colors
    return rgba

if __name__ == '__main__':
    lod, name, out = sys.argv[1:4]
    cols = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    groups = decode(read(lod, name)[1])
    cells = [(g, i, im) for g, fr in sorted(groups.items()) for i, (_, im) in enumerate(fr)]
    W = max(im.width for *_, im in cells); H = max(im.height for *_, im in cells) + 12
    sheet = Image.new('RGBA', (cols * W, ((len(cells) + cols - 1) // cols) * H), (60, 60, 60, 255))
    d = ImageDraw.Draw(sheet)
    for k, (g, i, im) in enumerate(cells):
        x, y = (k % cols) * W, (k // cols) * H
        sheet.alpha_composite(im, (x, y)); d.text((x + 2, y + H - 11), '%d:%d' % (g, i), fill=(255, 255, 0))
    sheet.save(out); print(len(cells), 'frames', W, 'x', H - 12)
