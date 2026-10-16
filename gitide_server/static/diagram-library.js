(()=>{
const folder='.documents/diagramas/';let revision=0;
const $=id=>document.getElementById(id);
async function refresh(){const current=++revision,project=state.activeProjectId,rows=$('diagram-rows');rows.replaceChildren();$('diagram-create').disabled=!project;
 if(!project){$('diagram-status').textContent='Selecione um projeto para visualizar seus diagramas.';return;}
 $('diagram-status').textContent='Carregando…';
 try{const response=await fetch('/api/projects/'+project+'/files',{headers:getHeaders()});if(!response.ok)throw Error('Não foi possível listar os diagramas ('+response.status+').');const data=await response.json();if(current!==revision)return;
 const files=data.files.filter(f=>f.path.startsWith(folder)&&f.path.endsWith('.mmd')).sort((a,b)=>a.path.localeCompare(b.path));$('diagram-status').textContent=files.length?files.length+' diagrama(s)':'Nenhum diagrama salvo neste projeto.';
 for(const file of files){const tr=document.createElement('tr');for(const text of [file.path.slice(folder.length),new Date(file.last_modified).toLocaleString('pt-BR')]){const td=document.createElement('td');td.textContent=text;td.style.padding='14px 0';tr.append(td);}const td=document.createElement('td'),link=document.createElement('a');link.className='btn btn-secondary';link.textContent='Abrir no editor';link.href='/diagrams?project='+encodeURIComponent(project)+'&file='+encodeURIComponent(file.path);td.append(link);const remove=document.createElement('button');remove.className='btn btn-secondary';remove.textContent='Excluir';remove.style.marginLeft='12px';remove.onclick=async()=>{if(!confirm('Excluir o diagrama '+file.path.slice(folder.length)+' do projeto?'))return;remove.disabled=true;try{const response=await fetch('/api/projects/'+project+'/files/delete?filepath='+encodeURIComponent(file.path),{method:'DELETE',headers:getHeaders()});if(!response.ok)throw Error('Não foi possível excluir ('+response.status+').');await refresh();}catch(e){$('diagram-status').textContent=e.message;remove.disabled=false;}};td.append(remove);tr.append(td);rows.append(tr);}
 }catch(e){if(current===revision)$('diagram-status').textContent=e.message;}
}
$('diagram-refresh').onclick=refresh;
$('diagram-create').onclick=()=>{if(state.activeProjectId)location.href='/diagrams?project='+encodeURIComponent(state.activeProjectId)+'&new=1';};
document.querySelector('[data-tab="tab-diagrams"]').addEventListener('click',refresh);
window.addEventListener('gitide:active-project-changed',()=>{if(state.activeProjectId&&location.hash==='#diagramas')switchTab('tab-diagrams');refresh();});
if(state.activeProjectId&&location.hash==='#diagramas'){switchTab('tab-diagrams');refresh();}
})();
