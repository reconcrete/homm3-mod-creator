#!/usr/bin/env python3
"""Build a numbered review sheet of hero portraits.

Each card shows the full generated image and, next to it, the 58x64 in-game
crop blown up 3x, so Anton can judge how it reads at real size.

Usage: tools/review-sheet.py OUT.png file1.png file2.png ... [--cols 3]
"""
import argparse
import pathlib

from PIL import Image, ImageDraw, ImageFont

FULL = 300
GAME = (58, 64)
GAME_SCALE = 3
PAD = 12
LABEL_H = 34
BG = (24, 24, 24)
FG = (235, 235, 235)


def ingame_crop(im):
    w, h = im.size
    cw = int(h * GAME[0] / GAME[1])
    left = (w - cw) // 2
    return im.crop((left, 0, left + cw, h)).resize(GAME, Image.LANCZOS)


def label_for(path):
    return path.stem.removeprefix("hero-").replace("-", " ").title()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--cols", type=int, default=3)
    args = ap.parse_args()

    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    gw, gh = GAME[0] * GAME_SCALE, GAME[1] * GAME_SCALE
    card_w = FULL + PAD + gw
    card_h = max(FULL, gh) + LABEL_H
    paths = [pathlib.Path(f) for f in args.files]
    rows = (len(paths) + args.cols - 1) // args.cols
    sheet = Image.new("RGB", (args.cols * card_w + (args.cols + 1) * PAD * 2, rows * card_h + (rows + 1) * PAD * 2), BG)
    draw = ImageDraw.Draw(sheet)

    for i, path in enumerate(paths):
        r, c = divmod(i, args.cols)
        x = PAD * 2 + c * (card_w + PAD * 2)
        y = PAD * 2 + r * (card_h + PAD * 2)
        im = Image.open(path).convert("RGB")
        sheet.paste(im.resize((FULL, FULL), Image.LANCZOS), (x, y))
        sheet.paste(ingame_crop(im).resize((gw, gh), Image.NEAREST), (x + FULL + PAD, y))
        draw.text((x, y + max(FULL, gh) + 6), f"{i + 1}. {label_for(path)}", font=font, fill=FG)

    sheet.save(args.out)
    print(args.out, sheet.size)


if __name__ == "__main__":
    main()
