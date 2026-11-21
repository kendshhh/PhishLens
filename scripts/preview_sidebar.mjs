// Preview the extension's side panel in any browser without loading the extension.
// Serves extension/popup.html at http://127.0.0.1:8767/ with preview/sidebar-preview.mjs
// standing in for the extension APIs. Only extension/ and preview/ files are served.
// Edit files and refresh the page to see changes. Uses only Node built-ins.
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const port = Number(process.env.SIDEBAR_PREVIEW_PORT) || 8767;
const allowed = ['extension', 'preview'].map(folder => path.join(root, folder));
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.wasm': 'application/wasm' };

// Shows the page at side-panel width against a darker backdrop, like Chrome's panel.
const FRAME = '<style>:root:root{background:#cfd8e4}body{box-shadow:0 0 0 1px #b9c5d6,0 10px 30px #1935522e}</style>';

createServer(async (request, response) => {
  try {
    const urlPath = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    if (urlPath === '/' || urlPath === '/sidebar') {
      let page = await readFile(path.join(root, 'extension', 'popup.html'), 'utf8');
      page = page.replace('<head>', '<head><base href="/extension/">')
        .replace('</head>', `${FRAME}</head>`)
        .replace('src="popup.js"', 'src="/preview/sidebar-preview.mjs"');
      response.writeHead(200, { 'Content-Type': TYPES['.html'], 'Cache-Control': 'no-store' }).end(page);
      return;
    }
    const file = path.resolve(root, '.' + urlPath);
    if (!allowed.some(folder => file.startsWith(folder + path.sep)) || !(await stat(file)).isFile()) throw Error('not found');
    response.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' })
      .end(await readFile(file));
  } catch {
    response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }).end('Not found');
  }
}).listen(port, '127.0.0.1', () => console.log(`PhishLens sidebar preview: http://127.0.0.1:${port}/`));
