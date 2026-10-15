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
