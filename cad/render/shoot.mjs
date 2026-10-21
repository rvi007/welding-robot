// Render the documentation images with the 3D viewer in headless Chromium.
//
//   npm install playwright-core@1.56.1
//   CHROME=/path/to/chrome node cad/render/shoot.mjs .      (from the repository root;
//   ONLY=<regex> renders just the matching images)
//
// Writes docs/images/*.png (assembly views) and docs/images/parts/*.png (catalog).

import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, join, resolve } from 'node:path';
import { chromium } from 'playwright-core';

const ROOT = resolve(process.argv[2] || '.');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
                '.stl': 'model/stl', '.png': 'image/png', '.css': 'text/css' };

const server = createServer(async (req, res) => {
  try {
    const path = join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    if (!path.startsWith(ROOT)) throw new Error('outside root');
    const body = await readFile(path);
    res.writeHead(200, { 'Content-Type': TYPES[extname(path)] || 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404); res.end();
  }
}).listen(0);
const base = `http://127.0.0.1:${server.address().port}/docs/viewer/index.html`;

const SHOTS = [
  // [file, query, width, height]
  ['images/hero.png',      'view=hero&q=13.2,68.3,-27.1,-40.8,-12.2&path=fillet_straight', 1600, 1000],
  ['images/closeup.png',   'view=closeup&q=13.2,68.3,-27.1,-40.8,-12.2&path=fillet_straight', 1400, 1000],
  ['images/drive.png',     'view=drive&q=-10,25,15,0,-25&cell=0', 1400, 1000],
  ['images/front.png',     'view=front&q=0,30,10,0,-20', 1200, 900],
  ['images/side.png',      'view=side&q=0,40,5,0,-25', 1200, 900],
  ['images/ready.png',     'view=hero&q=0,0,0,0,0&cell=0', 1200, 1000],
];

const PRINTED = {
  base_floor: 'printed2', base_shell: 'printed2', j1_motor_mount: 'printed2', j1_spigot: 'printed2',
  j1_collar: 'printed2', turntable: 'printed2', upper_arm_drive: 'printed', upper_arm_idle: 'printed',
  forearm_drive: 'printed', forearm_idle: 'printed', wrist: 'printed', tool_holder: 'printed2',
  j2_cover: 'printed', j3_cover: 'printed', spacer_m8: 'printed2', endstop_clip: 'printed2', fit_test: 'printed2',
};
const ROT = { base_shell: '180,0,52', j2_cover: '180,0,30', j3_cover: '180,0,30', upper_arm_idle: '180,0,0',
              forearm_idle: '180,0,0', j1_spigot: '180,0,0', tool_holder: '0,0,30', wrist: '0,0,20' };
for (const [name, mat] of Object.entries(PRINTED))
  SHOTS.push([`images/parts/${name}.png`, `part=../../stl/${name}.stl&mat=${mat}&rot=${ROT[name] || '0,0,0'}`, 900, 700]);
for (const [name, rot] of [['gm17_48', '-90,0,35'], ['gm17_34', '-90,0,35'], ['gm23_56', '-90,0,35'], ['b608', '60,0,30'], ['b6008', '60,0,30']])
  SHOTS.push([`images/parts/${name}.png`, `catalog=${name}&rot=${rot}`, 900, 700]);

const browser = await chromium.launch({
  executablePath: process.env.CHROME,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
});
await mkdir(join(ROOT, 'docs/images/parts'), { recursive: true });
const only = process.env.ONLY ? new RegExp(process.env.ONLY) : null;
for (const [file, query, w, h] of SHOTS.filter(s => !only || only.test(s[0]))) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  page.on('pageerror', e => console.error(file, e.message));
  await page.goto(`${base}?ui=0&w=${w}&h=${h}&${query}`);
  await page.waitForFunction(() => window.__ready || window.__error, null, { timeout: 180000 });
  const err = await page.evaluate(() => window.__error);
  if (err) console.error(file, err);
  await page.waitForTimeout(300);
  await page.locator('#view').screenshot({ path: join(ROOT, 'docs', file) });
  console.log('wrote', file);
  await page.close();
}
await browser.close();
server.close();
