#!/usr/bin/env python3
"""Remove a painted "fake transparency" checkerboard (or any light, grey background).

The image model sometimes draws a light grey checkerboard instead of returning real
alpha. This clears every light, unsaturated pixel that is connected to the image border,
so white clothing inside the figure's outline is kept, plus enclosed gaps that show
the checkerboard's two tones, then trims a 1 px fringe.

Usage: tools/fix-background.py file1.png [file2.png ...]   (files are fixed in place;
images that already have real transparency are left alone)
"""
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


def fix(path):
    im = Image.open(path)
    rgba = np.array(im.convert("RGBA"))
    if (rgba[..., 3] < 10).mean() > 0.05:
        return "already transparent"
    rgb = rgba[..., :3].astype(int)
    light = (rgb.min(axis=2) >= 180) & ((rgb.max(axis=2) - rgb.min(axis=2)) <= 18)
    labels, _ = ndimage.label(light)
    border = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    background = np.isin(labels, border[border != 0])
    # Enclosed gaps (between an arm and the body, inside a sword's hole) are not connected
    # to the border. Clear one only when nearly all its pixels sit on the two exact grey
    # tones of this image's own checkerboard; polished metal and white cloth are gradients
    # and fail that test.
    value = rgb.max(axis=2)
    hist = np.bincount(value[background], minlength=256)
    tone1 = int(hist.argmax())
    far = hist.copy()
    far[max(0, tone1 - 12):tone1 + 13] = 0
    tone2 = int(far.argmax())
    if far[tone2] > 0.1 * hist[tone1]:
        sizes = ndimage.sum(light, labels, range(1, labels.max() + 1))
        for lab in np.nonzero(sizes > 120)[0] + 1:
            if lab in border:
                continue
            v = value[labels == lab]
            on1, on2 = (abs(v - tone1) <= 5).mean(), (abs(v - tone2) <= 5).mean()
            if on1 + on2 > 0.9 and min(on1, on2) > 0.15:
                background |= labels == lab
    background = ndimage.binary_dilation(background, iterations=1)
    rgba[..., 3] = np.where(background, 0, 255)
    out = Image.fromarray(rgba, "RGBA")
    alpha = out.getchannel("A").filter(ImageFilter.GaussianBlur(0.6))
    out.putalpha(alpha.point(lambda v: 0 if v < 110 else (255 if v > 200 else v)))
    out.save(path)
    return f"background removed ({background.mean():.0%} of the image)"


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p.split("/")[-1], "->", fix(p))
