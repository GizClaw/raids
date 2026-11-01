"use strict";
let report=window.RAIDS_REPORT;
let sortKey=null,sortDirection=1;
const $=(selector,parent=document)=>parent.querySelector(selector);
const $$=(selector,parent=document)=>[...parent.querySelectorAll(selector)];
const categoryNames={story:"故事",adventure:"探索",figure:"人物",guess:"猜谜",learn:"学习",assistant:"助手",translate:"翻译"};
const cohortNames={optimized:"有专项改动",control:"未专项改动"};
const states={queued:"待测试",running:"测试中",collected:"待评分","pending-review":"已评待核",incomplete:"已中断",scored:"已评分",blocked:"受阻",untested:"未测试"};
const order=["figure","story","guess","adventure","learn","sushi"];
const selectControls=new Map();
let openSelect=null;
function el(tag,className,text){const node=document.createElement(tag);if(className)node.className=className;if(text!==undefined&&text!==null)node.textContent=String(text);return node;}
function cell(row,text,className=""){const node=el("td",className,text);row.append(node);return node;}
function time(value){return new Intl.DateTimeFormat("zh-CN",{timeZone:"Asia/Singapore",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}).format(new Date(value));}
function turns(session){return session.rows.filter(row=>row.round>0).length;}
function scored(session){return session.rows.filter(row=>row.score).length;}
function language(value){return value==="zh"?"中文":value==="en"?"English":value==="mixed"?"混合":"—";}
function records(){const result=[];for(const item of report.catalog){const sessions=report.sessions.filter(s=>s.catalog_id===item.id);if(sessions.length){for(const session of sessions){const impacts=session.summary?.impact_counts;result.push({catalog:item,session,title:item.title,cohort:session.cohort??null,category:item.category,language:session.language,status:session.status,collected:turns(session),scored:scored(session),mean:session.summary?.mean??null,minimum:session.summary?.minimum??null,maximum:session.summary?.maximum??null,stddev:session.summary?.stddev??null,coreIssues:impacts?(impacts.core+impacts.missed+impacts.unusable):null});}}else result.push({catalog:item,session:null,title:item.title,cohort:null,category:item.category,language:"none",status:"untested",collected:null,scored:null,mean:null,minimum:null,maximum:null,stddev:null,coreIssues:null});}return result;}
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
  const version=report.scoring?.versions?.includes("reply-score-v3.0")?" · v3 按实际影响评分":report.scoring?.versions?.includes("reply-score-v2.0")?" · v2 日志重评":" · 原评分口径";
  const retained=report.sessions.reduce((n,s)=>n+s.rows.length,0),rated=report.sessions.reduce((n,s)=>n+scored(s),0);
  $("#metadata").textContent="更新 "+time(report.updated_at)+" UTC+8 · GizClaw "+report.runtime+" · "+report.catalog.length+" 个剧本 · 本轮计划 "+report.sessions.length+" 场 · 已记录 "+retained+" / 已评分 "+rated+" 条 · 目标每场 51 轮问答"+version;
  const collectionNotice=$("#collection-notice");
  collectionNotice.hidden=!report.collection_notice;
  collectionNotice.textContent=report.collection_notice||"";
  if($("#category").options.length===1){for(const [key,title]of Object.entries(categoryNames)){const option=el("option","",title);option.value=key;$("#category").append(option);}}
  enhanceSelects();renderTable();renderHistory();renderScoringEvidence();renderCohorts();
}
function renderTable(){
  const query=$("#search").value.trim().toLocaleLowerCase(),category=$("#category").value,lang=$("#language").value,cohort=$("#cohort").value,scope=$("#scope").value;
  const rows=records().filter(r=>(category==="all"||r.category===category)&&(lang==="all"||r.language===lang)&&(cohort==="all"||r.cohort===cohort)&&(scope==="all"||(scope==="current"?r.session:!r.session))&&[r.title,r.catalog.title_en,r.catalog.id].join(" ").toLocaleLowerCase().includes(query));
  rows.sort((a,b)=>{
    if(sortKey){const x=a[sortKey],y=b[sortKey];if(x===null&&y!==null)return 1;if(y===null&&x!==null)return -1;return (typeof x==="number"?x-y:String(x??"").localeCompare(String(y??""),"zh-CN"))*sortDirection;}
    if(Boolean(a.session)!==Boolean(b.session))return a.session?-1:1;
    if(a.session&&b.session)return order.indexOf(a.session.case)-order.indexOf(b.session.case)||a.language.localeCompare(b.language)*-1;
    return a.title.localeCompare(b.title,"zh-CN");
  });
  const target=$("#report-rows");target.replaceChildren();
  for(const record of rows){
    const s=record.session,row=el("tr"),name=cell(row);
    const displayTitle=record.title+(s?.variant==="before"?" · 改前":s?.variant==="after"?" · 改后":"");
    if(s?.rows.length&&s.logs)name.append(logLink(s,displayTitle,"text-button name-button"));else name.textContent=displayTitle;
    name.title=record.catalog.title_en+" · "+record.catalog.id;
    if(s?.case==="sushi"){
      const scope=el("span","baseline","沿用既有框架");
      scope.title="本轮未专项改动；与李白是不同人物，不能当作同剧本优化前后的对照。";
      name.append(scope);
    }
    if(s?.live_execution){
      name.append(el("span","baseline","下列分数来自旧片段 "+s.rows.length+" 条回复"));
    }else if(s&&record.scored&&(!s.complete||record.scored<s.rows.length)){
      name.append(el("span","baseline","数值评分覆盖 "+record.scored+"/"+s.rows.length+"；非整场最终分"));
    }
    cell(row,cohortNames[record.cohort]||"—");cell(row,categoryNames[record.category]);cell(row,language(record.language));const statusCell=cell(row,s?.display_status||states[record.status]||record.status,"status");if(s?.interruption)statusCell.title=s.interruption;
    cell(row,s?record.collected+"/51":"—","num");cell(row,s?record.scored+"/"+s.rows.length:"—","num");
    for(const key of ["minimum","maximum","mean","stddev"]){
      const value=record[key]===null?"—":record[key].toFixed(key==="stddev"?2:1);
      const note=key==="mean"&&s&&(!s.complete||record.scored<s.rows.length)&&record[key]!==null?"（仅"+record.scored+"条）":"";
      cell(row,value+note,"num");
    }
    cell(row,record.coreIssues===null?"—":record.coreIssues,"num");
    const detail=cell(row);if(s?.rows.length&&s.logs)detail.append(logLink(s));else detail.textContent="—";
    target.append(row);
  }
  if(!rows.length){const row=el("tr"),td=cell(row,"无匹配记录","no-results");td.colSpan=13;target.append(row);}
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
function renderScoringEvidence(){
  const comparison=report.scoring?.comparison,calibration=report.scoring?.calibration;
  const comparisonSection=$("#comparison-evidence"),calibrationSection=$("#calibration-evidence");
  comparisonSection.hidden=!comparison;calibrationSection.hidden=!calibration;
  if(comparison){
    $("#comparison-status").textContent=comparison.status;
    $("#comparison-explanation").textContent=comparison.explanation+" "+comparison.execution;
    const target=$("#comparison-rows");target.replaceChildren();
    const names={figure:"李白",story:"Alice",sushi:"苏轼",guess:"动物猜谜",adventure:"宝藏探索",learn:"一年级科学"};
    for(const pair of comparison.prepared_versions){
      const row=el("tr");cell(row,names[pair.case]||pair.case);
      cell(row,pair.before_sha256.slice(0,12),"hash");
      cell(row,pair.after_sha256.slice(0,12),"hash");
      cell(row,pair.source_changed?"源码有改动；收益待同题实测":"两份源码相同");
      target.append(row);
    }
    const paired=$("#paired-comparison"),pairedRows=$("#paired-comparison-rows");
    paired.hidden=!comparison.paired_results;
    pairedRows.replaceChildren();
    for(const item of comparison.paired_results||[]){
      const row=el("tr");cell(row,item.title);cell(row,language(item.language));
      cell(row,item.before_mean===null?"—":item.before_mean.toFixed(2),"num");
      cell(row,item.after_mean===null?"—":item.after_mean.toFixed(2),"num");
      cell(row,item.paired_delta===null?"—":(item.paired_delta>0?"+":"")+item.paired_delta.toFixed(2),"num");
      cell(row,item.before_coverage+" / "+item.after_coverage);
      cell(row,item.matched_scored_replies+"/52","num");
      cell(row,item.improved+" / "+item.regressed+" / "+item.unchanged,"num");
      pairedRows.append(row);
    }
  }
  if(calibration){
    $("#calibration-method").textContent=calibration.method+" "+calibration.normal_controls+"个正常控制未误扣，"+calibration.pending+"个未知保留待核。";
    const target=$("#calibration-rows");target.replaceChildren();
    for(const pair of calibration.pairs){
      const row=el("tr");cell(row,pair.name);cell(row,pair.before,"num");cell(row,pair.after,"num");cell(row,"+"+pair.delta,"num");cell(row,"人工修复对照");target.append(row);
    }
  }
}
function renderCohorts(){
  const cohorts=report.scoring?.cohorts,section=$("#cohort-evidence");
  section.hidden=!cohorts;if(!cohorts)return;
  $("#cohort-status").textContent=cohorts.status;
  $("#cohort-description").textContent=cohorts.description+" 覆盖为已评分/已记录；当前均分只代表已有评分，待核保持空值。";
  const categories=$("#cohort-category-rows");categories.replaceChildren();
  for(const item of cohorts.categories){
    const row=el("tr");cell(row,categoryNames[item.category]);cell(row,language(item.language));
    for(const cohort of ["optimized","control"]){
      const value=item[cohort];cell(row,value.title);
      cell(row,value.mean===null?"—":value.mean.toFixed(2),"num");
      cell(row,value.rated_replies+"/"+value.recorded_replies);
    }
    categories.append(row);
  }
  const groups=$("#cohort-group-rows");groups.replaceChildren();
  for(const item of cohorts.groups){
    const row=el("tr");cell(row,cohortNames[item.cohort]);cell(row,language(item.language));
    cell(row,item.rated_scripts+"/5","num");cell(row,item.rated_replies+" / "+item.recorded_replies);
    for(const key of ["minimum","maximum","mean","stddev"])cell(row,item[key]===null?"—":item[key].toFixed(2),"num");
    groups.append(row);
  }
}
for(const selector of ["#search","#category","#language","#cohort","#scope"])$(selector).addEventListener(selector==="#search"?"input":"change",renderTable);
$$('[data-sort]').forEach(th=>$("button",th).addEventListener("click",()=>{if(sortKey===th.dataset.sort)sortDirection*=-1;else{sortKey=th.dataset.sort;sortDirection=1;}renderTable();}));
$("#filters").addEventListener("submit",event=>event.preventDefault());
render();
async function refresh(){try{const response=await fetch("report.json?updated="+Math.floor(Date.now()/60000),{cache:"no-store"});if(!response.ok)return;const next=await response.json();if(next.schema==="raids-public-report/v1"&&next.updated_at!==report?.updated_at){report=next;render();}}catch(_){}}
refresh();setInterval(refresh,60000);
