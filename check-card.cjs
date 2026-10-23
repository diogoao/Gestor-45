const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element{
 constructor(tag='div'){this.tag=tag;this.dataset={};this.children=[];this.parts=new Map();this.events={};this.attributes={};this.open=false;this.disabled=false;}
 setAttribute(k,v){this.attributes[k]=v;}
 querySelector(k){if(!this.parts.has(k)){const child=new Element();child.parent=this;this.parts.set(k,child);}return this.parts.get(k);}
 append(child){child.parent=this;this.children.push(child);}
 replaceChildren(){this.children=[];}
 addEventListener(name,fn){this.events[name]=fn;}
 showModal(){this.open=true;}
 close(){this.open=false;this.events.close?.();}
 contains(target){for(let e=target;e;e=e.parent)if(e===this)return true;return false;}
 closest(){for(let e=this;e;e=e.parent)if(e.dataset.actDay)return e;return null;}
 getBoundingClientRect(){return {left:0,right:100,top:0,bottom:100};}
}
const body=new Element(),listeners={},agenda=new Element();
const document={body,querySelector:s=>s==='#agendaCard'?agenda:null,createElement:t=>new Element(t),addEventListener:(name,fn)=>listeners[name]=fn};
const date='2026-10-26',category='juri',number='0000001-00.2026.8.17.2001',url='https://drive.google.com/drive/folders/test';
const window={PublicMaterialsData:{pauta:async()=>({}),index:async()=>({links:new Map([[number,url]])}),events:()=>[{date,category,number,time:'09:00'}]}};
const context={document,window};vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/Gestor MP/index.html','utf8').split('// Navegação de consulta, sem as operações do painel local.')[1].split('</script>')[0],context);
const modal=body.children[0],back=modal.querySelector('.public-back'),close=modal.querySelector('.public-close');
function delegated(target,extra={}){const event={target,prevented:false,preventDefault(){this.prevented=true;},...extra};listeners.click(event);return event;}
(async()=>{
 const trigger=new Element('a');trigger.dataset={actDay:date,actCategory:category};
 assert.equal(delegated(trigger).prevented,true);await new Promise(setImmediate);
 assert.equal(modal.open,true);const row=modal.querySelector('.public-files').children[0];
 assert.equal(row.href,url);assert.equal(row.target,'_blank');
 assert.equal(delegated(row.querySelector('.public-event-process')).prevented,false,'process link must keep its default navigation');
 close.onclick();delegated(close);await new Promise(setImmediate);assert.equal(modal.open,false,'close must not reopen card');
 await window.PublicMaterials.openDay(date,category);assert.equal(back.disabled,false);assert.equal(back.attributes['aria-label'],'Voltar à página inicial');
 back.onclick();delegated(back);await new Promise(setImmediate);assert.equal(modal.open,false,'back must return to homepage');
 await window.PublicMaterials.openDay(date,category);const original=modal.querySelector('.original');assert.equal(delegated(original).prevented,false);
 modal.events.click({target:modal,clientX:200,clientY:200});delegated(modal);await new Promise(setImmediate);assert.equal(modal.open,false,'backdrop close must not reopen');
 assert.equal(delegated(trigger,{ctrlKey:true}).prevented,false);assert.equal(modal.open,false);
 console.log('PASS: date opens card; process and original Drive links remain native; Close, Back and backdrop close without reopening; modified clicks preserved.');
})().catch(e=>{console.error(e);process.exitCode=1;});
