import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { verifyCrud } from '../../scripts/verify_crud.mjs';

const expectedSha = 'a'.repeat(40);
const options = { environment: 'disposable', expectedSha, allowWrites: true };

for (const url of [
    'https://phishlens-api-ocvt.onrender.com',
    'https://example.test',
    'https://phishlens-staging.onrender.com.evil.invalid',
    'http://127.0.0.1:8000/path',
    'http://user:password@localhost:8000'
]) {
    test('imported runner rejects unsafe target ' + url, async () => {
        await assert.rejects(verifyCrud(url, options), /Target must|plain HTTP/);
    });
}

test('imported runner cannot omit write permission', async () => {
    await assert.rejects(verifyCrud('http://127.0.0.1:8000'), /write permission/);
});

test('requires a full backend SHA', async () => {
    await assert.rejects(verifyCrud('http://127.0.0.1:8000', { ...options, expectedSha: 'abc' }), /full expected/);
});

for (const scenario of ['production', 'wrong-sha', 'invalid-json', 'identity-503', 'not-ready', 'identity-redirect', 'post-redirect']) {
    test('refuses writes for ' + scenario, async () => {
        const requests = [];
        let redirectedWrites = 0;
        const destination = createServer((req, res) => {
            if (req.method !== 'GET') redirectedWrites++;
            res.end('{}');
        });
        await new Promise(resolve => destination.listen(0, '127.0.0.1', resolve));
        const server = createServer((req, res) => {
            requests.push({ method: req.method, path: req.url });
            res.setHeader('Content-Type', 'application/json');
            if ((scenario === 'identity-redirect' && req.url === '/version') ||
                (scenario === 'post-redirect' && req.method === 'POST')) {
                res.writeHead(307, { Location: 'http://127.0.0.1:' + destination.address().port });
                return res.end();
            }
            if (req.url === '/version') {
                if (scenario === 'identity-503') res.statusCode = 503;
                if (scenario === 'invalid-json') return res.end('not-json');
                return res.end(JSON.stringify({
                    environment: scenario === 'production' ? 'production' : 'disposable',
                    commit: scenario === 'wrong-sha' ? 'b'.repeat(40) : expectedSha
                }));
            }
            if (req.url === '/ready') {
                if (scenario === 'not-ready') res.statusCode = 503;
                return res.end(JSON.stringify({ status: 'ready', database: 'connected' }));
            }
            res.statusCode = 500;
            res.end('{}');
        });
        await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
        try {
            await assert.rejects(verifyCrud('http://127.0.0.1:' + server.address().port, options));
            if (scenario !== 'post-redirect') assert.ok(requests.every(request => request.method === 'GET'));
            assert.equal(redirectedWrites, 0);
        } finally {
            await new Promise(resolve => server.close(resolve));
            await new Promise(resolve => destination.close(resolve));
        }
    });
}
