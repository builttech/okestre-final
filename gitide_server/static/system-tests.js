(()=>{
const $=id=>document.getElementById(id),paths=['.documents/test/test.md','.documents/test/test.details.md'];
const states=['Não executado','Em execução','Aprovado','Reprovado','Bloqueado'];
let project=null,source=['',''],items=[],opened=null,dirty=false,loading=false,revision=0,returnFocus=null;
const mask=s=>s.replace(/<!--[\s\S]*?-->/g,m=>m.replace(/[^\n]/g,' '));
const field=(body,name)=>{const line=body.split('\n').find(l=>l.startsWith('- **'+name+':**'));return line?line.split(':**').slice(1).join(':**').trim():'';};
function sections(text){const matches=[...mask(text).matchAll(/^# (TEST-E2E-\d+)\s+[—–-]\s+(.+)$/gm)];return matches.map((m,i)=>({id:m[1],title:m[2],start:m.index,end:matches[i+1]?.index??text.length,body:text.slice(m.index+m[0].length,matches[i+1]?.index??text.length).trim()}));}
function parse(){const details=sections(source[1]);items=[...mask(source[0]).matchAll(/^- \[([ xX])\] (TEST-E2E-\d+): (.+)$/gm)].map(m=>{const detail=details.find(d=>d.id===m[2]);const body=detail?.body||'';return {id:m[2],title:m[3],status:field(body,'Status')||(m[1].toLowerCase()==='x'?'Aprovado':'Não executado'),task:field(body,'Task relacionada'),rf:field(body,'RF / Requisito'),body};});}
async function request(path,options={},target=project){const response=await fetch('/api/projects/'+target+'/files/'+path,{...options,headers:getHeaders()});if(!response.ok){const e=Error('Falha ao acessar testes ('+response.status+').');e.status=response.status;throw e;}return response.json();}
async function read(path,target=project){try{return (await request('read?filepath='+encodeURIComponent(path),{},target)).content;}catch(e){if(e.status===404)return '';throw e;}}
function render(){const rows=$('e2e-rows');rows.replaceChildren();const search=$('e2e-search').value.toLowerCase(),filter=$('e2e-filter').value;const filtered=items.filter(t=>(!filter||t.status===filter)&&[t.id,t.title,t.task,t.rf].join(' ').toLowerCase().includes(search));
$('e2e-summary').textContent=items.length+' testes · '+items.filter(t=>t.status==='Aprovado').length+' aprovados · '+items.filter(t=>t.status==='Reprovado').length+' reprovados · '+items.filter(t=>t.status==='Bloqueado').length+' bloqueados';
for(const t of filtered){const tr=document.createElement('tr');for(const value of [t.id+' — '+t.title,[t.task,t.rf].filter(Boolean).join(' / ')||'Não vinculado',t.status]){const td=document.createElement('td');td.textContent=value;tr.append(td);}const td=document.createElement('td'),button=document.createElement('button');button.className='btn btn-secondary';button.textContent='Detalhes';button.onclick=()=>open(t);td.append(button);tr.append(td);rows.append(tr);}
if(!filtered.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=4;td.textContent=items.length?'Nenhum teste corresponde ao filtro.':'Nenhum teste cadastrado. Crie o primeiro cenário após a implementação.';tr.append(td);rows.append(tr);}}
async function load(){if(dirty&&!confirm('Descartar alterações não salvas do teste?'))return;close(true);const current=++revision;project=state.activeProjectId;items=[];render();$('e2e-new').disabled=true;if(!project){$('e2e-message').textContent='Selecione um projeto.';return;}loading=true;$('e2e-message').textContent='Carregando testes…';try{const data=await Promise.all(paths.map(path=>read(path)));if(current!==revision)return;source=data;parse();render();$('e2e-message').textContent='Documentos: .documents/test/test.md e test.details.md';$('e2e-new').disabled=false;}catch(e){if(current===revision)$('e2e-message').textContent=e.message;}finally{if(current===revision)loading=false;}}
const defaultBody=`- **Objetivo:**
- **Ambiente / Versão:**
- **Pré-condições:**
- **Massa de dados:**
- **Passos:**
  1. 
- **Resultado esperado:**
- **Resultado obtido:** Não executado.
- **Evidências:**
- **Defeito / Task de correção:**
- **Responsável:**
- **Executado em:**
- **Histórico de execuções:**
  - Planejado; execução pendente.`;
function open(t){if(loading||!project)return;returnFocus=document.activeElement;opened=t||{id:'TEST-E2E-'+String(Math.max(0,...items.map(i=>Number(i.id.split('-').pop())),...sections(source[1]).map(i=>Number(i.id.split('-').pop())))+1).padStart(3,'0'),title:'',status:states[0],task:'',rf:'',body:defaultBody};$('e2e-id').textContent=opened.id;$('e2e-title').value=opened.title;$('e2e-status').value=states.includes(opened.status)?opened.status:states[0];$('e2e-task').value=opened.task;$('e2e-rf').value=opened.rf;$('e2e-details').value=opened.body.split('\n').filter(l=>!/^[-] \*\*(Status|Task relacionada|RF \/ Requisito):\*\*/.test(l)).join('\n').trim()||defaultBody;$('e2e-save-message').textContent='';dirty=false;$('e2e-drawer').classList.add('is-open');$('e2e-backdrop').classList.add('is-open');$('e2e-drawer').setAttribute('aria-hidden','false');$('e2e-title').focus();}
function close(force=false){if(dirty&&!force&&!confirm('Descartar alterações não salvas?'))return;dirty=false;opened=null;$('e2e-drawer').classList.remove('is-open');$('e2e-backdrop').classList.remove('is-open');$('e2e-drawer').setAttribute('aria-hidden','true');returnFocus?.focus();}
$('e2e-form').oninput=()=>dirty=true;
$('e2e-form').onsubmit=async event=>{event.preventDefault();if(!opened)return;const title=$('e2e-title').value.trim(),status=$('e2e-status').value,body=$('e2e-details').value.trim(),task=$('e2e-task').value.trim(),rf=$('e2e-rf').value.trim(),id=opened.id;
if(!title||/[\r\n]/.test(title+task+rf))return;
if(status==='Aprovado'&&(!field(body,'Evidências')||!field(body,'Resultado obtido')||field(body,'Resultado obtido')==='Não executado.')){$('e2e-save-message').textContent='Para aprovar, registre o resultado obtido e as evidências.';return;}
$('e2e-save').disabled=true;let wroteDetails=false;const saveProject=project;
try{if(project!==state.activeProjectId)throw Error('O projeto foi alterado. Reabra o teste no projeto correto.');const current=await Promise.all(paths.map(path=>read(path)));if(current.some((s,i)=>s!==source[i]))throw Error('Os documentos foram alterados por outra operação. Copie seu texto e atualize a lista antes de salvar.');
const line='- ['+(status==='Aprovado'?'x':' ')+'] '+id+': '+title;const match=[...mask(source[0]).matchAll(/^- \[[ xX]\] (TEST-E2E-\d+): .+$/gm)].find(m=>m[1]===id);const list=match?source[0].slice(0,match.index)+line+source[0].slice(match.index+match[0].length):(source[0]||'# Test List\n').trimEnd()+'\n\n'+line+'\n';
const section='# '+id+' — '+title+'\n- **Status:** '+status+'\n- **Task relacionada:** '+task+'\n- **RF / Requisito:** '+rf+'\n'+body+'\n\n';const old=sections(source[1]).find(t=>t.id===id);const details=old?source[1].slice(0,old.start)+section+source[1].slice(old.end):(source[1]||'# Test Details\n').trimEnd()+'\n\n'+section;
await request('write',{method:'POST',body:JSON.stringify({filepath:paths[1],content:details})},saveProject);wroteDetails=true;await request('write',{method:'POST',body:JSON.stringify({filepath:paths[0],content:list})},saveProject);if(project!==saveProject)return;source=[list,details];parse();render();close(true);$('e2e-message').textContent=id+' salvo no projeto.';
}catch(e){$('e2e-save-message').textContent=(wroteDetails?'O detalhe foi salvo, mas a lista não. Atualize os documentos antes de tentar novamente. ':'')+e.message;}finally{$('e2e-save').disabled=false;}};
$('e2e-new').onclick=()=>open();$('e2e-refresh').onclick=load;$('e2e-close').onclick=()=>close();$('e2e-backdrop').onclick=()=>close();$('e2e-search').oninput=render;$('e2e-filter').onchange=render;
window.loadSystemTests=load;
window.addEventListener('gitide:active-project-changed',()=>{if(project===state.activeProjectId)return;revision++;close(true);if(state.activeTab==='tab-system-tests')load();else{project=null;items=[];render();}});
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
document.addEventListener('keydown',e=>{if(!$('e2e-drawer').classList.contains('is-open'))return;if(e.key==='Escape')close();if(e.key==='Tab'){const controls=[...$('e2e-drawer').querySelectorAll('button,input,select,textarea')].filter(el=>!el.disabled);const first=controls[0],last=controls.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}});
})();
