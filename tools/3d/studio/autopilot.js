// Tripo Studio animation autopilot. Paste into a model's Animate page (Claude in Chrome
// javascript_tool), then call window.__ap.start([...steps]). Studio runs one animation task per
// model at a time, so this applies the steps one by one: it clicks a step, waits while the page
// shows Retargeting / Generating / Queuing, then moves on. Steps:
//   'idle'              a preset from the Preset tab, by its exact name
//   {ai: 'Ninja Block'} a saved AI motion from the AI Animation tab, by the start of its name
//                       (motions made on one model are listed on every model)
// window.__ap.status() -> {step, left, busy, log}; a step busy for 6+ minutes is logged 'STUCK'
// (cancel it in Studio and call window.__ap.retry()).
(() => {
  if (window.__ap) return 'already';
  const ap = { queue: [], log: [], current: null, clickedAt: 0, busySince: 0, timer: null };
  const busy = () => /Retargeting|Generating\.\.\.|Queuing/.test(document.body.innerText);
  const buttons = () => [...document.querySelectorAll('button, [role="tab"]')];
  const tab = (label) => {
    const t = buttons().find(b => b.innerText.trim() === label);
    if (t) t.click();
    return !!t;
  };
  const tile = (match) => buttons().find(b => match(b.innerText.trim()));
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  async function apply(step) {   // a tab's list renders a moment after switching to it
    if (typeof step === 'string') {
      tab('Preset');
      let b = null;   // coming back from the AI tab, the preset list can take a few seconds to render
      for (let i = 0; i < 6 && !b; i++) { await sleep(1200); b = tile(t => t === step || t.split('\n').pop() === step); }
      if (!b) return 'no preset ' + step;
      b.click(); return 'preset ' + step;
    }
    tab('AI Animation'); await sleep(1200);
    const b = tile(t => t.toLowerCase().startsWith(step.ai.toLowerCase()) || t.split('\n').pop().toLowerCase().startsWith(step.ai.toLowerCase()));
    if (!b) return 'no AI motion ' + step.ai;
    b.click(); return 'ai ' + step.ai;
  }
  async function tick() {
    const now = Date.now();
    if (now - ap.clickedAt < 8000) return;
    // Studio can take a while to show a new task as busy; clicking the next clip before then
    // replaces the pending one, so a step counts as done only after it was seen busy (or 45 s).
    if (ap.current && !ap.sawBusy && !busy() && now - ap.clickedAt < 45000) return;
    if (busy()) {
      ap.sawBusy = true;
      if (!ap.busySince) ap.busySince = now;
      if (now - ap.busySince > 360000 && !ap.stuck) { ap.stuck = true; ap.log.push('STUCK ' + JSON.stringify(ap.current)); }
      return;
    }
    if (ap.current) { ap.log.push('done ' + JSON.stringify(ap.current) + ' ' + Math.round((now - ap.startedAt) / 1000) + 's'); ap.current = null; }
    ap.busySince = 0; ap.stuck = false;
    const next = ap.queue.shift();
    if (next === undefined) { clearInterval(ap.timer); ap.timer = null; ap.log.push('ALL DONE'); return; }
    ap.current = next; ap.startedAt = now; ap.clickedAt = now; ap.sawBusy = false;
    ap.log.push(await apply(next));
  }
  ap.start = (steps) => { ap.queue.push(...steps); if (!ap.timer) ap.timer = setInterval(tick, 3000); return ap.queue.length; };
  ap.retry = () => { if (ap.current) ap.queue.unshift(ap.current); ap.current = null; ap.stuck = false; ap.busySince = 0; ap.clickedAt = 0; if (!ap.timer) ap.timer = setInterval(tick, 3000); };
  ap.status = () => ({ step: ap.current, left: ap.queue.length, busy: busy(), log: ap.log.slice(-8) });
  window.__ap = ap;
  return 'autopilot ready';
})()
