"""Decode the Heroes 3 'PCX' images stored in .lod archives into Pillow images."""
import struct
from PIL import Image

def decode(data):
    size, w, h = struct.unpack('<III', data[:12])
    px = data[12:12 + size]
    if size == w * h:  # 8-bit paletted, palette after pixels
        pal = data[12 + size:12 + size + 768]
        img = Image.frombytes('P', (w, h), px); img.putpalette(pal)
        return img.convert('RGB')
    img = Image.frombytes('RGB', (w, h), px, 'raw', 'BGR')
    return img
