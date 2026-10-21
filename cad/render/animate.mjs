// Capture still frames of a weld job from the 3D viewer (headless Chromium).
// Usage: CHROME=/path/to/chrome node cad/render/animate.mjs <repo root> <job> <frames> <out dir>
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, join, resolve } from 'node:path';
import { chromium } from 'playwright-core';

const [root = '.', job = 'fillet_straight', count = '40', outDir = 'frames'] = process.argv.slice(2);
const ROOT = resolve(root);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.stl': 'model/stl' };
const server = createServer(async (req, res) => {
  try {
    const path = join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    if (!path.startsWith(ROOT)) throw new Error('outside root');
    const body = await readFile(path);
    res.writeHead(200, { 'Content-Type': TYPES[extname(path)] || 'application/octet-stream' });
    res.end(body);
  } catch { res.writeHead(404); res.end(); }
}).listen(0);
const base = `http://127.0.0.1:${server.address().port}/docs/viewer/index.html`;
const browser = await chromium.launch({ executablePath: process.env.CHROME,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
await mkdir(outDir, { recursive: true });
const n = +count, w = 800, h = 560;
for (let i = 0; i < n; i++) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  await page.goto(`${base}?ui=0&w=${w}&h=${h}&view=closeup&jobframe=${job}&t=${(i / (n - 1)).toFixed(4)}`);
  await page.waitForFunction(() => window.__ready || window.__error, null, { timeout: 180000 });
  await page.locator('#view').screenshot({ path: join(outDir, `f${String(i).padStart(3, '0')}.png`) });
  await page.close();
  process.stdout.write('.');
}
await browser.close();
server.close();
console.log(' done');
