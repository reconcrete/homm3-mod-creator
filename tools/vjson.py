"""Lenient loader for VCMI-style JSON (// and /* */ comments, trailing commas).
Usage as a module: from vjson import load; or CLI: python3 tools/vjson.py FILE [key]"""
import json, re, sys

def strip(text):
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == '\\': out.append(text[i+1]); i += 1
            elif c == '"': in_str = False
        elif c == '"': in_str = True; out.append(c)
        elif text.startswith('//', i):
            while i < n and text[i] != '\n': i += 1
            continue
        elif text.startswith('/*', i):
            i = text.find('*/', i) + 2; continue
        else: out.append(c)
        i += 1
    return re.sub(r',(\s*[}\]])', r'\1', ''.join(out))

def load(path):
    return json.loads(strip(open(path, encoding='utf-8-sig').read()))

if __name__ == '__main__':
    d = load(sys.argv[1])
    for k in sys.argv[2:]: d = d[k]
    print(json.dumps(d, indent=1, ensure_ascii=False))
