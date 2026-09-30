"""Minimal reader for Heroes 3 .lod archives.
python3 tools/lod.py ARCHIVE list [pattern]      list entries
python3 tools/lod.py ARCHIVE extract NAME OUTDIR  extract one entry (case-insensitive)"""
import struct, sys, zlib, os, fnmatch

def entries(path):
    f = open(path, 'rb')
    magic, _, count = struct.unpack('<4sII', f.read(12))
    assert magic == b'LOD\0', 'not a LOD archive'
    f.seek(92)
    for _ in range(count):
        name, off, size, _typ, csize = struct.unpack('<16sIIII', f.read(32))
        yield name.split(b'\0')[0].decode('latin1'), off, size, csize

def read(path, wanted):
    for name, off, size, csize in entries(path):
        if name.lower() == wanted.lower():
            f = open(path, 'rb'); f.seek(off)
            data = f.read(csize or size)
            return name, (zlib.decompress(data) if csize else data)
    raise KeyError(wanted)

if __name__ == '__main__':
    arc, cmd = sys.argv[1], sys.argv[2]
    if cmd == 'list':
        pat = sys.argv[3].lower() if len(sys.argv) > 3 else '*'
        for name, off, size, csize in entries(arc):
            if fnmatch.fnmatch(name.lower(), pat): print(name, size)
    elif cmd == 'extract':
        name, data = read(arc, sys.argv[3])
        os.makedirs(sys.argv[4], exist_ok=True)
        open(os.path.join(sys.argv[4], name), 'wb').write(data)
        print(name, len(data))
