let worker, active, ready = false, idle;
function stop(code) {
  worker?.terminate(); worker = undefined; ready = false;
  if (active) { clearTimeout(active.timer); clearInterval(active.heartbeat);
    active.respond({ ok: false, code }); active = undefined; }
}
function finish(result) {
  if (!active) return;
  clearTimeout(active.timer); clearInterval(active.heartbeat);
  active.respond(result); active = undefined;
  clearTimeout(idle); idle = setTimeout(() => stop('idle_unload'), 5 * 60 * 1000);
}
function createWorker() {
  worker = new Worker(chrome.runtime.getURL('ai/judge-worker.mjs'), { type: 'module' });
  worker.onmessage = ({ data }) => {
    if (!active || data.jobId !== active.jobId) return;
    if (data.type === 'ready') {
      // First inference also compiles GPU kernels. It remains inside the bounded
      // cold-readiness deadline; subsequent scans use the warm deadline.
      ready = true;
    } else if (data.type === 'progress') {
      chrome.runtime.sendMessage({ ...data, type: 'phishlens-judge-progress' }).catch(() => {});
    } else if (data.type === 'result') finish({ ok: true, ...data });
    else if (data.type === 'failure') {
      console.error('PhishLens local judge runtime failure at ' + data.diagnostic?.phase);
      finish({ ok: false, code: data.code, diagnostic: data.diagnostic });
    }
  };
  worker.onerror = () => stop('local_judge_failed');
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (sender.id !== chrome.runtime.id) return;
  if (message?.type === 'phishlens-cancel-judge') {
    if (active) stop('cancelled');
    respond({ ok: true }); return;
  }
  if (message?.type !== 'phishlens-run-judge') return;
  clearTimeout(idle);
  if (active) stop('superseded');
  if (!worker) createWorker();
  active = { jobId: message.jobId, respond,
    timer: setTimeout(() => stop('judge_timeout'), ready ? 15000 : 120000),
    heartbeat: setInterval(() => chrome.runtime.sendMessage({ type: 'phishlens-judge-heartbeat', jobId: message.jobId }).catch(() => {}), 2000) };
  worker.postMessage({ jobId: message.jobId, primary: message.primary });
  return true;
});
