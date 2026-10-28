import { appendFileSync, readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

export function classify(item, files = [], linked = []) {
  const labels = new Set();
  const title = item.title || '';
  // Ignore template/checklist prose: it mentions unrelated components.
  const text = title.toLowerCase();
  const type = title.match(/^(fix|docs|feat|ci|chore|test|refactor|perf|build)(?:\s|\(|:|!)/i)?.[1]?.toLowerCase();
  if (type === 'fix') labels.add('bug');
  else if (type === 'docs') labels.add('documentation');
  else if (type) labels.add('enhancement');
  const areas = {
    devops: /\b(devops|ci|pipeline|deploy|deployment|workflow|consultation)\b/,
    frontend: /\b(frontend|extension|popup|browser|ui|api-client)\b/,
    backend: /\b(backend|endpoint|endpoints)\b/,
    database: /\b(database|postgresql|postgres|schema|migration|persistence)\b/,
    api: /\b(api|api-client|endpoint|endpoints|http)\b/,
    ai: /\b(ai|model|inference|distilbert|gemini|classifier)\b/,
    integration: /\b(integration|integrate|end-to-end)\b/,
    testing: /\b(test|tests|testing|acceptance|smoke)\b/
  };
  for (const [area, pattern] of Object.entries(areas)) {
    if (pattern.test(text)) labels.add('area: ' + area);
  }
  for (const file of files) {
    if (/^\.github\/|^scripts\//.test(file)) labels.add('area: devops');
    if (/^extension\//.test(file)) labels.add('area: frontend');
    if (/^backend\//.test(file)) labels.add('area: backend');
    if (/^backend\/(alembic|migrations)\//.test(file)) labels.add('area: database');
    if (/^backend\/app\/ai\//.test(file)) labels.add('area: ai');
    if (/(^|\/)(tests?|__tests__)(\/|\.)|\.test\./.test(file)) labels.add('area: testing');
    if (/\.md$/.test(file)) labels.add('documentation');
  }
  const planning = title + '\n' + (item.body || '');
  for (const match of planning.matchAll(/\b(?:sprint[- :]*|s)([12])(?:\b|[- ])/gi)) labels.add('sprint-' + match[1]);
  for (const match of planning.matchAll(/\bpriority\s*:\s*(P[01])\b/gi)) labels.add('priority:' + match[1].toUpperCase());
  // Only inherit descriptive labels from explicit same-repository issue links.
  for (const issue of linked) for (const label of issue.labels || []) {
    const name = typeof label === 'string' ? label : label.name;
    if (/^(area: |sprint-)/.test(name)) labels.add(name);
  }
  if (![...labels].some(x => ['bug', 'documentation', 'enhancement'].includes(x))) labels.add('enhancement');
  return [...labels].sort();
}

export function linkedNumbers(body, repo) {
  const numbers = new Set();
  for (const line of (body || '').split('\n')) {
    const match = line.match(/^\s*(?:[-*]\s*)?(?:closes?|fix(?:es)?|resolves?|related to|related issue:?)[ :]+(.+)$/i);
    if (!match) continue;
    for (const ref of match[1].matchAll(/(?:^|[\s,;])#([1-9]\d*)\b/g)) numbers.add(Number(ref[1]));
    for (const ref of match[1].matchAll(/https:\/\/github\.com\/([^/]+\/[^/]+)\/issues\/([1-9]\d*)\b/g)) {
      if (ref[1].toLowerCase() === repo.toLowerCase()) numbers.add(Number(ref[2]));
    }
  }
  return [...numbers].slice(0, 20);
}

export async function runLabeler({ env = process.env, fetchImpl = fetch } = {}) {
  const repo = env.GITHUB_REPOSITORY;
  const token = env.GITHUB_TOKEN;
  async function api(path, method = 'GET', data) {
    const url = 'https://api.github.com/repos/' + repo + '/' + path;
    const options = {
      method, headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' },
      ...(data ? { body: JSON.stringify(data) } : {}),
      signal: AbortSignal.timeout(30000)
    };
    let response = await fetchImpl(url, options);
    if (!response.ok && response.status === 403 && method === 'GET' && data === undefined) {
      const publicOptions = { ...options, headers: { ...options.headers } };
      delete publicOptions.headers.Authorization;
      response = await fetchImpl(url, publicOptions);
    }
    if (!response.ok) {
      const error = new Error('GitHub HTTP ' + response.status);
      error.status = response.status;
      throw error;
    }
    return response.json();
  }
  try {
    async function pages(path) {
      const rows = [];
      for (let page = 1; page <= 30; page++) {
        const result = await api(path + (path.includes('?') ? '&' : '?') + 'per_page=100&page=' + page);
        rows.push(...result);
        if (result.length < 100) return rows;
      }
      throw new Error('Pagination limit reached');
    }
    const event = JSON.parse(readFileSync(env.GITHUB_EVENT_PATH, 'utf8'));
    const number = event.issue?.number || event.pull_request?.number;
    if (!number) throw new Error('Missing issue or PR number');
    // Use the webhook snapshot for item data; pull_request_target already receives the
    // base-repository event payload and this avoids an unnecessary issue lookup.
    const item = event.issue || event.pull_request;
    const isPullRequest = Boolean(event.pull_request);
    const files = isPullRequest ? (await pages('pulls/' + number + '/files')).map(x => x.filename) : [];
    const linked = [];
    if (isPullRequest) for (const n of linkedNumbers(item.body, repo)) {
      try { linked.push(await api('issues/' + n)); }
      catch (error) { if (!error.message.endsWith('404')) throw error; }
    }
    const available = new Set((await pages('labels')).map(x => x.name));
    const current = new Set(item.labels.map(x => x.name));
    const additions = classify(item, files, linked).filter(x => available.has(x) && !current.has(x));
    if (additions.length) await api('issues/' + number + '/labels', 'POST', { labels: additions });
    console.log('Item #' + number + ': added ' + (additions.join(', ') || 'no labels'));
    return { skipped: false, additions };
  } catch (error) {
    if (error.status !== 403) throw error;
    const warning = 'Automatic labeling skipped because GitHub denied API access (HTTP 403); no labels were changed. Check repository or organization Actions token restrictions. CI continues.';
    console.warn('::warning::' + warning);
    if (env.GITHUB_STEP_SUMMARY) appendFileSync(env.GITHUB_STEP_SUMMARY, warning + '\n');
    return { skipped: true, reason: 'github-api-forbidden' };
  }
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await runLabeler();
