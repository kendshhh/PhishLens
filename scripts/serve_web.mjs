// Local preview of the generated static files and fixed-destination API routes.
// This server is loopback-only; it is not the production server.
import { createServer, request as httpRequest } from 'node:http';
import { request as httpsRequest } from 'node:https';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const dist = path.join(root, 'web', 'dist');
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.md': 'text/markdown; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8' };

export function createPreviewServer(config, { directory = dist } = {}) {
  return createServer(async (request, response) => {
  let incoming, urlPath;
  try { incoming = new URL(request.url, 'http://localhost'); urlPath = decodeURIComponent(incoming.pathname); }
  catch { response.writeHead(400).end(); return; }
  const headers = {};
  for (const rule of config.routes) {
    if (!rule.src || !new RegExp(rule.src).test(urlPath) || (rule.methods && !rule.methods.includes(request.method))) continue;
    Object.assign(headers, rule.headers);
    if (!rule.dest) continue;
    // The upstream hostname is configuration only. User input supplies a path,
    // never a full request URL, even after regex substitution/normalization.
    const upstream = new URL(rule.dest.replace(/\$\d+/g, ''));
    const upstreamPath = urlPath.replace(new RegExp(rule.src), rule.dest.slice(upstream.origin.length)) + incoming.search;
    if (!upstreamPath.startsWith('/') || upstreamPath.startsWith('//')) { response.writeHead(400, headers).end(); return; }
    try {
      const forwarded = { ...request.headers };
      for (const name of ['host', 'cookie', 'connection', 'transfer-encoding', 'content-length', 'accept-encoding']) delete forwarded[name];
      const chunks = []; let size = 0;
      for await (const chunk of request) {
        size += chunk.length;
        if (size > 131072) { response.writeHead(413, headers).end(); return; }
        chunks.push(chunk);
      }
      await new Promise((resolve, reject) => {
        const send = upstream.protocol === 'https:' ? httpsRequest : httpRequest;
        const proxied = send({ protocol: upstream.protocol, hostname: upstream.hostname,
          port: upstream.port, path: upstreamPath, method: request.method, headers: forwarded,
          signal: AbortSignal.timeout(30000) }, result => {
          // Node's native request never follows redirects. Never relay cookies.
          response.writeHead(result.statusCode, { 'Content-Type': result.headers['content-type'] || 'application/json', ...headers });
          result.on('error', reject);
          result.on('end', resolve);
          result.pipe(response);
        });
        proxied.on('error', reject);
        proxied.end(chunks.length ? Buffer.concat(chunks) : undefined);
      });
    } catch {
      if (response.headersSent) response.destroy();
      else response.writeHead(502, { 'Content-Type': 'application/json', ...headers }).end('{"detail":"API temporarily unavailable"}');
    }
    return;
  }
  if (!['GET', 'HEAD'].includes(request.method)) { response.writeHead(405, headers).end(); return; }
  let file = path.resolve(directory, '.' + (urlPath.endsWith('/') ? urlPath + 'index.html' : urlPath));
  if (file !== directory && !file.startsWith(directory + path.sep)) { response.writeHead(403).end(); return; }
  try {
    if ((await stat(file)).isDirectory()) file = path.join(file, 'index.html');
    const body = await readFile(file);
    response.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream',
      ...headers });
    response.end(request.method === 'HEAD' ? undefined : body);
  } catch {
    response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8', ...headers }).end('Not found');
  }
  });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const config = JSON.parse(await readFile(path.join(root, 'web/.build-routing.json'), 'utf8'));
  const port = Number(process.env.PORT) || 4173;
  createPreviewServer(config).listen(port, '127.0.0.1', () => console.log(`PhishLens web app: http://127.0.0.1:${port}/`));
}
