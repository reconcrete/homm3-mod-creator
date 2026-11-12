#!/usr/bin/env python3
"""Read original Heroes 3 graphics from the game's .lod archives.

Used to build style reference sheets for image generation.

  h3data.py list  LOD [PREFIX]           list entries
  h3data.py def   LOD NAME OUTDIR        extract every frame of a .def sprite as PNG
"""
import os
import struct
import sys
import zlib

from PIL import Image


def lod_entries(path):
    data = open(path, "rb").read()
    count = struct.unpack("<I", data[8:12])[0]
    entries = {}
    for i in range(count):
        o = 92 + i * 32
        name, off, size, _, csize = struct.unpack("<16sIIII", data[o:o + 32])
        name = name.split(b"\0")[0].decode("latin1")
        raw = data[off:off + (csize or size)]
        entries[name.upper()] = (raw, csize)
    return entries


def lod_read(entries, name):
    raw, csize = entries[name.upper()]
    return zlib.decompress(raw) if csize else raw


def _decode_frame(buf, off):
    size, fmt, full_w, full_h, w, h, left, top = struct.unpack("<8I", buf[off:off + 32])
    base = off + 32
    px = bytearray(w * h)
    if fmt == 0:
        px[:] = buf[base:base + w * h]
    elif fmt == 1:
        line_offsets = struct.unpack(f"<{h}I", buf[base:base + 4 * h])
        for y in range(h):
            p, x = base + line_offsets[y], 0
            while x < w:
                code, length = buf[p], buf[p + 1] + 1
                p += 2
                if code == 0xFF:
                    px[y * w + x:y * w + x + length] = buf[p:p + length]
                    p += length
                else:
                    px[y * w + x:y * w + x + length] = bytes([code]) * length
                x += length
    elif fmt in (2, 3):
        if fmt == 2:
            p = base + struct.unpack("<H", buf[base:base + 2])[0]
            starts = None
        else:
            blocks = w // 32
            starts = [struct.unpack(f"<{blocks}H", buf[base + y * blocks * 2:base + (y + 1) * blocks * 2])[0] for y in range(h)]
        for y in range(h):
            if starts is not None:
                p = base + starts[y]
            x = 0
            while x < w:
                seg = buf[p]
                p += 1
                code, length = seg >> 5, (seg & 31) + 1
                if code == 7:
                    px[y * w + x:y * w + x + length] = buf[p:p + length]
                    p += length
                else:
                    px[y * w + x:y * w + x + length] = bytes([code]) * length
                x += length
    else:
        raise ValueError(f"unknown frame format {fmt}")
    return full_w, full_h, w, h, left, top, bytes(px)


def def_frames(buf):
    """Yield (group, index, RGBA image) for every frame of a .def file."""
    _, width, height, block_count = struct.unpack("<4I", buf[:16])
    palette = buf[16:16 + 768]
    p = 16 + 768
    for _ in range(block_count):
        group, count, _, _ = struct.unpack("<4I", buf[p:p + 16])
        p += 16 + 13 * count
        offsets = struct.unpack(f"<{count}I", buf[p:p + 4 * count])
        p += 4 * count
        for i, off in enumerate(offsets):
            full_w, full_h, w, h, left, top, px = _decode_frame(buf, off)
            rgba = bytearray()
            for idx in px:
                if idx in (0, 1, 4, 5, 6, 7):  # transparency and shadow indices
                    rgba += b"\0\0\0\0"
                else:
                    rgba += palette[idx * 3:idx * 3 + 3] + b"\xff"
            frame = Image.new("RGBA", (full_w, full_h), (0, 0, 0, 0))
            if w and h:
                frame.paste(Image.frombytes("RGBA", (w, h), bytes(rgba)), (left, top))
            yield group, i, frame


def main():
    cmd, lod = sys.argv[1], sys.argv[2]
    entries = lod_entries(lod)
    if cmd == "list":
        prefix = sys.argv[3].upper() if len(sys.argv) > 3 else ""
        for name in sorted(entries):
            if name.startswith(prefix):
                print(name)
    elif cmd == "def":
        name, outdir = sys.argv[3], sys.argv[4]
        os.makedirs(outdir, exist_ok=True)
        n = 0
        for group, i, frame in def_frames(lod_read(entries, name)):
            frame.save(os.path.join(outdir, f"{group}_{i}.png"))
            n += 1
        print(f"{n} frames -> {outdir}")


if __name__ == "__main__":
    main()
