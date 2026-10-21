# RAVI WR-1 3D viewer

An interactive 3D model of the robot. Drag to orbit, scroll to zoom, move each joint with the sliders, and play the example weld jobs.

**Open it locally.** Browsers block loading model files straight from disk, so serve the repository:

```bash
python -m http.server 8000          # from the repository root
# open http://localhost:8000/docs/viewer/
```

**Host it on GitHub Pages.** Go to *Settings → Pages*, choose this branch and the root folder. The viewer is then at `https://<user>.github.io/<repo>/docs/viewer/`.

URL options, also used to make the documentation images:

| Option | Example | Effect |
|---|---|---|
| `q` | `q=0,30,10,0,-20` | joint angles J1–J5 in degrees |
| `view` | `view=hero`, `drive`, `front`, `side`, `top`, `closeup` | camera preset |
| `cell` | `cell=0` | hide the table, block and coupon |
| `path` | `path=fillet_straight` | draw that job's weld path |
| `jobframe`, `t` | `jobframe=fillet_straight&t=0.5` | still frame halfway through a job |
| `part`, `mat`, `rot` | `part=../../stl/turntable.stl&mat=printed2&rot=0,0,30` | show one printed part |
| `catalog` | `catalog=gm17_48` | show one purchased part (`gm17_48`, `gm17_34`, `gm23_56`, `b608`, `b6008`) |
| `theme` | `theme=dark` | dark studio |
| `ui` | `ui=0` | hide the panel |

## Regenerating

The meshes in `models/` and the joint paths in `jobs/` are generated from the CAD and the software:

```bash
OPENSCAD=/path/to/openscad python3 cad/render/export_models.py
```

The documentation images in `docs/images` are rendered by headless Chromium. This needs Node.js and `npm install playwright-core`:

```bash
CHROME=/path/to/chrome node cad/render/shoot.mjs .                                # stills + parts catalog
CHROME=/path/to/chrome node cad/render/animate.mjs . fillet_straight 44 frames    # animation frames
```

Rendering uses [three.js](https://threejs.org) r160 (MIT license, `vendor/three-LICENSE.txt`). The bundled copy has one unused legacy object-type alias removed from its JSON scene loader; otherwise it is unmodified.
