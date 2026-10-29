/* Only allowlisted public dialogue is shipped. Never render log text as HTML. */
"use strict";
let report = window.RAIDS_REPORT;
let languageFilter = "all";
const $ = (selector, parent = document) => parent.querySelector(selector);
const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];
const categoryNames = {story:"故事",adventure:"探索",figure:"人物",guess:"猜谜",learn:"学习",assistant:"助手",translate:"翻译"};
const categoryEnglish = {story:"STORY",adventure:"ADVENTURE",figure:"BIOGRAPHY",guess:"GUESS",learn:"LEARNING",assistant:"ASSISTANT",translate:"TRANSLATE"};
const stateNames = {queued:"待测试",running:"采集中",collected:"待日志评分",incomplete:"采集未完成",scored:"已评分",blocked:"受阻"};
const dimensions = ["回应与推进","连贯与规则","事实与逻辑","互动表达","角色与语言"];
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}
function button(label, action, className = "session-open") {
  const node = el("button", className, label);
  node.type = "button";
  node.addEventListener("click", action);
  return node;
}
function prettyDate(value) {
  return new Intl.DateTimeFormat("zh-CN", {timeZone:"Asia/Singapore",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}).format(new Date(value));
}
function render() {
  if (!report) { $("#load-error").hidden = false; return; }
  const sessions = report.sessions;
  const count = sessions.reduce((a,s) => a + s.rows.length, 0);
  $("#replies-count").textContent = count;
  $("#complete-count").replaceChildren(document.createTextNode(String(sessions.filter(s => s.complete).length).padStart(2,"0")),el("small", "", " / 12 场"));
  $("#graded-count").replaceChildren(document.createTextNode(String(sessions.filter(s => s.official).length).padStart(2,"0")),el("small", "", " / 12 场"));
  $("#batch-state").textContent = sessions.some(s => s.status === "running") ? "正在采集" : count ? "结果更新中" : "准备就绪";
  $("#nav-count").textContent = report.catalog.length;
  $("#catalog-count").textContent = report.catalog.length;
  $("#updated-at").textContent = "数据更新 " + prettyDate(report.updated_at) + " · UTC+8";
  const grid = $("#coverage-grid"); grid.replaceChildren();
  for (const s of sessions) for (let i = 0; i < 52; i++) {
    const dot = el("i", s.rows[i]?.score ? "scored" : s.rows[i] ? "collected" : "");
    dot.title = s.title + " / " + (s.language === "zh" ? "中文" : "English") + " / " + (i === 0 ? "开场" : "第 " + i + " 轮");
    grid.append(dot);
  }
  renderSamples();
  renderCatalog();
  renderRubric();
  renderArchive();
}
function renderSamples() {
  const container = $("#sample-grid"); container.replaceChildren();
  const order = ["story","adventure","figure","guess","learn","sushi"];
  order.forEach((key,index) => {
    const sample = report.samples.find(s => s.key === key);
    if (!sample) return;
    const catalog = report.catalog.find(c => c.id === sample.catalog_id);
    const card = $("#sample-template").content.firstElementChild.cloneNode(true);
    $(".case-index",card).textContent = "0" + (index + 1) + " / 06";
    $(".case-category",card).textContent = categoryEnglish[sample.category];
    $("h3",card).textContent = sample.title;
    $(".case-english",card).textContent = catalog.title_en;
    $(".case-description",card).textContent = catalog.summary;
    $(".case-source",card).textContent = "SHA256 " + sample.source_sha256.slice(0,12);
    $(".case-baseline",card).textContent = key === "sushi" ? "未优化基线" : "当前候选";
    report.sessions.filter(s => s.case === key && (languageFilter === "all" || s.language === languageFilter)).forEach(s => {
      const row = el("div","session-row");
      row.append(el("span","language-key",s.language === "zh" ? "中" : "EN"));
      const progress = el("div","session-progress");
      progress.append(el("b","",s.official ? s.summary.mean.toFixed(1) + " 分" : s.rows.length + " / 52"));
      progress.append(el("span","",stateNames[s.status] || "待测试"));
      const track = el("div","mini-track"), fill = el("i");
      fill.style.width = Math.min(100,s.rows.length / 52 * 100) + "%";
      track.append(fill); progress.append(track);
      row.append(progress,button(s.rows.length ? "看实录 ↗" : "查看计划 ↗",() => openSession(s)));
      $(".session-list",card).append(row);
    });
    container.append(card);
  });
}
function renderCatalog() {
  const select = $("#category-filter");
  if (select.options.length === 1) {
    Object.entries(categoryNames).forEach(([key,name]) => { const option = el("option","",name); option.value = key; select.append(option); });
  }
  const query = $("#catalog-search").value.trim().toLocaleLowerCase();
  const category = select.value, scope = $("#scope-filter").value;
  const list = report.catalog.filter(c => (category === "all" || c.category === category)
    && (scope === "all" || (scope === "current" ? c.current : !c.current))
    && [c.title,c.title_en,c.summary,...c.tags].join(" ").toLocaleLowerCase().includes(query));
  const target = $("#catalog-list"); target.replaceChildren();
  list.forEach(c => {
    const row = el("article","catalog-item");
    row.append(el("span","catalog-icon",c.title.slice(0,1)));
    const body = el("div"); body.append(el("h3","",c.title),el("p","",categoryNames[c.category] + " · " + c.title_en)); row.append(body);
    if (c.current) {
      row.append(button("本轮样本 ↗",() => {
        const session = report.sessions.find(s => s.catalog_id === c.id && s.language === "zh");
        if (session) openSession(session);
      },"session-open"));
    } else row.append(el("span","pill","未测试"));
    target.append(row);
  });
  $("#catalog-result-count").textContent = list.length + " / " + report.catalog.length;
  $("#catalog-empty").hidden = list.length > 0;
}
function renderRubric() {
  const descriptions = ["回答本轮实际问题、执行已选行动或合理澄清，让故事或学习继续。","持物、体型、时间、谜底、关卡、重连与更正，与已发生的内容一致。","避免实质误导，区分创作、推测、实际观察与已查证结论。","表达自然清楚、符合受众；简短而正确的回答也可以满分。","遵守固定角色、旁白职责与用户指定语言，保持沉浸感。"];
  const rows = $("#rubric-rows"); rows.replaceChildren();
  [25,25,25,15,10].forEach((weight,i) => {
    const row = el("article","rubric-row"); row.append(el("strong","",weight),el("h2","",dimensions[i]),el("p","",descriptions[i])); rows.append(row);
  });
}
function renderArchive() {
  const target = $("#archive-list"); target.replaceChildren();
  if (!report.archives.length) { target.append(el("p","empty","尚无历史记录。")); return; }
  report.archives.forEach(s => {
    const card = el("article","archive-card"), body = el("div");
    body.append(el("p","eyebrow","HISTORICAL / INSUFFICIENT COVERAGE"),el("h2","",s.title),
      el("p","",s.note),el("span","pill",s.rows.length + " 条历史回复 · 无正式长测分"));
    card.append(body,button("打开完整实录 ↗",() => openSession(s)));
    target.append(card);
  });
}
function openSession(session) {
  const target = $("#dialog-content"); target.replaceChildren();
  target.append(el("h2","",session.title + " / " + (session.language === "mixed" ? "历史观察" : session.language === "zh" ? "中文" : "English")));
  $("h2",target).id = "dialog-title";
  target.append(el("p","detail-meta",session.note || "独立新会话 · 开场 + 51 轮用户对话 · 目标 52 条主持回复"));
  target.append(el("p","detail-meta","候选 SHA256 " + session.candidate_sha256 + " · GizClaw " + (session.runtime || report.runtime)));
  const stats = el("div","detail-stats");
  [["已收齐",session.rows.length + " / " + (session.historical ? "52" : session.expected)],
    ["已评分",session.rows.filter(r=>r.score).length + " 条"],
    ["正式成绩",session.official ? session.summary.mean.toFixed(1) + " 分" : "尚未形成"]].forEach(([label,value]) => {
      const stat = el("div"); stat.append(el("strong","",value),el("span","",label)); stats.append(stat);
    });
  target.append(stats);
  if (!session.official) target.append(el("p","notice",session.historical ? "这是一段历史短测，覆盖不足，不计入本轮 51 轮长测，也不公布正式剧本成绩。" : "尚未完整收齐 52 条并完成逐轮评分。当前进度和逐条观察不代表通过。"));
  const tech = el("div","detail-tech");
  (session.technical || []).forEach(t => tech.append(el("span","pill" + (t.status === "fail" ? " tech-warning" : ""),t.label)));
  target.append(tech);
  if (session.official) {
    const lines = el("div","thresholds");
    Object.entries(session.summary.thresholds).forEach(([line,result]) => lines.append(el("span","",line + " 分线：" + (result.pass ? "通过" : "未通过") + " · " + result.count + "/52 达线")));
    target.append(lines);
  }
  target.append(el("h3","detail-subhead","逐轮对话与评分"));
  if (!session.rows.length) {
    target.append(el("div","no-turns","此场尚无对话日志。采集后在这里逐轮显示用户原话、完整回复与评分理由。"));
  } else {
    const filters = el("div","round-filter");
    const search = el("input"); search.type = "search"; search.placeholder = "搜索用户原话、回复或扣分理由"; search.setAttribute("aria-label","搜索逐轮日志");
    const select = el("select"); select.setAttribute("aria-label","对话排序");
    [["round","按对话顺序"],["score","分数从低到高"]].forEach(([v,label])=>{const option=el("option","",label);option.value=v;select.append(option);});
    filters.append(search,select); target.append(filters);
    const list = el("div"); target.append(list);
    const draw = () => {
      list.replaceChildren(); const q = search.value.trim().toLowerCase();
      const rows = session.rows.filter(r => [r.intended,r.reply,r.score?.why || ""].join(" ").toLowerCase().includes(q));
      if (select.value === "score") rows.sort((a,b) => (a.score?.total ?? 101) - (b.score?.total ?? 101) || a.round - b.round);
      rows.forEach(r => list.append(turnElement(r)));
      if (!rows.length) list.append(el("p","empty","没有匹配的对话。"));
    };
    search.addEventListener("input",draw); select.addEventListener("change",draw); draw();
  }
  const dialog = $("#report-dialog");
  if (!dialog.open) dialog.showModal();
  dialog.scrollTop = 0;
}
function turnElement(row) {
  const details = el("details","turn"), summary = el("summary");
  const title = el("span"); title.append(el("b","",row.round === 0 ? "开场" : String(row.round).padStart(2,"0")),document.createTextNode(row.intended));
  summary.append(title,el("span",row.score ? "turn-score" + (row.score.total < 80 ? " low" : "") : "pill",row.score ? row.score.total : "待日志评分"));
  details.append(summary,el("p","turn-label","用户原话 · 实际合成输入"),el("p","turn-text",row.intended),
    el("p","turn-label","主持完整回复"),el("p","turn-text host-text",row.reply));
  if (row.score) {
    const ratings = el("div","score-dimensions");
    row.score.ratings.forEach((rating,i) => { const cell=el("span","",dimensions[i]);cell.append(el("b","",rating + "/5"));ratings.append(cell); });
    const why = el("div","deduction"); why.append(el("b","","日志评分依据"),document.createTextNode(row.score.why));
    details.append(ratings,why);
  }
  if (row.heard && row.heard !== row.intended) {
    const transcript = el("details");
    transcript.append(el("summary","detail-meta","查看 ASR 转写（语音诊断，不代替用户原话）"),el("p","turn-text",row.heard));details.append(transcript);
  }
  return details;
}
function showTab(name) {
  const key = ["overview","catalog","rubric","archive"].includes(name) ? name : "overview";
  $$(".tab-panel").forEach(node=>node.hidden = node.id !== key);
  $$("[data-tab]").forEach(node=>node.getAttribute("data-tab") === key ? node.setAttribute("aria-current","page") : node.removeAttribute("aria-current"));
}
$$("[data-language]").forEach(node=>node.addEventListener("click",()=>{
  languageFilter=node.dataset.language;$$("[data-language]").forEach(n=>n.setAttribute("aria-pressed",String(n===node)));renderSamples();
}));
["#catalog-search","#category-filter","#scope-filter"].forEach(selector=>$(selector).addEventListener(selector.includes("search") ? "input" : "change",renderCatalog));
$("#close-dialog").addEventListener("click",()=>$("#report-dialog").close());
$("#report-dialog").addEventListener("click",event=>{if(event.target===$("#report-dialog")){const box=event.target.getBoundingClientRect();if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)event.target.close();}});
window.addEventListener("hashchange",()=>showTab(location.hash.slice(1)));
showTab(location.hash.slice(1)); render();
async function refreshReport() {
  try { const response=await fetch("report.json?updated="+Math.floor(Date.now()/60000),{cache:"no-store"});if(!response.ok)return;const next=await response.json();if(next.schema==="raids-public-report/v1"&&next.updated_at!==report?.updated_at){report=next;render();} } catch (_) { /* Keep the last readable report while offline. */ }
}
refreshReport();
setInterval(refreshReport,60000);
