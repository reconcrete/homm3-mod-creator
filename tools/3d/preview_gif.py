#!/usr/bin/env python3
"""One preview GIF per creature: every rendered clip side by side, playing together.

Looping clips (idle, walk) cycle; one-shot clips play once and hold their last frame, then the
whole sheet restarts.

Usage: tools/3d/preview_gif.py FRAMES OUT.gif     (FRAMES = WORK/frames with one folder per clip)
"""
import pathlib
import sys

from PIL import Image

ORDER = ["idle", "walk", "attack", "hit", "defend", "death", "shoot"]
LOOPING = {"idle", "walk"}
CELL = (300, 267)
COLS = 4

frames_dir, out = pathlib.Path(sys.argv[1]), sys.argv[2]
clips = [(c, [Image.open(p) for p in sorted((frames_dir / c).glob("*.png"))])
         for c in ORDER if (frames_dir / c).is_dir()]
length = max(len(f) for _, f in clips) + 4
rows = (len(clips) + COLS - 1) // COLS
sheet = []
for i in range(length):
    canvas = Image.new("RGB", (CELL[0] * min(COLS, len(clips)), CELL[1] * rows), (84, 104, 72))
    for k, (clip, frames) in enumerate(clips):
        im = frames[i % len(frames)] if clip in LOOPING else frames[min(i, len(frames) - 1)]
        im = im.crop((0, 50, 900, 850)).resize(CELL)
        canvas.paste(im, ((k % COLS) * CELL[0], (k // COLS) * CELL[1]), im)
    sheet.append(canvas)
sheet[0].save(out, save_all=True, append_images=sheet[1:], duration=110, loop=0)
print(out, ", ".join(c for c, _ in clips))
