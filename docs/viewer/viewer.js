// RAVI WR-1 3D viewer: loads the meshes exported by cad/render/export_models.py,
// builds the joint chain, and plays the example weld jobs.
//
// URL options (also used by cad/render/shoot.mjs for the images in docs/):
//   ?q=18,40,12,0,-20     joint angles (deg)       ?view=hero|front|side|top|closeup
//   ?ui=0                 hide the panel           ?cell=0  hide table, block and coupon
//   ?path=fillet_straight draw that job's weld path on the coupon
//   ?jobframe=fillet_straight&t=0.4   still frame of a job at 40 % (used for the animation)
//   ?theme=dark           dark studio background
//   ?part=../../stl/turntable.stl&mat=printed2&rot=0,0,30   one printed part
//   ?catalog=gm17_48&rot=-90,0,0                           one purchased part

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/OrbitControls.js';
import { STLLoader } from 'three/addons/STLLoader.js';
import { RoomEnvironment } from 'three/addons/RoomEnvironment.js';
import { toCreasedNormals } from 'three/addons/BufferGeometryUtils.js';

THREE.Object3D.DEFAULT_UP.set(0, 0, 1);
const P = new URLSearchParams(location.search);
const deg = THREE.MathUtils.degToRad;
const nums = (s, n) => (s ? s.split(',').map(Number) : Array(n).fill(0));
if (P.get('ui') === '0') document.body.classList.add('hide-ui');

const THEMES = {
  light: { bg: '#dde1e6', floor: '#e4e7eb', fog: [2600, 6000] },
  dark:  { bg: '#1c1f24', floor: '#24282e', fog: [2000, 5000] },
};
const theme = THEMES[P.get('theme')] || THEMES.light;

// ---- renderer, scene, lights ---------------------------------------------------
const canvas = document.getElementById('view');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.background = new THREE.Color(theme.bg);
scene.fog = new THREE.Fog(theme.bg, ...theme.fog);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), 0.04).texture;

scene.add(new THREE.HemisphereLight(0xeef3f8, 0x50565e, 0.6));
const key = new THREE.DirectionalLight(0xffffff, 2.4);
key.position.set(520, -760, 1250);
key.castShadow = true;
key.shadow.mapSize.set(4096, 4096);
Object.assign(key.shadow.camera, { left: -650, right: 650, top: 650, bottom: -650, near: 50, far: 4000 });
key.shadow.bias = -0.0002;
key.shadow.normalBias = 0.6;
key.shadow.radius = 4;
scene.add(key, key.target);
const rim = new THREE.DirectionalLight(0xcfe0ff, 0.9);
rim.position.set(-800, 700, 600);
scene.add(rim);

const floor = new THREE.Mesh(new THREE.PlaneGeometry(20000, 20000),
  new THREE.MeshStandardMaterial({ color: theme.floor, roughness: 0.95, metalness: 0 }));
floor.receiveShadow = true;
scene.add(floor);

const camera = new THREE.PerspectiveCamera(32, 1, 5, 20000);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;

// ---- loading helpers ----------------------------------------------------------------
const loader = new STLLoader();
let MATERIALS = {};

function material(name) {
  const m = MATERIALS[name] || { color: '#888888', metalness: 0, roughness: 0.6 };
  const base = { color: new THREE.Color(m.color), metalness: m.metalness, roughness: m.roughness, envMapIntensity: 0.85 };
  return m.metalness < 0.1
    ? new THREE.MeshPhysicalMaterial({ ...base, clearcoat: 0.2, clearcoatRoughness: 0.55 })
    : new THREE.MeshStandardMaterial(base);
}

async function mesh(url, mat) {
  const g = toCreasedNormals(await loader.loadAsync(url), deg(32));
  const m = new THREE.Mesh(g, material(mat));
  m.castShadow = m.receiveShadow = true;
  return m;
}

function frame(view, box) {
  const VIEWS = {
    hero:    { pos: [820, 720, 480], target: [130, 0, 160], fov: 30 },
    drive:   { pos: [680, -900, 480], target: [20, -40, 200], fov: 30 },
    front:   { pos: [1250, 120, 330], target: [110, 0, 175], fov: 28 },
    side:    { pos: [140, -1250, 300], target: [110, 0, 175], fov: 28 },
    top:     { pos: [140, -20, 1500], target: [140, 0, 100], fov: 28 },
    closeup: { pos: [470, 380, 330], target: [215, 0, 130], fov: 28 },
  };
  if (box) {                                  // fit a single part
    const s = box.getBoundingSphere(new THREE.Sphere());
    const dist = (s.radius / Math.sin(deg(15))) * 1.08;
    const dir = new THREE.Vector3(0.62, -0.78, 0.5).normalize();
    camera.fov = 30;
    camera.position.copy(s.center).addScaledVector(dir, dist);
    controls.target.copy(s.center);
  } else {
    const v = VIEWS[view] || VIEWS.hero;
    camera.fov = v.fov;
    camera.position.set(...v.pos);
    controls.target.set(...v.target);
  }
  camera.updateProjectionMatrix();
  controls.update();
}

// ---- robot -------------------------------------------------------------------------
const links = Array.from({ length: 7 }, () => new THREE.Group());
let G = null;

function setPose(q) {
  links[1].rotation.set(0, 0, deg(q[0]));
  links[2].rotation.set(0, deg(q[1]), 0);
  links[3].rotation.set(0, deg(q[2]), 0);
  links[4].rotation.set(deg(q[3]), 0, 0);
  links[5].rotation.set(0, deg(q[4]), 0);
  scene.updateMatrixWorld(true);
}

function tip() { return links[5].localToWorld(new THREE.Vector3(0, 0, -G.tool)); }

async function loadRobot(manifest) {
  G = manifest.geometry;
  scene.add(links[0], links[6]);
  links[0].add(links[1]);
  links[1].add(links[2]); links[2].position.set(0, 0, G.d1);
  links[2].add(links[3]); links[3].position.set(0, 0, G.l2);
  links[3].add(links[4]); links[4].position.set(G.l3, 0, 0);
  links[4].add(links[5]);
  const jobs = [];
  for (const [n, parts] of Object.entries(manifest.links))
    for (const p of parts) jobs.push(mesh(`models/${p.file}`, p.mat).then(m => links[+n].add(m)));
  await Promise.all(jobs);
  floor.position.z = -15.2;
  links[6].visible = P.get('cell') !== '0';
}

async function loadJob(name) {
  return (await fetch(`jobs/${name}.json`)).json();
}

function drawPath(job) {
  const pts = [];
  for (const f of job.frames) if (f.weld) { setPose(f.q); pts.push(tip()); }
  if (pts.length < 2) return;
  const curve = new THREE.CatmullRomCurve3(pts);
  const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, pts.length * 2, 0.9, 8, false),
    new THREE.MeshStandardMaterial({ color: 0xffb347, emissive: 0xff7a1a, emissiveIntensity: 1.6, roughness: 0.4 }));
  scene.add(tube);
}

// ---- UI: sliders and job playback -------------------------------------------------
let pose = nums(P.get('q') || '18,40,12,0,-20', 5);
let playing = null;
const status = document.getElementById('status');
const sliders = [];

function buildSliders(joints) {
  const box = document.getElementById('sliders');
  joints.forEach((j, i) => {
    const row = document.createElement('label');
    row.className = 'row';
    row.innerHTML = `<span>${j.name.split(' ')[0]} ${j.name.split(' ').slice(1).join(' ')}</span>
      <input type="range" min="${j.min}" max="${j.max}" step="0.5" value="${pose[i]}"><output>${pose[i]}°</output>`;
    const input = row.querySelector('input'), out = row.querySelector('output');
    input.addEventListener('input', () => { playing = null; pose[i] = +input.value; out.textContent = `${pose[i]}°`; setPose(pose); });
    sliders.push({ input, out });
    box.appendChild(row);
  });
}

function syncSliders() {
  sliders.forEach((s, i) => { s.input.value = pose[i]; s.out.textContent = `${pose[i].toFixed(0)}°`; });
}

const spark = new THREE.PointLight(0x9ecbff, 0, 260, 2);
const sparkDot = new THREE.Mesh(new THREE.SphereGeometry(2.2, 16, 12),
  new THREE.MeshBasicMaterial({ color: 0xe8f2ff }));
spark.add(sparkDot);
sparkDot.visible = false;
scene.add(spark);
let trail = null;

async function play(name) {
  const job = await loadJob(name);
  if (trail) scene.remove(trail);
  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(job.frames.length * 3), 3));
  geom.setDrawRange(0, 0);
  trail = new THREE.Line(geom, new THREE.LineBasicMaterial({ color: 0xff8a2a }));
  scene.add(trail);
  playing = { job, i: 0, t: 0, n: 0 };
  status.textContent = job.name;
}

document.getElementById('play').onclick = () => play(document.getElementById('job').value);
document.getElementById('ready').onclick = () => { playing = null; pose = [0, 0, 0, 0, 0]; syncSliders(); setPose(pose); };

const clock = new THREE.Clock();
function animate() {
  const dt = Math.min(clock.getDelta(), 0.1);
  if (playing) {
    const { job } = playing;
    playing.t += dt;
    while (playing.i < job.frames.length - 1 && playing.t > job.frames[playing.i + 1].dt) {
      playing.t -= job.frames[playing.i + 1].dt;
      playing.i += 1;
      const f = job.frames[playing.i];
      if (f.weld) {
        setPose(f.q);
        const p = tip();
        trail.geometry.attributes.position.setXYZ(playing.n++, p.x, p.y, p.z);
        trail.geometry.attributes.position.needsUpdate = true;
        trail.geometry.setDrawRange(0, playing.n);
      }
    }
    const f = job.frames[playing.i];
    pose = [...f.q];
    setPose(pose);
    syncSliders();
    const on = f.weld;
    spark.position.copy(tip());
    spark.intensity = on ? 40000 * (0.7 + 0.3 * Math.random()) : 0;
    sparkDot.visible = on;
    if (playing.i >= job.frames.length - 1) { playing = null; spark.intensity = 0; sparkDot.visible = false; status.textContent = 'Done'; }
  }
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

function resize() {
  const w = +(P.get('w') || window.innerWidth), h = +(P.get('h') || window.innerHeight);
  renderer.setSize(w, h, false);
  canvas.style.width = `${w}px`; canvas.style.height = `${h}px`;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);

// ---- main --------------------------------------------------------------------------------
async function main() {
  resize();
  const manifest = await (await fetch('models/manifest.json')).json();
  MATERIALS = manifest.materials;
  const part = P.get('part'), cat = P.get('catalog');
  if (part || cat) {
    const group = new THREE.Group();
    const items = part ? [{ file: part, mat: P.get('mat') || 'printed' }]
                       : manifest.catalog[cat].map(c => ({ file: `models/${c.file}`, mat: c.mat }));
    for (const it of items) group.add(await mesh(it.file, it.mat));
    const r = nums(P.get('rot'), 3);
    group.rotation.set(deg(r[0]), deg(r[1]), deg(r[2]));
    scene.add(group);
    group.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(group);
    group.position.set(-(box.min.x + box.max.x) / 2, -(box.min.y + box.max.y) / 2, -box.min.z);
    group.updateMatrixWorld(true);
    key.position.set(320, -460, 900);
    frame(null, new THREE.Box3().setFromObject(group));
    document.getElementById('panel').style.display = 'none';
  } else {
    await loadRobot(manifest);
    buildSliders(manifest.joints);
    if (P.get('path')) drawPath(await loadJob(P.get('path')));
    if (P.get('jobframe')) {
      const job = await loadJob(P.get('jobframe'));
      const last = Math.round((+P.get('t') || 0) * (job.frames.length - 1));
      const done = [];
      job.frames.slice(0, last + 1).forEach(f => { if (f.weld) { setPose(f.q); done.push(tip()); } });
      if (done.length > 1) {
        const bead = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(done), done.length * 2, 1.4, 8, false),
          new THREE.MeshStandardMaterial({ color: 0x9a8f86, metalness: 0.7, roughness: 0.35 }));
        bead.castShadow = true;
        scene.add(bead);
      }
      const f = job.frames[last];
      pose = [...f.q];
      setPose(pose);
      if (f.weld) { spark.position.copy(tip()); spark.intensity = 60000; sparkDot.visible = true; sparkDot.scale.setScalar(1.6); }
    }
    setPose(pose);
    frame(P.get('view'));
    status.textContent = 'Drag to orbit, scroll to zoom.';
  }
  renderer.render(scene, camera);
  requestAnimationFrame(() => { renderer.render(scene, camera); window.__ready = true; });
  animate();
}
main().catch(e => { status.textContent = `Error: ${e.message}`; console.error(e); window.__error = String(e); });
