/* Source and fixture-state checks only. This is not a browser or a DOM renderer. */
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const file = path.join(__dirname, 'prototype.html');
const html = fs.readFileSync(file, 'utf8');
const source = html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(source);
const elements = new Map();
const listeners = {};
function element(key) {
  if (!elements.has(key)) elements.set(key, {
    value: '', checked: false, open: false, innerHTML: '', textContent: '',
    tagName: 'INPUT', dataset: {}, options: [], attrs: {}, disabled: false,
    classList: {add() {}, remove() {}}, setAttribute(k,v) {this.attrs[k]=v;},
    insertAdjacentHTML(position,html){this.innerHTML=html+this.innerHTML;},scrollTop:0,scrollHeight:1000,focus() {}, showModal() {this.open=true;}, close() {this.open=false;},
  });
  return elements.get(key);
}
element('#demoState').value = 'normal';
element('#demoState').options = Array.from({length:10},()=>({value:'',textContent:''}));
const context = {
  document: {body:{dataset:{variant:'A'}}, documentElement:{lang:'en'},
    querySelector:element, getElementById:id=>element('#'+id),
    querySelectorAll:selector=>selector.includes('curateAccount')?[{value:'@mio.beauty'}]:[],
    addEventListener:(name,fn)=>{(listeners[name]??=[]).push(fn);}},
  location:{href:'http://127.0.0.1:8876/prototype.html',hash:''},
  history:{replaceState(){}}, URL,URLSearchParams,
  setTimeout:()=>1,clearTimeout(){},MouseEvent:class {},
  fetch(){throw Error('External calls are forbidden in fixture checks');},
};
context.window=context;
vm.createContext(context);vm.runInContext(source,context);
const run=s=>vm.runInContext(s,context);
if(process.argv.includes('--markup')){
 const markup={};
 for(const language of ['en','ko'])for(const view of ['assistant','monitoring','graph']){
  run(`lang='${language}';page='${view}';render()`);
  markup[language+'-'+view]=element('#main').innerHTML;
 }
 console.log(JSON.stringify(markup));process.exit(0);
}
let passed=0;
function check(name,fn){fn();passed++;console.log('PASS '+name);}
check('JavaScript parses and initial campaign renders',()=>assert.match(element('#main').innerHTML,/Recommended accounts/));
check('Exact approval cannot submit without explicit checkbox',()=>{run("proposal();actions.approve()");assert.equal(run('proposalState'),'draft');assert.equal(run('approvedRevision'),null);});
check('Revised scope creates a fresh immutable revision and clears approval',()=>{element('#scopeQuery').value='new query';element('#scopeSubject').value='Cushion';element('#scopeRecords').value='12';run('actions.saveScope()');assert.equal(run('proposalRevision'),2);assert.equal(run('proposalScope.query'),'new query');assert.equal(run('approvedRevision'),null);});
check('Saved proposal scope and purpose are immutable snapshots',()=>{assert.equal(run('Object.isFrozen(proposalSnapshots[0])'),true);assert.equal(run('Object.isFrozen(proposalSnapshots[0].scope)'),true);assert.equal(run('proposalSnapshots[0].scope.query'),'クッションファンデ');assert.equal(run('proposalSnapshots[1].scope.query'),'new query');});
check('Explicit checked approval queues the exact revision',()=>{element('#approveCheck').checked=true;run('actions.approve()');assert.equal(run('approvedRevision'),2);assert.equal(run('proposalState'),'queued');assert.equal(run('approvedProposal.revision'),2);assert.equal(run('approvedProposal.scope.records'),12);});
check('Closed modal prevents approval replay from becoming another task',()=>{run('actions.approve()');assert.equal(run('approvedRevision'),2);assert.equal(run('proposalRevision'),2);});
check('Acquisition remains unusable until publication',()=>{run('actions.advanceTask();actions.advanceTask()');assert.equal(run('taskState'),'retrieved');assert.match(element('#main').innerHTML,/publication|Published|publication/i);run('actions.advanceTask()');assert.equal(run('taskState'),'published');});
check('Publication does not regenerate a saved shortlist',()=>assert.equal(run('revision'),2));
check('Explicit regeneration appends history without changing previous membership',()=>{const original=run('JSON.stringify(revisionRecords[1])');run('actions.confirmRegenerate()');assert.equal(run('revision'),3);assert.equal(run('JSON.stringify(revisionRecords[1])'),original);assert.equal(run('revisionRecords[2].author'),'automation');});
check('Optional curation saves selected membership with human attribution',()=>{element('#curationReason').value='Fixture reason';run('actions.saveCuration()');assert.equal(run('revision'),4);assert.equal(run('revisionRecords[3].author'),'Mina');assert.equal(run('revisionRecords[3].accounts.length'),1);assert.doesNotMatch(run('campaign()'),/<strong>@sora.skin<\/strong>/);});
check('Unknown response retains waiting and does not reissue a request',()=>{run('actions.unknownResponse()');assert.equal(run('taskState'),'waiting');});
check('Context-only investigation changes no campaign revision',()=>{const before=run('revision');run('actions.context()');assert.equal(run('alertContext'),true);assert.equal(run('revision'),before);});
check('Selective promotion rejects an empty selection',()=>{element('#promoteCheck').checked=false;run('actions.promote()');assert.equal(run('promoted'),false);});
check('Graph traversal projects observed and derived edges',()=>{run("page='graph';selected='post1';hop=1;graphBasis='all';graphText='';drawGraph()");assert.match(element('#graphSvg').innerHTML,/data-edge="e1"/);assert.match(element('#graphSvg').innerHTML,/data-edge="e3"/);});
check('Graph relationship basis filter removes other edge bases',()=>{run("graphBasis='observed';drawGraph()");assert.doesNotMatch(element('#graphSvg').innerHTML,/data-edge="e3"/);});
check('Graph deeper traversal includes human catalog association',()=>{run("graphBasis='all';hop=2;drawGraph()");assert.match(element('#graphSvg').innerHTML,/data-edge="e5"/);});
check('Graph relationship inspector exposes derived basis and evidence',()=>{run("selected='e3';inspectGraph()");assert.match(element('#graphInspector').innerHTML,/Provisional literal mention/);assert.match(element('#graphInspector').innerHTML,/obs-21/);});
check('Withdrawal removes source node and its dependent relationships',()=>{run('actions.withdraw()');assert.doesNotMatch(element('#graphSvg').innerHTML,/data-node="post1"/);assert.doesNotMatch(element('#graphSvg').innerHTML,/data-edge="e3"/);assert.match(element('#graphInspector').innerHTML,/Unavailable under current policy/);});
check('Bilingual switch preserves text drafts and semantic select values',()=>{for(const [id,value] of [['briefTitle','Unsaved campaign'],['criteria','Original criteria'],['question','My question'],['note','Draft note']]){listeners.input.forEach(fn=>fn({target:{id,value}}));}listeners.change.forEach(fn=>fn({target:{id:'market',value:'KR'}}));run("page='campaigns';tab='brief';lang='ko';render()");assert.equal(element('#briefTitle').value,'Unsaved campaign');assert.equal(element('#criteria').value,'Original criteria');assert.equal(element('#market').value,'KR');assert.equal(run('formEdits.question'),undefined);assert.equal(run('formEdits.note'),'Draft note');assert.match(element('#variantLabel').textContent,/근거 중심/);});
check('Localized state labels retain stable underlying state values',()=>{assert.equal(element('#demoState').options[2].value,'Loading');assert.equal(element('#demoState').options[2].textContent,'불러오는 중');});
check('Restricted state hides source view instead of leaking fixture evidence',()=>{element('#demoState').value='Restricted';run('render()');assert.doesNotMatch(element('#main').innerHTML,/軽いつけ心地/);});
check('Keyword registration enforces the ten-keyword limit',()=>{run('keywords=10');element('#newKeyword').value='test';run('actions.saveKeyword()');assert.equal(run('keywords'),10);});
check('Prototype has no external assets or network code',()=>{assert.doesNotMatch(html,/<(?:script|img)[^>]+src=|<link[^>]+href=|\bfetch\s*\(|XMLHttpRequest|WebSocket|localStorage|sessionStorage/);});
check('Responsive, focus, dialog and keyboard source hooks exist',()=>{for(const pattern of ['@media(max-width:650px)',':focus-visible','prefers-reduced-motion','<dialog',"['Enter',' ']",'ArrowLeft','data-node'])assert.ok(html.includes(pattern),pattern);});
check('Monitoring target engagement success shows matched metric age and denominators',()=>{run("lang='en';monitoringMethod='engagement';baselineQuality='comparable'");assert.match(run('monitoringSummary()'),/24 recent vs 24 baseline/);assert.match(run('monitoringSummary()'),/6 hours/);});
check('Semantic shift target preserves coded numerator, denominator and provisional meaning',()=>{run("monitoringMethod='semantic_shift'");assert.match(run('monitoringSummary()'),/7 of 20 recent inputs vs 2 of 20/);assert.match(run('monitoringSummary()'),/not population sentiment/);});
check('Insufficient baseline withholds a spike or shift result',()=>{run("baselineQuality='missing'");assert.match(run('monitoringSummary()'),/No assessable signal/);assert.doesNotMatch(run('monitoringSummary()'),/metric-strip/);});
check('Failed method withholds generated signal without granting acquisition',()=>{run("baselineQuality='invalid'");assert.match(run('monitoringSummary()'),/does not authorize external research/);assert.doesNotMatch(run('monitoringSummary()'),/metric-strip/);});
check('New campaign starts empty and requires a saved complete brief',()=>{element('#demoState').value='normal';element('#newCampaignName').value='New fixture campaign';run('actions.createCampaign()');assert.equal(run('revision'),0);assert.equal(run('revisionRecords.length'),0);run('actions.initialRecommendation()');assert.equal(run('revision'),0);element('#briefTitle').value='New fixture campaign';element('#objective').value='Consideration';element('#criteria').value='Source-backed category evidence';run('actions.saveBrief();actions.initialRecommendation()');assert.equal(run('revision'),1);assert.equal(run('revisionRecords[0].brief'),1);assert.equal(run('revisionRecords[0].author'),'automation');});

function input(id,value){element('#'+id).value=value;listeners.input.forEach(fn=>fn({target:{id,value}}));}
function change(id,value){listeners.change.forEach(fn=>fn({target:{id,value}}));}
function key(target,key,extras={}){let prevented=false;listeners.keydown.forEach(fn=>fn({target,key,preventDefault(){prevented=true;},...extras}));return prevented;}
function clickAction(action){listeners.click.forEach(fn=>fn({target:{closest(){return {dataset:{action}};}}}));}
check('Chat renders distinct turns, scrollable log, threads and bottom composer',()=>{element('#demoState').value='normal';run("lang='en';withdrawn=false;page='assistant';render()");const h=element('#main').innerHTML;for(const token of ['chat-turn user','chat-turn assistant','role="log"','class="composer"','New conversation','Sources, dates and claim details'])assert.ok(h.includes(token),token);assert.ok(h.indexOf('class="composer"')>h.indexOf('role="log"'));});
check('Enter sends escaped text and deterministic fixture follow-up, clearing only its draft',()=>{input('question','Compare <sample>\nwith dates');const before=run('currentThread().turns.length');assert.equal(key({id:'question'},'Enter'),true);assert.equal(run('currentThread().turns.length'),before+2);assert.equal(run('currentThread().draft'),'');assert.match(element('#main').innerHTML,/&lt;sample&gt;/);assert.equal(run('currentThread().turns.at(-1).fixtureFollowup'),true);assert.equal(element('#question').value,'');});
check('Shift+Enter and IME composition do not send',()=>{input('question','Multiline draft');const before=run('currentThread().turns.length');assert.equal(key({id:'question',dataset:{},closest(){return true;}},'Enter',{shiftKey:true}),false);assert.equal(key({id:'question',dataset:{},closest(){return true;}},'Enter',{isComposing:true}),false);assert.equal(run('currentThread().turns.length'),before);});
check('Send button and plain yes cannot approve or create acquisition',()=>{const before=run('JSON.stringify([proposalRevision,proposalState,approvedRevision,taskState])');input('question','yes');clickAction('sendChat');assert.equal(run('currentThread().turns.at(-1).kind'),'ack');assert.equal(run('JSON.stringify([proposalRevision,proposalState,approvedRevision,taskState])'),before);});
check('Threads preserve separate drafts and conversation context across EN/KO and navigation',()=>{input('question','Original draft 원문');const before=run('JSON.stringify(currentThread().turns)');element('#conversation').scrollTop=77;run("lang='ko';render();page='monitoring';render();page='assistant';render()");assert.equal(element('#question').value,'Original draft 원문');assert.equal(element('#conversation').scrollTop,77);assert.equal(run('JSON.stringify(currentThread().turns)'),before);clickAction('newConversation');input('question','Second thread draft');clickAction('thread:cushion');assert.equal(element('#question').value,'Original draft 원문');assert.equal(run('JSON.stringify(currentThread().turns)'),before);clickAction('thread:thread-3');assert.equal(element('#question').value,'Second thread draft');});
check('Empty composer cannot create a turn',()=>{input('question','  ');const before=run('currentThread().turns.length');clickAction('sendChat');assert.equal(run('currentThread().turns.length'),before);});
check('Retrieved task material is excluded from fixture answer support',()=>{run("taskState='retrieved'");input('question','What is supported?');clickAction('sendChat');assert.equal(run('currentThread().turns.at(-1).support'),'pub-17 / obs-21');assert.match(element('#main').innerHTML,/pub-17/);});
check('Publication and policy withdrawal preserve pinned turns while withholding content',()=>{const before=run('JSON.stringify(currentThread().turns)');run("taskState='published';render()");assert.equal(run('JSON.stringify(currentThread().turns)'),before);run('withdrawn=true;render()');assert.doesNotMatch(element('#main').innerHTML,/軽いつけ心地/);assert.match(element('#main').innerHTML,/철회/);run('withdrawn=false');});
check('Reopening submitted proposal cannot create another approval of same revision',()=>{run("proposalState='queued';proposal()");assert.match(element('#modal').innerHTML,/이미 제출된/);assert.doesNotMatch(element('#modal').innerHTML,/id="approveCheck"/);run('closeModal()');});
check('Monitoring SVG shows latest 24, axes, units, current region and accessible table',()=>{run("lang='en';page='monitoring';monitoringMethod='volume';baselineQuality='comparable';monitorWindow='w6';historyRange=6;render()");const h=element('#main').innerHTML;for(const token of ['Latest 24','streamTitle streamDesc','stroke="#E6002A"','Window values and keyboard selection','Distinct eligible posts / window','Selected window','24 vs 8'])assert.ok(h.includes(token),token);});
check('Chronological windows have an explicit missing collection, zero and unscheduled gap',()=>{assert.equal(run('monitorWindows[2].volume'),null);assert.equal(run('monitorWindows[3].volume'),0);assert.equal(run('monitorWindows.every((w,i,a)=>i===0||Date.parse(w.start)>Date.parse(a[i-1].start))'),true);const chart=run('monitoringChart()');assert.equal((chart.match(/class="series"/g)||[]).length,3);assert.match(chart,/Missing collection/);assert.match(chart,/No collection was scheduled at 23:00/);});
check('Point and table selection update corresponding summary and evidence',()=>{clickAction('window:w2');assert.equal(run('monitorWindow'),'w2');assert.match(run('selectedWindowSummary()'),/<strong>9<\/strong>/);clickAction('windowEvidence');assert.match(element('#modal').innerHTML,/evidence-w2/);assert.match(element('#modal').innerHTML,/21:00–22:00/);assert.equal(key({dataset:{action:'window:w6'}},'Enter'),true);assert.equal(run('monitorWindow'),'w6');});
check('All four latest metrics match chart values, denominators and selected summary',()=>{for(const [method,value] of [['volume','24'],['engagement','36'],['semantic_shift','35%'],['controversy','4']]){run(`monitoringMethod='${method}';baselineQuality='comparable'`);assert.ok(run('monitoringChart()').includes('Latest '+value));assert.ok(run('selectedWindowSummary()').includes('<strong>'+value+'</strong>'));assert.ok(run('monitoringSummary()').includes(value));}assert.match(run('selectedWindowSummary()'),/4 selected of 12/);});
check('Metric-specific baseline missing and failed states never invent change',()=>{for(const method of ['volume','engagement','semantic_shift','controversy']){run(`monitoringMethod='${method}';baselineQuality='missing'`);assert.match(run('monitoringSummary()'),/No assessable signal/);run("baselineQuality='invalid'");assert.match(run('monitoringSummary()'),/does not authorize external research/);if(['semantic_shift','controversy'].includes(method)){assert.equal(run('metricValue(monitorWindows.at(-1))'),null);assert.doesNotMatch(run('monitoringChart()'),/class="series"/);}}run("render()");assert.doesNotMatch(element('#main').innerHTML,/Possible quality controversy/);});
check('Bounded history and metric controls retain or deliberately reset selected window',()=>{run("baselineQuality='comparable';monitorWindow='w2';historyRange=6");change('historyRange','4');assert.equal(run('monitorWindow'),'w6');assert.equal(run('visibleWindows().length'),4);clickAction('window:w5');change('monitorMethod','engagement');run("lang='ko';render();page='campaigns';render();page='monitoring';render()");assert.equal(run('monitorWindow'),'w5');assert.equal(run('monitoringMethod'),'engagement');assert.equal(run('historyRange'),4);assert.match(run('selectedWindowSummary()'),/<strong>20<\/strong>/);});

function luminance(hex){const c=hex.match(/[a-f0-9]{2}/gi).map(h=>parseInt(h,16)/255).map(c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4);return .2126*c[0]+.7152*c[1]+.0722*c[2];}
function ratio(a,b){const values=[luminance(a),luminance(b)].sort((a,b)=>b-a);return (values[0]+.05)/(values[1]+.05);}
check('Primary text palette pairs meet normal-text 4.5 contrast',()=>{for(const [a,b] of [['#FFFFFF','#E6002A'],['#FFFFFF','#3E3A39'],['#3E3A39','#F4ABAF']]){const r=ratio(a,b);assert.ok(r>=4.5,`${a} on ${b}: ${r}`);console.log(`CONTRAST ${a} / ${b}: ${r.toFixed(2)}:1`);}});
console.log(`${passed} source/fixture-state checks passed. No browser, rendering, screenshots or human review performed.`);
