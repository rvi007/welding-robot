#!/usr/bin/env python3
"""Export the meshes used by the 3D viewer (docs/viewer) and the render script.

For every robot link and material it runs OpenSCAD on cad/assembly.scad
(LINK=n, MAT=name) and writes docs/viewer/models/L<n>_<mat>.stl, plus single
purchased parts for the parts catalog and a manifest.json. It also writes the
joint paths of the example jobs so the viewer can play them.

    OPENSCAD=/path/to/openscad python3 cad/render/export_models.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "cad"
OUT = ROOT / "docs" / "viewer" / "models"
JOBS_OUT = ROOT / "docs" / "viewer" / "jobs"
OPENSCAD = os.environ.get("OPENSCAD", "openscad")
FN = os.environ.get("VIEWER_FN", "48")

LINK_MATS = {
    0: ["printed2", "logo", "alu", "black", "steel", "rubber"],
    1: ["printed2", "printed", "logo", "alu", "black", "steel", "rubber"],
    2: ["printed", "logo", "alu", "black", "steel", "rubber"],
    3: ["printed", "logo", "alu", "black", "steel", "rubber"],
    4: ["printed", "alu", "black", "steel", "rubber"],
    5: ["printed2", "alu", "steel"],
    6: ["table", "block", "coupon"],
}

# purchased parts shown on their own in the parts catalog
CATALOG = {
    "gm17_48": "gearmotor_real(GM17_48);",
    "gm17_34": "gearmotor_real(GM17_34);",
    "gm23_56": "gearmotor_real(GM23_56);",
    "b608": "bearing(B608);",
    "b6008": "bearing(B6008);",
}
CATALOG_MATS = ["alu", "black", "steel", "rubber", "logo"]

MATERIALS = {
    "printed":  {"color": "#e8711a", "metalness": 0.0, "roughness": 0.55},
    "printed2": {"color": "#30353d", "metalness": 0.0, "roughness": 0.6},
    "logo":     {"color": "#f4f4f4", "metalness": 0.0, "roughness": 0.4},
    "alu":      {"color": "#cfd2d6", "metalness": 1.0, "roughness": 0.32},
    "black":    {"color": "#26282c", "metalness": 0.55, "roughness": 0.45},
    "steel":    {"color": "#b4b8bd", "metalness": 1.0, "roughness": 0.25},
    "rubber":   {"color": "#151515", "metalness": 0.0, "roughness": 0.85},
    "table":    {"color": "#5b6067", "metalness": 0.85, "roughness": 0.55},
    "block":    {"color": "#8d9298", "metalness": 0.6, "roughness": 0.6},
    "coupon":   {"color": "#8a8f95", "metalness": 0.9, "roughness": 0.45},
}


def run(args: list[str], out: Path) -> bool:
    out.unlink(missing_ok=True)
    cmd = [OPENSCAD, "-q", "--export-format", "binstl", "-D", f"$fn={FN}", *args, "-o", str(out)]
    subprocess.run(cmd, cwd=CAD, capture_output=True, text=True)
    return out.exists() and out.stat().st_size > 84


def export_link(link: int, mat: str):
    out = OUT / f"L{link}_{mat}.stl"
    ok = run(["-D", f"LINK={link}", "-D", f'MAT="{mat}"', "assembly.scad"], out)
    return link, mat, ok


def export_catalog(name: str, mat: str):
    src = CAD / "render" / f"_catalog_{name}.scad"
    src.write_text(f"include <../parts.scad>\ninclude <../vitamins.scad>\n{CATALOG[name]}\n")
    out = OUT / f"C_{name}_{mat}.stl"
    ok = run(["-D", f'MAT="{mat}"', str(src)], out)
    return name, mat, ok


def export_jobs():
    sys.path.insert(0, str(ROOT))
    from robot import config, gcode, weld  # noqa: E402

    robot = config.load()
    JOBS_OUT.mkdir(parents=True, exist_ok=True)
    for path in sorted((ROOT / "jobs").glob("*.json")):
        traj = gcode.solve(weld.plan_job(weld.load_job(path)), robot)
        frames = [{"q": [round(v, 3) for v in st.q], "dt": round(st.dt if st.kind == "move" else 0.8, 4),
                   "weld": bool(st.weld)} for st in traj.steps if st.q is not None]
        (JOBS_OUT / path.name).write_text(json.dumps({"name": traj.name, "frames": frames}))
        print(f"job {path.stem}: {len(frames)} frames")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = [(export_link, (l, m)) for l, mats in LINK_MATS.items() for m in mats]
    tasks += [(export_catalog, (n, m)) for n in CATALOG for m in CATALOG_MATS]
    links: dict[str, list] = {}
    catalog: dict[str, list] = {}
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        for fn, (a, b, ok) in zip(tasks, pool.map(lambda t: t[0](*t[1]), tasks)):
            if not ok:
                continue
            if fn[0] is export_link:
                links.setdefault(str(a), []).append({"file": f"L{a}_{b}.stl", "mat": b})
            else:
                catalog.setdefault(a, []).append({"file": f"C_{a}_{b}.stl", "mat": b})
            print(f"exported {a} {b}")
    for f in (CAD / "render").glob("_catalog_*.scad"):
        f.unlink()

    robot = json.loads((ROOT / "config" / "robot.json").read_text())
    g = robot["geometry"]
    manifest = {
        "geometry": {"d1": g["d1"], "l2": g["l2"], "l3": g["l3"], "tool": g["tool"]},
        "joints": [{"name": j["name"], "min": j["min"], "max": j["max"]} for j in robot["joints"]],
        "materials": MATERIALS,
        "links": links,
        "catalog": catalog,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    export_jobs()
    total = sum(p.stat().st_size for p in OUT.glob("*.stl"))
    print(f"{len(list(OUT.glob('*.stl')))} meshes, {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
