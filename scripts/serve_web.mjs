// Serve web/dist on http://127.0.0.1:4173 for local preview, applying the same
// response headers as vercel.json so Content-Security-Policy problems show up locally.
// Run `npm run web:build` first. Uses only Node built-ins.
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const dist = path.join(root, 'web', 'dist');
const port = Number(process.env.PORT) || 4173;
const config = JSON.parse(await readFile(path.join(root, 'vercel.json'), 'utf8'));
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.md': 'text/markdown; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8' };

function headersFor(urlPath) {
  const headers = {};
  for (const rule of config.headers) {
    const pattern = new RegExp('^' + rule.source.replace(/\(\.\*\)/g, '.*') + '$');
    if (pattern.test(urlPath)) for (const { key, value } of rule.headers) headers[key] = value;
  }
  return headers;
}

createServer(async (request, response) => {
  const urlPath = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
  let file = path.resolve(dist, '.' + (urlPath.endsWith('/') ? urlPath + 'index.html' : urlPath));
  if (file !== dist && !file.startsWith(dist + path.sep)) { response.writeHead(403).end(); return; }
  try {
    if ((await stat(file)).isDirectory()) file = path.join(file, 'index.html');
    const body = await readFile(file);
    response.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream',
      ...headersFor(urlPath) });
    response.end(request.method === 'HEAD' ? undefined : body);
  } catch {
    response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }).end('Not found');
  }
}).listen(port, '127.0.0.1', () => console.log(`PhishLens web app: http://127.0.0.1:${port}/`));
