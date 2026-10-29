"use strict";
let report=window.RAIDS_REPORT;
let sortKey=null,sortDirection=1,activeSessionId=null,page=0;
const $=(selector,parent=document)=>parent.querySelector(selector);
const $$=(selector,parent=document)=>[...parent.querySelectorAll(selector)];
const categoryNames={story:"故事",adventure:"探索",figure:"人物",guess:"猜谜",learn:"学习",assistant:"助手",translate:"翻译"};
const states={queued:"待测试",running:"采集中",collected:"待评分",incomplete:"未完成",scored:"已评分",blocked:"受阻",untested:"未测试"};
const order=["story","adventure","figure","guess","learn","sushi"];
const selectControls=new Map();
let openSelect=null;
function el(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined&&text!==null)node.textContent=String(text);return node;}
function action(label,callback,className="text-button"){const node=el("button",className,label);node.type="button";node.addEventListener("click",callback);return node;}
function cell(row,text,className=""){const node=el("td",className,text);row.append(node);return node;}
function time(value){return new Intl.DateTimeFormat("zh-CN",{timeZone:"Asia/Singapore",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}).format(new Date(value));}
function scored(session){return session.rows.filter(row=>row.score).length;}
function language(value){return value==="zh"?"中文":value==="en"?"English":value==="mixed"?"混合":"—";}
function technical(session){const checks=session?.technical||[];if(checks.some(c=>c.status==="fail"))return ["未通过","failure"];if(checks.length&&checks.every(c=>c.status==="pass"))return ["通过","success"];return ["待完成","pending"];}
function records(){const result=[];for(const item of report.catalog){const sessions=report.sessions.filter(s=>s.catalog_id===item.id);if(sessions.length){for(const session of sessions)result.push({catalog:item,session,title:item.title,category:item.category,language:session.language,status:session.status,collected:session.rows.length,scored:scored(session),mean:session.official?session.summary.mean:null,minimum:session.official?session.summary.minimum:null});}else result.push({catalog:item,session:null,title:item.title,category:item.category,language:"none",status:"untested",collected:null,scored:null,mean:null,minimum:null});}return result;}
function enhanceSelects(){
  for(const native of $$("select")){
    if(selectControls.has(native)){selectControls.get(native).sync();continue;}
    const label=$('label[for="'+native.id+'"]');
    const control=el("div","select-control");
    control.dataset.select=native.id;
    native.before(control);control.append(native);native.classList.add("select-native");
    const trigger=el("button","select-trigger");
    trigger.type="button";trigger.id=native.id+"-trigger";
    trigger.setAttribute("role","combobox");
    trigger.setAttribute("aria-haspopup","listbox");
    trigger.setAttribute("aria-expanded","false");
    trigger.setAttribute("aria-controls",native.id+"-options");
    if(label){label.htmlFor=trigger.id;trigger.setAttribute("aria-labelledby",label.id);}
    const value=el("span");trigger.append(value);
    const menu=el("div","select-menu");
    menu.id=native.id+"-options";menu.hidden=true;menu.setAttribute("role","listbox");
    if(label)menu.setAttribute("aria-labelledby",label.id);
    control.append(trigger,menu);
    const options=[...native.options];
    let cursor=native.selectedIndex,typed="",typedAt=0;
    function activate(index,scroll=true){
      cursor=(index+options.length)%options.length;
      [...menu.children].forEach((option,i)=>option.classList.toggle("is-active",i===cursor));
      trigger.setAttribute("aria-activedescendant",menu.children[cursor].id);
      if(scroll)menu.children[cursor].scrollIntoView({block:"nearest"});
    }
    function sync(){
      value.textContent=options[native.selectedIndex]?.textContent||"";
      [...menu.children].forEach((option,i)=>option.setAttribute("aria-selected",String(i===native.selectedIndex)));
      if(menu.hidden)cursor=native.selectedIndex;
    }
    const controller={
      sync,
      close(focus=false){
        menu.hidden=true;trigger.setAttribute("aria-expanded","false");
        trigger.removeAttribute("aria-activedescendant");
        if(openSelect===controller)openSelect=null;
        if(focus)trigger.focus({preventScroll:true});
      },
      contains(target){return control.contains(target);}
    };
    function show(){
      if(openSelect&&openSelect!==controller)openSelect.close();
      const rect=trigger.getBoundingClientRect();
      const below=document.documentElement.clientHeight-rect.bottom-14,above=rect.top-14;
      const upwards=below<Math.min(200,options.length*34+12)&&above>below;
      control.classList.toggle("opens-up",upwards);
      menu.style.maxHeight=Math.max(72,Math.min(280,upwards?above:below))+"px";
      menu.hidden=false;trigger.setAttribute("aria-expanded","true");
      openSelect=controller;activate(native.selectedIndex);trigger.focus({preventScroll:true});
    }
    function choose(index){
      native.value=options[index].value;
      native.dispatchEvent(new Event("change",{bubbles:true}));
      controller.close(true);
    }
    options.forEach((option,index)=>{
      const item=el("div","select-option",option.textContent);
      item.id=native.id+"-option-"+index;item.setAttribute("role","option");
      item.addEventListener("pointerdown",event=>event.preventDefault());
      item.addEventListener("pointermove",()=>activate(index,false));
      item.addEventListener("click",()=>choose(index));
      menu.append(item);
    });
    trigger.addEventListener("click",()=>menu.hidden?show():controller.close());
    trigger.addEventListener("keydown",event=>{
      if(["ArrowDown","ArrowUp","Home","End","Enter"," ","Escape"].includes(event.key)){
        if(event.key==="Escape"){
          if(!menu.hidden){event.preventDefault();event.stopPropagation();controller.close(true);}
          return;
        }
        event.preventDefault();
        if(event.key==="Enter"||event.key===" "){if(menu.hidden)show();else choose(cursor);return;}
        const wasClosed=menu.hidden;if(wasClosed)show();
        if(event.key==="Home")activate(0);
        else if(event.key==="End")activate(options.length-1);
        else if(!wasClosed)activate(cursor+(event.key==="ArrowDown"?1:-1));
      }else if(event.key==="Tab"){controller.close();}
      else if(event.key.length===1&&!event.metaKey&&!event.ctrlKey&&!event.altKey){
        event.preventDefault();if(menu.hidden)show();
        const now=Date.now();typed=(now-typedAt<700?typed:"")+event.key.toLocaleLowerCase();typedAt=now;
        let index=options.findIndex(option=>option.textContent.toLocaleLowerCase().startsWith(typed));
        if(index<0){typed=event.key.toLocaleLowerCase();index=options.findIndex(option=>option.textContent.toLocaleLowerCase().startsWith(typed));}
        if(index>=0)activate(index);
      }
    });
    native.addEventListener("change",sync);
    selectControls.set(native,controller);sync();
  }
}
document.addEventListener("pointerdown",event=>{if(openSelect&&!openSelect.contains(event.target))openSelect.close();});
document.addEventListener("scroll",event=>{if(openSelect&&!openSelect.contains(event.target))openSelect.close();},true);
window.addEventListener("resize",()=>openSelect?.close());
function render(){if(!report){$("#load-error").hidden=false;return;}$("#load-error").hidden=true;const replies=report.sessions.reduce((n,s)=>n+s.rows.length,0),ratings=report.sessions.reduce((n,s)=>n+scored(s),0),official=report.sessions.filter(s=>s.official).length;$("#metadata").textContent="更新 "+time(report.updated_at)+" UTC+8 · GizClaw "+report.runtime+" · "+report.catalog.length+" 个剧本 · 本轮 "+report.sessions.length+" 场 · 回复 "+replies+"/624 · 已评分 "+ratings+"/624 · 正式成绩 "+official+"/12";if($("#category").options.length===1){for(const [key,title]of Object.entries(categoryNames)){const option=el("option","",title);option.value=key;$("#category").append(option);}}enhanceSelects();renderTable();renderHistory();if(activeSessionId)renderSession();}
function renderTable(){const query=$("#search").value.trim().toLocaleLowerCase(),category=$("#category").value,lang=$("#language").value,scope=$("#scope").value;let rows=records().filter(r=>(category==="all"||r.category===category)&&(lang==="all"||r.language===lang)&&(scope==="all"||(scope==="current"?r.session:!r.session))&&[r.title,r.catalog.title_en,r.catalog.id].join(" ").toLocaleLowerCase().includes(query));rows.sort((a,b)=>{if(sortKey){const x=a[sortKey],y=b[sortKey];if(x===null&&y!==null)return 1;if(y===null&&x!==null)return -1;const value=typeof x==="number"?x-y:String(x??"").localeCompare(String(y??""),"zh-CN");return value*sortDirection;}if(Boolean(a.session)!==Boolean(b.session))return a.session?-1:1;if(a.session&&b.session)return order.indexOf(a.session.case)-order.indexOf(b.session.case)||a.language.localeCompare(b.language)*-1;return a.title.localeCompare(b.title,"zh-CN");});const target=$("#report-rows");target.replaceChildren();for(const record of rows){const s=record.session,row=el("tr");const name=cell(row);if(s)name.append(action(record.title,()=>openSession(s.id),"text-button name-button"));else name.textContent=record.title;name.title=record.catalog.title_en+" · "+record.catalog.id;if(s?.case==="sushi")name.append(el("span","baseline","基线"));cell(row,categoryNames[record.category]);cell(row,language(record.language));cell(row,states[record.status]||record.status,"status "+(record.status==="incomplete"||record.status==="blocked"?"failure":record.status==="untested"?"muted":""));cell(row,s?record.collected+"/52":"—","num");cell(row,s?record.scored+"/52":"—","num");cell(row,record.mean===null?"—":record.mean.toFixed(1),"num");cell(row,record.minimum===null?"—":record.minimum.toFixed(0),"num");for(const line of [80,85,90]){const gate=s?.official?s.summary.thresholds[String(line)]:null;const td=cell(row,gate?(gate.pass?"通过":"未通过"):"—","line "+(gate?(gate.pass?"success":"failure"):"muted"));if(gate)td.title=gate.count+"/52 条达线";}const tech=s?technical(s):["—","muted"];const techCell=cell(row,tech[0],tech[1]);if(s)techCell.title=s.technical.map(c=>c.label).join("\n");const detail=cell(row);if(s)detail.append(action("日志",()=>openSession(s.id)));else detail.textContent="—";target.append(row);}if(!rows.length){const row=el("tr"),td=cell(row,"无匹配记录","no-results");td.colSpan=13;target.append(row);}$("#row-count").textContent=rows.length+" 条记录 / "+new Set(rows.map(r=>r.catalog.id)).size+" 个剧本";$$('[data-sort]').forEach(th=>th.setAttribute("aria-sort",th.dataset.sort===sortKey?(sortDirection===1?"ascending":"descending"):"none"));}
function renderHistory(){const target=$("#history-rows");target.replaceChildren();$("#history-title").textContent="历史记录（"+report.archives.length+"）";for(const s of report.archives){const row=el("tr");cell(row,s.title);cell(row,language(s.language));cell(row,s.rows.length,"num");cell(row,scored(s),"num");cell(row,"样本不足","muted");cell(row).append(action("日志",()=>openSession(s.id)));target.append(row);}}
function getSession(){return [...report.sessions,...report.archives].find(s=>s.id===activeSessionId);}
function openSession(id){activeSessionId=id;page=0;$("#turn-search").value="";$("#turn-sort").value="round";$("#deductions-only").checked=false;renderSession();const dialog=$("#report-dialog");if(!dialog.open)dialog.showModal();dialog.scrollTop=0;}
function renderSession(){const session=getSession();if(!session)return;$("#dialog-title").textContent=session.title+" / "+language(session.language);$("#session-meta").textContent="回复 "+session.rows.length+"/52 · 已评分 "+scored(session)+"/52 · "+(session.official?"均分 "+session.summary.mean.toFixed(1):session.historical?"历史记录，样本不足":"正式成绩未形成")+" · GizClaw "+(session.runtime||report.runtime)+" · SHA256 "+session.candidate_sha256;const target=$("#technical-rows");target.replaceChildren();for(const check of session.technical||[]){const row=el("tr");cell(row,check.label);cell(row,check.status==="pass"?"通过":check.status==="fail"?"未通过":"待完成",check.status==="pass"?"success":check.status==="fail"?"failure":"pending");target.append(row);}enhanceSelects();renderTurns();}
function renderTurns(){const session=getSession();if(!session)return;const q=$("#turn-search").value.trim().toLocaleLowerCase(),only=$("#deductions-only").checked;const rows=session.rows.filter(r=>(!only||(r.score&&r.score.total<100))&&[r.intended,r.reply,r.score?.why||""].join(" ").toLocaleLowerCase().includes(q));if($("#turn-sort").value==="score")rows.sort((a,b)=>(a.score?.total??101)-(b.score?.total??101)||a.round-b.round);const size=$("#page-size").value==="all"?Math.max(1,rows.length):Number($("#page-size").value),pages=Math.max(1,Math.ceil(rows.length/size));page=Math.min(page,pages-1);const visible=rows.slice(page*size,(page+1)*size),target=$("#turn-rows");target.replaceChildren();for(const r of visible){const row=el("tr");cell(row,r.round===0?"开场":r.round);const user=cell(row,r.intended);if(r.heard&&r.heard!==r.intended){const detail=el("details");detail.append(el("summary","","ASR 转写"),document.createTextNode(r.heard));user.append(detail);}cell(row,r.reply);const score=cell(row);if(r.score){score.append(el("strong","score-total"+(r.score.total<80?" failure":""),r.score.total));const ratings=el("dl","rating-values");["回应","连贯","事实","互动","角色"].forEach((name,index)=>ratings.append(el("dt","",name),el("dd","",r.score.ratings[index]+"/5")));score.append(ratings);}else score.textContent="待评分";cell(row,r.score?.why||"—");target.append(row);}if(!visible.length){const row=el("tr"),td=cell(row,session.rows.length?"无匹配记录":"尚无日志","no-results");td.colSpan=5;target.append(row);}$("#turn-count").textContent=rows.length+" 条 · 第 "+(page+1)+"/"+pages+" 页";$("#previous-page").disabled=page===0;$("#next-page").disabled=page>=pages-1;}
for(const selector of ["#search","#category","#language","#scope"])$(selector).addEventListener(selector==="#search"?"input":"change",renderTable);
$$('[data-sort]').forEach(th=>$("button",th).addEventListener("click",()=>{if(sortKey===th.dataset.sort)sortDirection*=-1;else{sortKey=th.dataset.sort;sortDirection=1;}renderTable();}));
for(const selector of ["#turn-search","#turn-sort","#deductions-only","#page-size"])$(selector).addEventListener(selector==="#turn-search"?"input":"change",()=>{page=0;renderTurns();});
$("#previous-page").addEventListener("click",()=>{page--;renderTurns();});$("#next-page").addEventListener("click",()=>{page++;renderTurns();});
$("#close-dialog").addEventListener("click",()=>$("#report-dialog").close());$("#report-dialog").addEventListener("close",()=>{activeSessionId=null;});
for(const selector of ["#filters","#turn-filters"])$(selector).addEventListener("submit",event=>event.preventDefault());
render();
async function refresh(){try{const response=await fetch("report.json?updated="+Math.floor(Date.now()/60000),{cache:"no-store"});if(!response.ok)return;const next=await response.json();if(next.schema==="raids-public-report/v1"&&next.updated_at!==report?.updated_at){report=next;render();}}catch(_){}}
refresh();setInterval(refresh,60000);
