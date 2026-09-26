"""Build collect.html: an offline page for pasting assistant answers into.
It shows only the questions, never the key, so collection isn't biased."""
import json
from pathlib import Path

HERE = Path(__file__).parent
qs = [{"id": q["id"], "question": q["question"]}
      for q in map(json.loads, (HERE / "questions.jsonl").read_text().splitlines())]

html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RetireBench collection</title>
<style>
:root{--bg:#fff;--fg:#1a1a1a;--muted:#666;--line:#ddd;--accent:#0b5cad;--done:#1f7a3a}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#eee;--muted:#aaa;--line:#333;--accent:#6aa9f0;--done:#5cc27a}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:860px;margin:0 auto;padding:16px}
h1{font-size:22px;margin:0 0 4px}.muted{color:var(--muted);font-size:13px}
.bar{position:sticky;top:0;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line);display:flex;gap:8px;flex-wrap:wrap;align-items:center;z-index:1}
select,input,button,textarea{font:inherit;color:inherit;background:transparent;border:1px solid var(--line);border-radius:6px;padding:6px 8px}
button{cursor:pointer}button.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
.q{border:1px solid var(--line);border-radius:8px;padding:12px;margin:12px 0}.q.done{border-left:4px solid var(--done)}
.qtext{font-weight:600;margin:4px 0 8px}textarea{width:100%;box-sizing:border-box;min-height:90px}
.row{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:6px;font-size:13px}
</style></head><body>
<h1>RetireBench answer collection</h1>
<p class="muted">Protocol: for each question, open a <b>new chat</b> with memory and custom instructions off, paste the question exactly as written, copy the <b>first</b> answer word for word, no follow-ups, no regenerating. Progress saves in this browser. Export when done.</p>
<div class="bar">
 <label>Assistant <select id="asst"><option>chatgpt-free</option><option>gemini-free</option><option>claude-free</option></select></label>
 <input id="model" placeholder="Model label shown (e.g. GPT-5 mini)" size="26">
 <span id="count" class="muted"></span>
 <button class="primary" id="export">Export JSON</button>
</div>
<div id="list"></div>
<script>
const QS = __QS__;
const KEY = "retirebench-v1";
let store = {}; try { store = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {} };
const asst = document.getElementById("asst"), model = document.getElementById("model");
const cur = () => (store[asst.value] ||= {model: "", answers: {}});
function render() {
  const s = cur(); model.value = s.model || "";
  const list = document.getElementById("list"); list.innerHTML = "";
  QS.forEach(q => {
    const a = s.answers[q.id] || {text: "", searched: false, date: ""};
    const d = document.createElement("div"); d.className = "q" + (a.text.trim() ? " done" : "");
    d.innerHTML = `<div class="muted">${q.id}</div><div class="qtext"></div>
      <div class="row"><button data-copy>Copy question</button></div>
      <textarea placeholder="Paste the assistant's first answer here"></textarea>
      <div class="row"><label><input type="checkbox" data-s> It searched the web</label><span class="muted" data-d></span></div>`;
    d.querySelector(".qtext").textContent = q.question;
    const ta = d.querySelector("textarea"), cb = d.querySelector("[data-s]"), dd = d.querySelector("[data-d]");
    ta.value = a.text; cb.checked = a.searched; dd.textContent = a.date ? "saved " + a.date : "";
    d.querySelector("[data-copy]").onclick = e => { navigator.clipboard.writeText(q.question); e.target.textContent = "Copied"; setTimeout(() => e.target.textContent = "Copy question", 1200); };
    const upd = () => { const date = new Date().toISOString().slice(0, 10);
      s.answers[q.id] = {text: ta.value, searched: cb.checked, date}; dd.textContent = "saved " + date;
      d.classList.toggle("done", !!ta.value.trim()); save(); count(); };
    ta.oninput = upd; cb.onchange = upd; list.appendChild(d);
  });
  count();
}
function count() { const n = Object.values(cur().answers).filter(a => a.text.trim()).length;
  document.getElementById("count").textContent = `${n}/${QS.length} answered`; }
asst.onchange = render; model.oninput = () => { cur().model = model.value; save(); };
document.getElementById("export").onclick = () => {
  const blob = new Blob([JSON.stringify({bench: KEY, collected: store}, null, 2)], {type: "application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "retirebench-answers.json"; a.click();
};
render();
</script></body></html>
"""
(HERE / "collect.html").write_text(html.replace("__QS__", json.dumps(qs)))
print("wrote collect.html with", len(qs), "questions")
