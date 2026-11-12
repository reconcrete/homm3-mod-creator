// Paste into a Tripo Studio tab (Claude in Chrome javascript_tool) before clicking Export.
// Studio's Export ends in an <a download> click, which Chrome blocks in the controlled tab;
// this takes the file inside the page and POSTs it to tools/3d/studio/receiver.py instead.
// Set window.__expName to the file name the receiver should save, e.g. 'genin-export.glb'.
window.__exp = window.__exp || [];
if (!window.__expHooked) {
  window.__expHooked = true;
  const post = (u, name) => {
    window.__exp.push('fetching ' + name);
    fetch(u).then(r => r.arrayBuffer())
      .then(b => fetch('http://127.0.0.1:8765/' + name, {method: 'POST', body: b}))
      .then(r => r.text()).then(t => window.__exp.push(t)).catch(e => window.__exp.push('ERR ' + e));
  };
  const handle = (u) => {
    if (!u || !(/^blob:/.test(u) || /tripo-data|\.glb|\.fbx|\.zip/.test(u))) return false;
    const ext = (u.match(/\.(glb|fbx|zip)/) || [, 'glb'])[1];
    post(u, window.__expName.replace(/\.\w+$/, '.' + ext));
    return true;
  };
  const click = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () { if (handle(this.href)) return; return click.call(this); };
  const open = window.open;
  window.open = function (u, ...rest) { if (handle(String(u))) return null; return open.call(this, u, ...rest); };
}
'hooked'
