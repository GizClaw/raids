"use strict";
let report=window.RAIDS_REPORT;
let sortKey=null,sortDirection=1;
const $=(selector,parent=document)=>parent.querySelector(selector);
const $$=(selector,parent=document)=>[...parent.querySelectorAll(selector)];
const categoryNames={story:"故事",adventure:"探索",figure:"人物",guess:"猜谜",learn:"学习",assistant:"助手",translate:"翻译"};
const states={queued:"待测试",running:"测试中",collected:"待评分",incomplete:"已中断",scored:"已评分",blocked:"受阻",untested:"未测试"};
const order=["story","adventure","figure","guess","learn","sushi"];
const selectControls=new Map();
let openSelect=null;
function el(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined&&text!==null)node.textContent=String(text);return node;}
function cell(row,text,className=""){const node=el("td",className,text);row.append(node);return node;}
function time(value){return new Intl.DateTimeFormat("zh-CN",{timeZone:"Asia/Singapore",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}).format(new Date(value));}
function turns(session){return session.rows.filter(row=>row.round>0).length;}
function scored(session){return session.rows.filter(row=>row.score).length;}
function language(value){return value==="zh"?"中文":value==="en"?"English":value==="mixed"?"混合":"—";}
function records(){const result=[];for(const item of report.catalog){const sessions=report.sessions.filter(s=>s.catalog_id===item.id);if(sessions.length){for(const session of sessions)result.push({catalog:item,session,title:item.title,category:item.category,language:session.language,status:session.status,collected:turns(session),scored:scored(session),mean:session.summary?.mean??null,minimum:session.summary?.minimum??null,maximum:session.summary?.maximum??null,stddev:session.summary?.stddev??null});}else result.push({catalog:item,session:null,title:item.title,category:item.category,language:"none",status:"untested",collected:null,scored:null,mean:null,minimum:null,maximum:null,stddev:null});}return result;}
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
function render(){
  if(!report){$("#load-error").hidden=false;return;}
  $("#load-error").hidden=true;
  $("#metadata").textContent="更新 "+time(report.updated_at)+" UTC+8 · GizClaw "+report.runtime+" · "+report.catalog.length+" 个剧本 · 本次 "+report.sessions.length+" 场独立测试 · 每场 51 轮问答";
  if($("#category").options.length===1){for(const [key,title]of Object.entries(categoryNames)){const option=el("option","",title);option.value=key;$("#category").append(option);}}
  enhanceSelects();renderTable();renderHistory();
}
function renderTable(){
  const query=$("#search").value.trim().toLocaleLowerCase(),category=$("#category").value,lang=$("#language").value,scope=$("#scope").value;
  const rows=records().filter(r=>(category==="all"||r.category===category)&&(lang==="all"||r.language===lang)&&(scope==="all"||(scope==="current"?r.session:!r.session))&&[r.title,r.catalog.title_en,r.catalog.id].join(" ").toLocaleLowerCase().includes(query));
  rows.sort((a,b)=>{
    if(sortKey){const x=a[sortKey],y=b[sortKey];if(x===null&&y!==null)return 1;if(y===null&&x!==null)return -1;return (typeof x==="number"?x-y:String(x??"").localeCompare(String(y??""),"zh-CN"))*sortDirection;}
    if(Boolean(a.session)!==Boolean(b.session))return a.session?-1:1;
    if(a.session&&b.session)return order.indexOf(a.session.case)-order.indexOf(b.session.case)||a.language.localeCompare(b.language)*-1;
    return a.title.localeCompare(b.title,"zh-CN");
  });
  const target=$("#report-rows");target.replaceChildren();
  for(const record of rows){
    const s=record.session,row=el("tr"),name=cell(row);
    if(s?.rows.length&&s.logs)name.append(logLink(s,record.title,"text-button name-button"));else name.textContent=record.title;
    name.title=record.catalog.title_en+" · "+record.catalog.id;
    if(s?.case==="sushi")name.append(el("span","baseline","基线"));
    cell(row,categoryNames[record.category]);cell(row,language(record.language));const statusCell=cell(row,states[record.status]||record.status,"status");if(s?.interruption)statusCell.title=s.interruption;
    cell(row,s?record.collected+"/51":"—","num");cell(row,s?record.scored+"/"+s.rows.length:"—","num");
    for(const key of ["minimum","maximum","mean","stddev"])cell(row,record[key]===null?"—":record[key].toFixed(key==="stddev"?2:1),"num");
    const detail=cell(row);if(s?.rows.length&&s.logs)detail.append(logLink(s));else detail.textContent="—";
    target.append(row);
  }
  if(!rows.length){const row=el("tr"),td=cell(row,"无匹配记录","no-results");td.colSpan=11;target.append(row);}
  $("#row-count").textContent=rows.length+" 条记录 / "+new Set(rows.map(r=>r.catalog.id)).size+" 个剧本";
  $$('[data-sort]').forEach(th=>th.setAttribute("aria-sort",th.dataset.sort===sortKey?(sortDirection===1?"ascending":"descending"):"none"));
}
function logLink(session,label="日志",className="text-button"){
  const link=el("a",className,label);link.href=session.logs.html+"?v="+encodeURIComponent(report.updated_at);link.target="_blank";link.rel="noopener";return link;
}
function renderHistory(){
  const target=$("#history-rows");target.replaceChildren();$("#history-title").textContent="历史记录（"+report.archives.length+"）";
  for(const s of report.archives){
    const row=el("tr");cell(row,s.title);cell(row,language(s.language));cell(row,turns(s)+"/51","num");cell(row,scored(s)+"/"+s.rows.length,"num");
    for(const key of ["minimum","maximum","mean","stddev"]){const value=s.summary?.[key];cell(row,value===null||value===undefined?"—":value.toFixed(key==="stddev"?2:1),"num");}
    cell(row).append(logLink(s));target.append(row);
  }
}
for(const selector of ["#search","#category","#language","#scope"])$(selector).addEventListener(selector==="#search"?"input":"change",renderTable);
$$('[data-sort]').forEach(th=>$("button",th).addEventListener("click",()=>{if(sortKey===th.dataset.sort)sortDirection*=-1;else{sortKey=th.dataset.sort;sortDirection=1;}renderTable();}));
$("#filters").addEventListener("submit",event=>event.preventDefault());
render();
async function refresh(){try{const response=await fetch("report.json?updated="+Math.floor(Date.now()/60000),{cache:"no-store"});if(!response.ok)return;const next=await response.json();if(next.schema==="raids-public-report/v1"&&next.updated_at!==report?.updated_at){report=next;render();}}catch(_){}}
refresh();setInterval(refresh,60000);
