#!/usr/bin/env python3
"""Build the art handoff gallery into art/gallery/ (published as a Claude artifact).

Every batch is one vault prompt note (starter prompt + one block per image). The page
shows each image, or its prompt when it is not generated yet, with downloads:
single images and whole batches as PNG, prompts as Markdown, reference sheets.

Usage: tools/gallery/build_gallery.py
"""
import json
import pathlib
import re
import shutil

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
ART = pathlib.Path("/Users/antonmorozov/O/Projects/HoMM3-Naruto/Knowledge/Art")
INBOX = ROOT / "art" / "inbox"
REF = ROOT / "art" / "reference"
OUT = ROOT / "art" / "gallery"

BATCHES = [
    # key, title, note, reference sheet, label prefix, kind
    ("heroes", "Hero portraits", "Naruto-Heroes-Hero-Portrait-Prompts.md", "h3-hero-portraits-reference.png", "H", "portrait"),
    ("artifacts", "Artifact icons", "Naruto-Heroes-Artifact-Prompts.md", "h3-artifact-icons-reference.png", "A", "icon"),
    ("creatures", "Creatures", "Naruto-Heroes-Creature-Prompts.md", "h3-creatures-reference.png", "C", "creature"),
    ("screens", "Town screens", "Naruto-Heroes-Town-Screen-Prompts.md", "h3-town-screens-reference.png", "T", "wide"),
    ("buildings", "Town buildings", "Naruto-Heroes-Town-Building-Prompts.md", "h3-town-buildings-reference.png", "B", "object"),
    ("mapobjects", "Map objects", "Naruto-Heroes-Map-Object-Prompts.md", "h3-map-objects-reference.png", "M", "object"),
    ("extras", "Extras", "Naruto-Heroes-Extras-Prompts.md", "h3-extras-reference.png", "X", "icon"),
]
SIZES = {
    "portrait": "Generated 1024×1024 (or larger). In game: 58×64 portrait and a 48×32 face crop.",
    "icon": "Generated 1024×1024, transparent. In game: 44×44 (icons) or 20–60 px (projectiles).",
    "creature": "Generated 1024×1024, transparent, facing right, neutral standing pose. In game: about 60–160 px tall in battle.",
    "wide": "Generated 1536×1024. In game: cropped to 800×374.",
    "object": "Generated 1024×1024, transparent. In game: 64–300 px wide.",
}


def parse(note):
    text = (ART / note).read_text()
    starter = re.search(r"## Starter prompt\n.*?```text\n(.*?)\n```", text, re.S).group(1)
    items = []
    for block in re.split(r"\n## ", text)[1:]:
        header, _, body = block.partition("\n")
        if header.startswith("Starter"):
            continue
        for name, extra, fname, line in re.findall(r"\*\*(.+?)\*\*(?: \((.+?)\))? → `([^`]+)`\n\n```text\n(.*?)\n```", body, re.S):
            items.append({"name": name, "extra": extra or "", "file": fname, "group": header.strip(), "prompt": line})
    return starter, items


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "orig").mkdir(parents=True)
    (OUT / "ref").mkdir()
    rejected = ROOT / "art" / "rejected"
    batches = []
    for key, title, note, ref, prefix, kind in BATCHES:
        starter, items = parse(note)
        for i, it in enumerate(items, 1):
            it["label"] = f"{prefix}{i:02d}"
            src = INBOX / it["file"]
            stem = src.stem
            it["revised"] = any(rejected.glob(f"{stem}-v*.png"))
            it["ready"] = src.exists()
            if it["ready"]:
                im = Image.open(src)
                if kind == "portrait" or im.mode != "RGBA":
                    path = f"orig/{stem}.jpg"
                    im.convert("RGB").save(OUT / path, quality=90)
                else:
                    path = f"orig/{stem}.webp"
                    im.save(OUT / path, quality=90, method=6)
                it["img"] = path
        ref_path = f"ref/{pathlib.Path(ref).stem}.jpg"
        Image.open(REF / ref).convert("RGB").save(OUT / ref_path, quality=90)
        batches.append({"key": key, "title": title, "kind": kind, "size": SIZES[kind], "starter": starter,
                        "ref": ref_path, "refName": ref, "note": note, "items": items})
        print(f"{title}: {sum(i['ready'] for i in items)}/{len(items)} generated")
    template = (pathlib.Path(__file__).parent / "gallery_template.html").read_text()
    data = json.dumps({"batches": batches}, ensure_ascii=False).replace("</", "<\\/")
    (OUT / "index.html").write_text(template.replace("/*__DATA__*/null", data))
    files = [str(p.relative_to(OUT)) for p in sorted(OUT.rglob("*")) if p.is_file() and p.name != "index.html"]
    json.dump(files, open(OUT / "files.json", "w"))
    total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print(f"{len(files)} files, {total / 2**20:.1f} MB")


if __name__ == "__main__":
    main()
