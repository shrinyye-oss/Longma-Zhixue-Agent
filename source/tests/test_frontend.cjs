const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const db=JSON.parse(fs.readFileSync(path.join(root,'data/knowledge.json'),'utf8'));
const nodes=new Map();
function element(id){if(!nodes.has(id))nodes.set(id,{id,hidden:false,innerHTML:'',textContent:'',value:'',disabled:false,style:{},classList:{toggle(){}},addEventListener(){},scrollIntoView(){},showModal(){},focus(){}});return nodes.get(id)}
const context={
  document:{getElementById(id){return id==='knowledge-json'?{textContent:JSON.stringify(db)}:element(id)},querySelectorAll(){return []}},
  localStorage:{value:{},getItem(k){return this.value[k]??null},setItem(k,v){this.value[k]=v},removeItem(k){delete this.value[k]}},
  location:{protocol:'file:'},
  console,
  Date,
  Intl,
  setTimeout,
  confirm:()=>true,
  alert:()=>{},
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root,'src/app.js'),'utf8'),context,{filename:'src/app.js'});
assert.equal(vm.runInContext("retrieve('RAG和微调的区别')[0].topic.id",context),'1.4');
assert.equal(vm.runInContext("retrieve('API Token 计费')[0].topic.id",context),'1.2');
vm.runInContext("showTopic(byId('1.4'),'帮我复习RAG与微调')",context);
assert.match(element('knowledge-title').textContent,/知识库/);
assert.match(element('quiz-question').textContent,/RAG|课程|方案/);
vm.runInContext("saveResult('1.4','q1401',false)",context);
assert.equal(vm.runInContext("getRecord('1.4').attempts",context),1);
assert.equal(vm.runInContext("chooseQuestion(byId('1.4')).id",context),'q1402');
vm.runInContext('renderProgress()',context);
assert.equal(element('total-attempts').textContent,1);
assert.equal(element('total-covered').textContent,'1/10');
console.log('PASS front-end: retrieval, adaptive selection, persistence, progress');
