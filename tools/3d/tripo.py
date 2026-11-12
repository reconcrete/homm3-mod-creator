#!/usr/bin/env python3
"""Tripo API pipeline: image -> textured 3D model -> auto-rig -> preset animations.

Needs TRIPO_API_KEY in the environment (create it at https://developers.tripo3d.ai/en/keys).
Every step records its task id in WORK/tripo.json, so a rerun resumes instead of paying twice.

Usage:
  tripo.py balance
  tripo.py run IMAGE WORK [--rig-type biped] [--anims idle,walk,slash,hurt,fall] [--faces 20000]
      biped uses rig model v3.0-20260909 and presets preset:<name>
      other rig types use v2.5-20260210 and presets like preset:quadruped:walk (pass full names)

Outputs in WORK: model.glb (textured, unrigged), rigged.glb, anim-<name>.glb (rigged model with
that animation), tripo.json (task ids and credits).
"""
import argparse
import json
import os
import pathlib
import sys
import time
import urllib.request

import requests

BASE = "https://openapi.tripo3d.ai/v3"


def headers():
    key = os.environ.get("TRIPO_API_KEY")
    if not key:
        sys.exit("TRIPO_API_KEY is not set")
    return {"Authorization": f"Bearer {key}"}


def call(method, path, **kw):
    r = requests.request(method, BASE + path, headers=headers(), timeout=120, **kw)
    try:
        body = r.json()
    except ValueError:
        sys.exit(f"{method} {path}: HTTP {r.status_code} {r.text[:300]}")
    if r.status_code != 200 or body.get("code") != 0:
        sys.exit(f"{method} {path}: HTTP {r.status_code} {json.dumps(body)[:500]}")
    return body["data"]


def wait(task_id, label):
    start = time.time()
    while True:
        d = call("GET", f"/tasks/{task_id}")
        status = d.get("status")
        if status == "success":
            print(f"  {label}: done in {time.time() - start:.0f}s, {d.get('credits_consumed')} credits", flush=True)
            return d
        if status in ("failed", "cancelled", "banned", "expired", "unknown"):
            sys.exit(f"{label} {task_id} ended as {status}: {json.dumps(d)[:500]}")
        time.sleep(4)


def download(url, path):
    urllib.request.urlretrieve(url, path)   # model URLs expire after 5 minutes: fetch at once
    print(f"  saved {path.name} ({path.stat().st_size // 1024} KB)", flush=True)


def step(state, work, key, label, make):
    """Run one task unless WORK/tripo.json already has it; return its result."""
    if key in state and state[key].get("status") == "success":
        print(f"  {label}: reusing {state[key]['task_id']}", flush=True)
        return state[key]
    task_id = make()
    print(f"  {label}: task {task_id}", flush=True)
    state[key] = {"task_id": task_id, "status": "running"}
    save(work, state)
    result = wait(task_id, label)
    state[key] = {"task_id": task_id, "status": "success", "credits": result.get("credits_consumed"),
                  "output": result.get("output", {})}
    save(work, state)
    return state[key]


def save(work, state):
    (work / "tripo.json").write_text(json.dumps(state, indent=2))


def run(a):
    work = pathlib.Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    state = json.loads((work / "tripo.json").read_text()) if (work / "tripo.json").exists() else {}
    print(f"balance before: {call('GET', '/account/balance')}", flush=True)

    if "file_token" not in state:
        with open(a.image, "rb") as fh:
            state["file_token"] = call("POST", "/files", files={"file": fh})["file_token"]
        save(work, state)

    gen = step(state, work, "model", "image to model", lambda: call("POST", "/generation/image-to-model", json={
        "input": state["file_token"], "model": "P2-20260801", "face_limit": a.faces, "texture": True, "pbr": True,
    })["task_id"])
    if not (work / "model.glb").exists() and gen["output"].get("model_url"):
        download(gen["output"]["model_url"], work / "model.glb")
        gen = state["model"]

    check = step(state, work, "rigcheck", "rig check", lambda: call("POST", "/animations/rig-check", json={
        "input": state["model"]["task_id"]})["task_id"])
    print(f"  rig check says: {check['output']}", flush=True)
    if not check["output"].get("riggable", True):
        sys.exit("Tripo says this model cannot be rigged")

    biped = a.rig_type == "biped"
    rig = step(state, work, "rig", "auto rig", lambda: call("POST", "/animations/rig", json={
        "input": state["model"]["task_id"], "rig_type": a.rig_type,
        "model": "v3.0-20260909" if biped else "v2.5-20260210", "out_format": "glb",
    })["task_id"])
    if not (work / "rigged.glb").exists():
        download(rig["output"]["model_url"], work / "rigged.glb")

    for name in a.anims.split(","):
        preset = name if name.startswith("preset:") else f"preset:{name}"
        short = preset.split(":")[-1]
        res = step(state, work, f"anim:{short}", f"animation {short}", lambda: call("POST", "/animations/retarget", json={
            "input": state["rig"]["task_id"], "animation": preset, "out_format": "glb", "animate_in_place": True,
        })["task_id"])
        if not (work / f"anim-{short}.glb").exists():
            download(res["output"]["model_url"], work / f"anim-{short}.glb")

    print(f"balance after: {call('GET', '/account/balance')}", flush=True)
    total = sum(float(v.get("credits") or 0) for v in state.values() if isinstance(v, dict))
    print(f"credits used by this creature: {total:.0f}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("balance")
    r = sub.add_parser("run")
    r.add_argument("image")
    r.add_argument("work")
    r.add_argument("--rig-type", default="biped")
    r.add_argument("--anims", default="idle,walk,slash,hurt,fall")
    r.add_argument("--faces", type=int, default=20000)
    a = ap.parse_args()
    if a.cmd == "balance":
        print(call("GET", "/account/balance"))
    else:
        run(a)


if __name__ == "__main__":
    main()
