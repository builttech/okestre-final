/* Desktop adaptation of the existing terminal; all original pages remain intact. */
(()=>{
 async function request(data){const r=await fetch('/desktop/action',{method:'POST',headers:{'Content-Type':'application/json','X-Desktop-Key':window.OKESTRE_DESKTOP_KEY},body:JSON.stringify(data)});const v=await r.json();if(!v.ok)throw Error(v.error||v.detail);return v.data;}
 document.addEventListener('submit',async e=>{
  if(e.target.id!=='terminal-form')return;e.preventDefault();e.stopImmediatePropagation();
  if(typeof state==='undefined'||!state.activeProjectId)return;
  const input=document.getElementById('terminal-input'),command=input.value.trim(),project_id=state.activeProjectId;if(!command)return;input.value='';
  const output=document.getElementById('terminal-output'),block=document.createElement('div'),title=document.createElement('div'),text=document.createElement('pre'),stop=document.createElement('button');title.textContent='$ '+command;stop.textContent='Encerrar processo';block.append(title,text,stop);output.append(block);stop.hidden=true;
  try{let job=await request({action:'execute',project_id,command});let timer;
   const show=()=>{text.textContent=(job.output||'')+'\n['+job.status+(job.exit_code===null?'':'; código '+job.exit_code)+']';stop.hidden=job.status!=='running';};show();
   stop.onclick=async()=>{try{job=await request({action:'stop',project_id,command_id:job.command_id});clearTimeout(timer);show();}catch(e){text.textContent=e.message;}};
   const poll=async()=>{if(job.status!=='running')return;try{job=await request({action:'poll',project_id,command,command_id:job.command_id});show();if(job.status==='running')timer=setTimeout(poll,1500);}catch(e){text.textContent=e.message;}};if(job.status==='running')timer=setTimeout(poll,1500);
  }catch(e){text.textContent=e.message;}
 },true);
})();

/* QA extension pairing is limited to this running Desktop session. */
(()=>{
 const panel=document.getElementById('tab-qa');if(!panel)return;
 const card=document.createElement('section');card.className='desktop-qa-pairing';
 const heading=document.createElement('h3');heading.textContent='Extensão QA · conexão local';
 const help=document.createElement('p');help.textContent='Gere um código e cole na extensão. Autoriza anotações e revisão de texto por IA nos projetos locais. Sem limite de tempo; a conexão termina ao revogar ou fechar o Desktop.';
 const issue=document.createElement('button');issue.className='btn btn-primary';issue.textContent='Gerar código de pareamento';issue.id='desktop-qa-pair';
 const revoke=document.createElement('button');revoke.className='btn btn-secondary';revoke.textContent='Revogar conexões QA';revoke.id='desktop-qa-revoke';
 const output=document.createElement('textarea');output.id='desktop-qa-code';output.readOnly=true;output.hidden=true;output.style.cssText='width:100%;margin-top:12px;min-height:80px';output.setAttribute('aria-label','Código para colar na extensão QA');
 const status=document.createElement('p');status.id='desktop-qa-status';status.setAttribute('role','status');
 async function action(name){const r=await fetch('/desktop/action',{method:'POST',headers:{'Content-Type':'application/json','X-Desktop-Key':window.OKESTRE_DESKTOP_KEY},body:JSON.stringify({action:name})});const v=await r.json();if(!r.ok||!v.ok)throw Error(v.error||v.detail||'Falha no pareamento.');return v.data;}
 issue.onclick=async()=>{try{const v=await action('qa_pair');output.value=JSON.stringify(v.pairing);output.hidden=false;output.select();status.textContent='Copie o código para a extensão. Sem expiração por tempo e válido para um único pareamento.';}catch(e){status.textContent=e.message;}};
 revoke.onclick=async()=>{try{await action('qa_revoke');output.value='';output.hidden=true;status.textContent='Conexões QA revogadas.';}catch(e){status.textContent=e.message;}};
 card.append(heading,help,issue,revoke,output,status);
 const sidebar=panel.querySelector('.qa-side');if(!sidebar)return;sidebar.append(card);
 panel.classList.add('desktop-qa');
 const style=document.createElement('style');style.textContent=`
 #tab-qa.desktop-qa>.qa-layout{width:100%;min-width:0;grid-template-columns:minmax(0,1fr) 340px;align-items:start}
 #tab-qa.desktop-qa .qa-main{min-width:0}
 #tab-qa.desktop-qa .qa-side{padding:20px!important;min-width:0}
 #tab-qa.desktop-qa .qa-extension-box,#tab-qa.desktop-qa #btn-qa-copy-extension-config{display:none!important}
 #tab-qa.desktop-qa .desktop-qa-pairing{margin-top:20px;padding-top:20px;border-top:1px solid var(--border-color,#303030)}
 #tab-qa.desktop-qa .desktop-qa-pairing h3{font-size:15px;margin:0 0 10px}
 #tab-qa.desktop-qa .desktop-qa-pairing p{font-size:12px;line-height:1.6;margin:10px 0 16px;color:var(--text-secondary,#a0aabc)}
 #tab-qa.desktop-qa .desktop-qa-pairing button{display:block;width:100%;margin-top:10px;min-height:36px}
 #tab-qa.desktop-qa #desktop-qa-code{box-sizing:border-box;background:var(--bg-primary,#101010);color:var(--text-primary,#eee);border:1px solid var(--border-color,#444);padding:10px;font-size:12px;resize:vertical}
 #tab-qa.desktop-qa .qa-toolbar{flex-wrap:wrap;gap:12px}
 #tab-qa.desktop-qa .qa-toolbar-left{flex-wrap:wrap;min-width:0}
 @media(max-width:1100px){#tab-qa.desktop-qa>.qa-layout{grid-template-columns:minmax(0,1fr)}#tab-qa.desktop-qa .qa-side{width:auto}}
 `;document.head.append(style);
})();
