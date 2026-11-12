#!/usr/bin/env python3
"""Generate mod art with the Codex CLI from a vault prompt note.

Reads the note's starter prompt and every `→ `file.png`` + text block pair,
then runs one `codex exec` per image with the reference sheet attached.
Extra images are attached when they exist: art/reference/characters/<file>
(official anime look, for likeness) and art/reference/upgrades/<file> (the
base creature, so an upgrade stays the same creature). Files already in art/inbox/ are skipped, so the script can be re-run safely.

Usage:
  tools/generate-art.py NOTE REFERENCE [--jobs 5] [--only file1.png,file2.png] [--feedback "extra text"]
"""
import argparse
import concurrent.futures
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
INBOX = ROOT / "art" / "inbox"
CHARACTERS = ROOT / "art" / "reference" / "characters"
UPGRADES = ROOT / "art" / "reference" / "upgrades"
ORDINALS = ["first", "second", "third"]
# Pinned: the Codex config default may name a model that ChatGPT-account logins can't use.
MODEL = "gpt-6-astra"
LOGS = ROOT / "art" / "logs"

LIKENESS = """The {nth} attached image shows the official anime look of this subject. Match its shape, face, hairstyle, colors, markings and outfit closely, but render it in the Heroes 3 style of the first image: realistic, not anime."""

UPGRADE = """The {nth} attached image is the base version of this creature, generated earlier in the same style. Make this upgrade clearly the same creature, only more elite: better gear, more intense colors, a stronger jutsu effect."""

RUN_INSTRUCTIONS = """Instructions for this run: generate exactly one image with your image generation tool, using the attached reference sheet as the style reference. Then copy the resulting PNG, unmodified (no resizing), to ./art/inbox/{fname}. Do not create or edit any other files. Reply with the saved path."""


def parse_note(path):
    text = pathlib.Path(path).read_text()
    starter = re.search(r"## Starter prompt\n.*?```text\n(.*?)\n```", text, re.S).group(1)
    items = re.findall(r"→ `([^`]+)`\n\n```text\n(.*?)\n```", text, re.S)
    return starter, items


def generate(fname, line, starter, reference, feedback, attempts=2):
    target = INBOX / fname
    extra = [(path, text) for path, text in ((CHARACTERS / fname, LIKENESS), (UPGRADES / fname, UPGRADE)) if path.exists()]
    prompt = f"{starter}\n\nSubject: {line}\n"
    for n, (_, text) in enumerate(extra, start=1):
        prompt += "\n" + text.format(nth=ORDINALS[n]) + "\n"
    if feedback:
        prompt += f"\nExtra direction for this image: {feedback}\n"
    prompt += "\n" + RUN_INSTRUCTIONS.format(fname=fname)
    for attempt in range(1, attempts + 1):
        start = time.time()
        log = LOGS / f"{target.stem}.attempt{attempt}.jsonl"
        with open(log, "w") as out:
            try:
                subprocess.run(
                    ["codex", "exec", "--skip-git-repo-check", "-C", str(ROOT), "-m", MODEL,
                     "-s", "workspace-write", "--json", "-i", str(reference),
                     *[arg for path, _ in extra for arg in ("-i", str(path))], "-"],
                    input=prompt, text=True, stdout=out, stderr=subprocess.STDOUT, timeout=900,
                )
            except subprocess.TimeoutExpired:
                pass
        if target.exists() and target.stat().st_size > 0:
            return fname, "ok", attempt, round(time.time() - start)
    return fname, "FAILED", attempts, 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("note")
    ap.add_argument("reference")
    ap.add_argument("--jobs", type=int, default=5)
    ap.add_argument("--only", default="")
    ap.add_argument("--feedback", default="")
    args = ap.parse_args()

    INBOX.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    starter, items = parse_note(args.note)
    only = {f.strip() for f in args.only.split(",") if f.strip()}
    todo = [(f, l) for f, l in items if (not only or f in only) and not (INBOX / f).exists()]
    print(f"{len(items)} items in note, {len(todo)} to generate, {args.jobs} in parallel", flush=True)

    failed = []
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        futures = [pool.submit(generate, f, l, starter, args.reference, args.feedback) for f, l in todo]
        for fut in concurrent.futures.as_completed(futures):
            fname, status, attempt, secs = fut.result()
            print(f"{status:6} {fname} (attempt {attempt}, {secs}s)", flush=True)
            if status != "ok":
                failed.append(fname)
    print(f"done: {len(todo) - len(failed)} ok, {len(failed)} failed {failed}", flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
