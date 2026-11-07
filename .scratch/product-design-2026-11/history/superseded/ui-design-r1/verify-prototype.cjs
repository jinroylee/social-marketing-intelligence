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
    focus() {}, showModal() {this.open=true;}, close() {this.open=false;},
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
let passed=0;
function check(name,fn){fn();passed++;console.log('PASS '+name);}
check('JavaScript parses and initial campaign renders',()=>assert.match(element('#main').innerHTML,/Recommended accounts/));
check('Exact approval cannot submit without explicit checkbox',()=>{run("proposal();actions.approve()");assert.equal(run('proposalState'),'draft');assert.equal(run('approvedRevision'),null);});
check('Revised scope creates a fresh immutable revision and clears approval',()=>{element('#scopeQuery').value='new query';element('#scopeSubject').value='Cushion';element('#scopeRecords').value='12';run('actions.saveScope()');assert.equal(run('proposalRevision'),2);assert.equal(run('proposalScope.query'),'new query');assert.equal(run('approvedRevision'),null);});
check('Explicit checked approval queues the exact revision',()=>{element('#approveCheck').checked=true;run('actions.approve()');assert.equal(run('approvedRevision'),2);assert.equal(run('proposalState'),'queued');});
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
check('Bilingual switch preserves text drafts and semantic select values',()=>{for(const [id,value] of [['briefTitle','Unsaved campaign'],['criteria','Original criteria'],['question','My question'],['note','Draft note']]){listeners.input.forEach(fn=>fn({target:{id,value}}));}listeners.change.forEach(fn=>fn({target:{id:'market',value:'KR'}}));run("page='campaigns';tab='brief';lang='ko';render()");assert.equal(element('#briefTitle').value,'Unsaved campaign');assert.equal(element('#criteria').value,'Original criteria');assert.equal(element('#market').value,'KR');assert.equal(run('formEdits.question'),'My question');assert.equal(run('formEdits.note'),'Draft note');assert.match(element('#variantLabel').textContent,/근거 중심/);});
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
function luminance(hex){const c=hex.match(/[a-f0-9]{2}/gi).map(h=>parseInt(h,16)/255).map(c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4);return .2126*c[0]+.7152*c[1]+.0722*c[2];}
function ratio(a,b){const values=[luminance(a),luminance(b)].sort((a,b)=>b-a);return (values[0]+.05)/(values[1]+.05);}
check('Primary text palette pairs meet normal-text 4.5 contrast',()=>{for(const [a,b] of [['#FFFFFF','#E6002A'],['#FFFFFF','#3E3A39'],['#3E3A39','#F4ABAF']]){const r=ratio(a,b);assert.ok(r>=4.5,`${a} on ${b}: ${r}`);console.log(`CONTRAST ${a} / ${b}: ${r.toFixed(2)}:1`);}});
console.log(`${passed} source/fixture-state checks passed. No browser, rendering, screenshots or human review performed.`);
