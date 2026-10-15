/* ER editor: structured model, validated Mermaid import, local draft and SVG preview. */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const key = 'okestre.er-diagram.v1';
const ident = /^[A-Za-z_\u00c0-\u024f][\w\u00c0-\u024f-]*$/u;
const typePattern = /^[A-Za-z_][\w\[\]()-]*$/;
const cards = ['one', 'zeroOne', 'many', 'zeroMany'];
const cardLabels = ['Exatamente um', 'Zero ou um', 'Um ou mais', 'Zero ou mais'];
const left = ['||', '|o', '}|', '}o'], right = ['||', 'o|', '|{', 'o{'];
const example = `erDiagram
  direction TB
  CUSTOMER {
  }
  DELIVERY-ADDRESS {
  }
  ORDER {
  }
  ORDER-ITEM {
  }
  PRODUCT-CATEGORY {
  }
  PRODUCT {
  }
  Untitled-Entity {
  }
  INVOICE {
    Nome Nome FK "tetre"
  }
  CUSTOMER }|..|{ DELIVERY-ADDRESS : "has"
  CUSTOMER ||--o{ ORDER : "places"
  CUSTOMER ||--o{ INVOICE : "liable for"
  DELIVERY-ADDRESS ||--o{ ORDER : "receives"
  INVOICE ||--|{ ORDER : "covers"
  ORDER ||--|{ ORDER-ITEM : "includes"
  PRODUCT-CATEGORY ||--|{ PRODUCT : "contains"
  PRODUCT ||--o{ ORDER-ITEM : "ordered in"
  PRODUCT-CATEGORY }|--|{ Untitled-Entity : "  "`;
let model, selected = 0, revision = 0, scale = 1, svg = '', dirtyCode = false;
function message(text, error = false) { $('message').textContent = text; $('message').classList.toggle('error', error); }
function parse(source) {
  if(source.length > 100000) throw Error('O diagrama deve ter no máximo 100 KB.');
  const doc = {direction:'TB', entities:[], relations:[]};
  let entity = null, header = false;
  for(const [n, raw] of source.replace(/\r/g,'').split('\n').entries()) {
    const line = raw.trim();
    if(!line || line.startsWith('%%')) continue;
    const fail = () => { throw Error(`Linha ${n+1}: sintaxe não suportada pelo editor visual.`); };
    if(!header) { if(line !== 'erDiagram') fail(); header = true; continue; }
    if(entity) {
      if(line === '}') {entity = null; continue;}
      const a = line.match(/^(\S+)\s+(\S+)(?:\s+((?:PK|FK|UK)(?:\s*,\s*(?:PK|FK|UK))*))?(?:\s+"([^"\r\n]*)")?$/);
      if(!a || !typePattern.test(a[1]) || !ident.test(a[2])) fail();
      entity.attributes.push({type:a[1], name:a[2], key:(a[3]||'').replace(/\s/g,''), comment:a[4]||''}); continue;
    }
    const direction = line.match(/^direction (TB|BT|LR|RL)$/);
    if(direction) { doc.direction = direction[1]; continue; }
    const ent = line.match(/^(\S+)\s*\{\s*(\})?$/);
    if(ent) { if(!ident.test(ent[1]) || doc.entities.some(e=>e.name===ent[1])) fail(); const e={name:ent[1],attributes:[]}; doc.entities.push(e); entity=ent[2]?null:e; continue; }
    const rel = line.match(/^(\S+?)\s*(\|\||\|o|}\||}o)(--|\.\.)(\|\||o\||\|{|o{)\s*(\S+)\s*:\s*"([^"\r\n]*)"$/);
    if(rel) {doc.relations.push({from:rel[1],to:rel[5],left:cards[left.indexOf(rel[2])],right:cards[right.indexOf(rel[4])],identifying:rel[3]==='--',label:rel[6]});continue;}
    fail();
  }
  if(!header || entity) throw Error('Confira erDiagram e o fechamento das chaves.');
  for(const r of doc.relations) for(const name of [r.from,r.to]) { if(!ident.test(name)) throw Error('Nome de entidade inválido.'); if(!doc.entities.some(e=>e.name===name)) doc.entities.push({name,attributes:[]}); }
  if(doc.entities.length>100 || doc.relations.length>200) throw Error('Limite de 100 entidades e 200 relações.');
  return doc;
}
function serialize() {
  const lines=['erDiagram',`  direction ${model.direction}`];
  for(const e of model.entities) {
    if(!ident.test(e.name)) throw Error('Use nomes de entidade sem espaços: letras, números, _ e hífen.');
    lines.push(`  ${e.name} {`);
    for(const a of e.attributes) {
      if(!typePattern.test(a.type)||!ident.test(a.name)||/["\r\n]/.test(a.comment)) throw Error('Confira tipo, nome e comentário do atributo. Comentários não podem conter aspas ou quebras de linha.');
      lines.push(`    ${a.type} ${a.name}${a.key?' '+a.key:''}${a.comment?' "'+a.comment+'"':''}`);
    }
    lines.push('  }');
  }
  for(const r of model.relations) {
    if(/["\r\n]/.test(r.label)) throw Error('O rótulo da relação não pode conter aspas ou quebras de linha.');
    lines.push(`  ${r.from} ${left[cards.indexOf(r.left)]}${r.identifying?'--':'..'}${right[cards.indexOf(r.right)]} ${r.to} : "${r.label}"`);
  }
  return lines.join('\n')+'\n';
}
function save() { try {localStorage.setItem(key,JSON.stringify({title:$('title').value,source:serialize()})); $('saved').textContent='Rascunho salvo neste navegador';} catch { $('saved').textContent='Não foi possível salvar neste navegador. Exporte o arquivo.'; } }
function fit() { const el=$('preview').querySelector('svg');if(!el)return; const b=el.viewBox.baseVal; scale=Math.min(1,($('viewport').clientWidth-60)/b.width); zoom(); }
function zoom() { const el=$('preview').querySelector('svg'); if(!el)return; const b=el.viewBox.baseVal;el.style.width=b.width*scale+'px';el.style.height=b.height*scale+'px'; }
async function render() {
  const seq=++revision;
  $('svg-export').disabled=true;
  let source;
  try {source=serialize();} catch(e) {message(e.message,true);return;}
  if(!dirtyCode) $('source').value=source;
  $('counts').textContent=`${model.entities.length} entidades · ${model.relations.length} relações`;
  $('direction').value=model.direction;
  save();
  if(!model.entities.length) {svg='';$('preview').replaceChildren();$('empty').hidden=false;return;}
  $('empty').hidden=true;
  try {
    const result=await mermaid.render('er-preview-'+seq,source);
    if(seq!==revision)return;
    svg=result.svg; $('preview').innerHTML=svg; fit(); $('svg-export').disabled=false; message('Diagrama atualizado.');
  } catch(e) {if(seq===revision) {svg='';$('preview').replaceChildren();message('Não foi possível renderizar. Confira o código e os atributos.',true);}}
}
function el(tag, text, cls) {const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function button(text, fn, cls) {const e=el('button',text,cls);e.type='button';e.onclick=fn;return e;}
function input(label,value,fn,options) {
  const box=el('label',label), control=el(options?'select':'input');
  if(options) options.forEach(([v,t])=>{const o=el('option',t);o.value=v;control.append(o);});
  control.setAttribute('aria-label',label);
  control.value=value; if(!options)control.maxLength=150;
  control.onchange=()=> { if(dirtyCode) {message('Aplique o código antes de editar visualmente.',true);control.value=value;return;} fn(control.value,control); };
  box.append(control);return box;
}
function editable(fn) {return ()=> {if(dirtyCode){message('Aplique o código antes de editar visualmente.',true);return;}fn();};}
function rebuild() {
  const select=$('entity-select');select.replaceChildren();model.entities.forEach((e,i)=>{const o=el('option',e.name);o.value=i;select.append(o);});
  selected=Math.max(0,Math.min(selected,model.entities.length-1));select.value=selected;
  const panel=$('entity-editor');panel.replaceChildren();const entity=model.entities[selected];
  if(entity) {
    panel.append(input('Nome da entidade',entity.name,(v,c)=>{if(!ident.test(v)||model.entities.some(e=>e!==entity&&e.name===v)){message('Nome inválido ou já utilizado.',true);c.value=entity.name;return;}model.relations.forEach(r=>{if(r.from===entity.name)r.from=v;if(r.to===entity.name)r.to=v;});entity.name=v;rebuild();render();}));
    panel.append(button('Excluir entidade',editable(()=>{if(!confirm('Excluir esta entidade e suas relações?'))return;model.relations=model.relations.filter(r=>r.from!==entity.name&&r.to!==entity.name);model.entities.splice(selected,1);rebuild();render();}),'danger'));
    entity.attributes.forEach((a,i)=>{
      const card=el('div',undefined,'card');card.append(button('×',editable(()=>{entity.attributes.splice(i,1);rebuild();render();}),'remove danger'));card.lastChild.setAttribute('aria-label','Excluir atributo '+a.name);
      const types=['string','text','char','varchar','int','bigint','float','double','decimal','boolean','date','time','datetime','timestamp','uuid','json','binary'];
      if(!types.includes(a.type))types.push(a.type);
      const row=el('div',undefined,'row');row.append(input('Tipo',a.type,v=>{a.type=v;render();},types.map(t=>[t,t])), input('Atributo',a.name,v=>{a.name=v;render();}));card.append(row);
      card.append(input('Chave',a.key,v=>{a.key=v;render();},['','PK','FK','UK','PK,FK','PK,UK','FK,UK','PK,FK,UK'].map(k=>[k,k||'Nenhuma'])),input('Comentário',a.comment,v=>{a.comment=v;render();}));panel.append(card);
    });
    panel.append(button('+ Atributo',editable(()=>{entity.attributes.push({type:'string',name:'campo_'+(entity.attributes.length+1),key:'',comment:''});rebuild();render();})));
  } else panel.append(el('p','Crie uma entidade para adicionar atributos.'));
  const rp=$('relation-editor');rp.replaceChildren();const names=model.entities.map(e=>[e.name,e.name]);
  model.relations.forEach((r,i)=>{
    const card=el('div',undefined,'card');card.append(button('Excluir relação',editable(()=>{model.relations.splice(i,1);rebuild();render();}),'remove danger'));
    card.append(input('Origem',r.from,v=>{r.from=v;render();},names),input('Cardinalidade da origem',r.left,v=>{r.left=v;render();},cards.map((v,i)=>[v,cardLabels[i]])),input('Destino',r.to,v=>{r.to=v;render();},names),input('Cardinalidade do destino',r.right,v=>{r.right=v;render();},cards.map((v,i)=>[v,cardLabels[i]])),input('Linha',r.identifying?'yes':'no',v=>{r.identifying=v==='yes';render();},[['yes','Identificadora — contínua'],['no','Não identificadora — pontilhada']]),input('Rótulo',r.label,v=>{r.label=v;render();}));rp.append(card);
  });
  if(!model.relations.length)rp.append(el('p','Conecte duas entidades e escolha suas cardinalidades.'));
  $('add-relation').disabled=!model.entities.length;
}
function download(name,data,type) {const url=URL.createObjectURL(new Blob([data],{type}));const a=el('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function filename() {return ($('title').value.trim()||'diagrama').replace(/[^\p{L}\p{N}_-]+/gu,'-');}
function apply(source) {try {const next=parse(source);model=next;dirtyCode=false;selected=0;rebuild();render();}catch(e){message(e.message,true);}}
$('entity-select').onchange=()=>{selected=Number($('entity-select').value);rebuild();};
$('add-entity').onclick=editable(()=>{if(model.entities.length>=100){message('Limite de 100 entidades.',true);return;}let i=1;while(model.entities.some(e=>e.name==='ENTIDADE-'+i))i++;model.entities.push({name:'ENTIDADE-'+i,attributes:[]});selected=model.entities.length-1;rebuild();render();});
$('add-relation').onclick=editable(()=>{if(model.relations.length>=200)return;model.relations.push({from:model.entities[0].name,to:model.entities[1]?.name||model.entities[0].name,left:'one',right:'zeroMany',identifying:true,label:'relaciona'});rebuild();render();});
$('direction').onchange=editable(()=>{model.direction=$('direction').value;render();});
$('source').oninput=()=>{dirtyCode=true;message('Código alterado. Clique em Aplicar código para atualizar.');};
$('apply').onclick=()=>apply($('source').value);
$('export').onclick=()=>{try{if(dirtyCode)throw Error('Aplique o código antes de exportar.');download(filename()+'.mmd',serialize(),'text/plain;charset=utf-8');}catch(e){message(e.message,true);}};
$('svg-export').onclick=()=>{if(dirtyCode){message('Aplique o código antes de exportar.',true);return;}if(svg)download(filename()+'.svg',svg,'image/svg+xml');};
$('copy').onclick=async()=>{try{await navigator.clipboard.writeText($('source').value);message('Código copiado.');}catch{$('source').focus();$('source').select();message('Selecione Copiar no navegador ou pressione Ctrl+C.');}};
$('import').onclick=()=>$('file').click();
$('file').onchange=async()=>{const f=$('file').files[0];if(!f)return;if(f.size>100000){message('Arquivo maior que 100 KB.',true);return;}if(confirm('Substituir o rascunho atual pelo arquivo?'))apply(await f.text());$('file').value='';};
$('new').onclick=()=>{if(confirm('Criar um novo diagrama? Exporte o atual para preservá-lo.')){$('title').value='Novo diagrama';apply('erDiagram\n  direction TB\n');}};
$('example').onclick=()=>{if(confirm('Substituir o rascunho pelo exemplo de pedidos?')){$('title').value='Modelo de pedidos';apply(example);}};
$('title').onchange=save;
window.addEventListener('resize',fit);
window.addEventListener('beforeunload',e=>{if(dirtyCode){e.preventDefault();e.returnValue='';}});
$('zoom-in').onclick=()=>{scale=Math.min(3,scale*1.2);zoom();};$('zoom-out').onclick=()=>{scale=Math.max(.15,scale/1.2);zoom();};$('fit').onclick=fit;
for(const b of document.querySelectorAll('[data-tab]')) b.onclick=()=>{for(const other of document.querySelectorAll('[data-tab]')) {const active=other===b;other.setAttribute('aria-pressed',String(active));$(other.dataset.tab).hidden=!active;}};
mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'base',themeVariables:{primaryColor:'#eeebff',primaryBorderColor:'#9d88e6',primaryTextColor:'#243c48',lineColor:'#66808a',fontFamily:'Segoe UI, sans-serif'},er:{useMaxWidth:false},suppressErrorRendering:true});
try{const stored=JSON.parse(localStorage.getItem(key));model=parse(stored?.source||example);if(stored?.title)$('title').value=stored.title;}catch{model=parse(example);}
rebuild();render();
})();
