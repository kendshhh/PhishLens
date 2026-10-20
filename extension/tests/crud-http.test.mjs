import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { verifyCrud } from '../../scripts/verify_crud.mjs';

test('CRUD acceptance runner works over HTTP against a local substitute', async () => {
    const records = new Map();
    const methods = [];
    const server = createServer(async (req, res) => {
        methods.push(req.method);
        res.setHeader('Content-Type', 'application/json');
        function send(status, data) {
            res.statusCode = status;
            res.end(data === undefined ? undefined : JSON.stringify(data));
        }
        if (req.url === '/version') return send(200, { environment: 'disposable', commit: 'a'.repeat(40) });
        if (req.url === '/ready') return send(200, { status: 'ready', database: 'connected' });
        let text = '';
        for await (const chunk of req) text += chunk;
        const input = text ? JSON.parse(text) : {};
        if (req.url === '/api/analyses' && req.method === 'POST') {
            const record = {
                id: crypto.randomUUID(), ...input, prediction: null, confidence: null,
                risk_level: null, threat_indicators: [], explanation: null,
                created_at: new Date().toISOString(), notes: null, feedback: 'none', analysis_mode: 'mock'
            };
            records.set(record.id, record);
            return send(201, record);
        }
        if (req.url === '/api/analyses' && req.method === 'GET') return send(200, { items: [...records.values()] });
        const id = req.url.split('/').pop();
        const record = records.get(id);
        if (!record) return send(404, { detail: 'Analysis not found' });
        if (req.method === 'GET') return send(200, record);
        if (req.method === 'PATCH') {
            Object.assign(record, input);
            return send(200, record);
        }
        if (req.method === 'DELETE') {
            records.delete(id);
            return send(204);
        }
        send(405, { detail: 'Method not allowed' });
    });
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    try {
        const result = await verifyCrud('http://127.0.0.1:' + server.address().port, { environment: 'disposable', expectedSha: 'a'.repeat(40), allowWrites: true });
        assert.equal(result.result, 'passed');
        assert.deepEqual(methods.slice(0, 3), ['GET', 'GET', 'POST']);
        assert.equal(records.size, 0);
        assert.ok(methods.includes('POST') && methods.includes('PATCH') && methods.includes('DELETE'));
    } finally {
        await new Promise(resolve => server.close(resolve));
    }
});
