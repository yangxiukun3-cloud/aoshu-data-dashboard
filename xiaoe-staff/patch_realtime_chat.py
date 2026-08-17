from pathlib import Path

p = Path('xiaoe-staff/index.html')
s = p.read_text('utf-8')

old_state = "var S={jwt:null,user:null,staff:null,apps:[],customers:{},payouts:{},support:[],threadKey:null,current:'dashboard',detail:null};"
new_state = "var S={jwt:null,user:null,staff:null,apps:[],customers:{},payouts:{},support:[],threadKey:null,current:'dashboard',detail:null,supportPolling:false,lastSupportId:0};"
if old_state not in s:
    raise SystemExit('state target not found')
s = s.replace(old_state, new_state, 1)

old_load = "async function loadSupport(silent){try{var rows=await api('support_messages?select=id,customer_id,application_id,sender_type,sender_auth_user_id,content,read_by_customer_at,read_by_staff_at,created_at&order=created_at.desc&limit=500');S.support=rows||[];updateSupportBadge();if(!silent)renderThreads();return S.support}catch(e){if(!silent)toast('客服消息加载失败：'+e.message);return []}}"
new_load = "async function loadSupport(silent){try{var rows=await api('support_messages?select=id,customer_id,application_id,sender_type,sender_auth_user_id,content,read_by_customer_at,read_by_staff_at,created_at&order=created_at.desc&limit=500');S.support=rows||[];S.lastSupportId=S.support.reduce(function(m,x){return Math.max(m,Number(x.id)||0)},0);updateSupportBadge();if(!silent)renderThreads();return S.support}catch(e){if(!silent)toast('客服消息加载失败：'+e.message);return []}}"
if old_load not in s:
    raise SystemExit('loadSupport target not found')
s = s.replace(old_load, new_load, 1)

marker = "function updateSupportBadge(){var n=S.support.filter(function(m){return m.sender_type==='customer'&&!m.read_by_staff_at}).length;$('mSupport').textContent=n;var b=$('supportUnread');b.textContent=n;b.classList.toggle('hidden',n===0)}"
if marker not in s:
    raise SystemExit('support badge marker not found')
poll_code = marker + "\nasync function pollSupport(){if(S.current!=='support'||S.supportPolling||!S.user)return;S.supportPolling=true;try{var last=Number(S.lastSupportId)||0;var rows=await api('support_messages?select=id,customer_id,application_id,sender_type,sender_auth_user_id,content,read_by_customer_at,read_by_staff_at,created_at&id=gt.'+last+'&order=id.asc&limit=200');if(rows&&rows.length){var seen={};S.support.forEach(function(x){seen[String(x.id)]=1});rows.forEach(function(x){if(!seen[String(x.id)])S.support.push(x);S.lastSupportId=Math.max(S.lastSupportId,Number(x.id)||0)});updateSupportBadge();renderThreads();if(S.threadKey)await openThread(S.threadKey)}}catch(e){console.warn('support poll',e)}finally{S.supportPolling=false}}"
s = s.replace(marker, poll_code, 1)

old_send = "async function sendReply(){if(!S.threadKey)return;var text=$('replyText').value.trim();if(!text)return;var parts=S.threadKey.split('|'),cid=Number(parts[0]),aid=parts[1]?Number(parts[1]):null;try{await api('support_messages',{method:'POST',body:{customer_id:cid,application_id:aid,sender_type:'staff',sender_auth_user_id:S.user.id,content:text}});$('replyText').value='';await loadSupport(false);await openThread(S.threadKey)}catch(e){toast('客服回复发送失败：'+e.message)}}"
new_send = "async function sendReply(){if(!S.threadKey)return;var text=$('replyText').value.trim();if(!text)return;var parts=S.threadKey.split('|'),cid=Number(parts[0]),aid=parts[1]?Number(parts[1]):null;try{$('replyBtn').disabled=true;var created=await api('support_messages',{method:'POST',body:{customer_id:cid,application_id:aid,sender_type:'staff',sender_auth_user_id:S.user.id,content:text}});$('replyText').value='';if(created&&created[0]){var row=created[0],exists=S.support.some(function(x){return String(x.id)===String(row.id)});if(!exists)S.support.push(row);S.lastSupportId=Math.max(S.lastSupportId,Number(row.id)||0);updateSupportBadge();renderThreads();await openThread(S.threadKey)}else{await pollSupport()}}catch(e){toast('客服回复发送失败：'+e.message)}finally{$('replyBtn').disabled=false}}"
if old_send not in s:
    raise SystemExit('sendReply target not found')
s = s.replace(old_send, new_send, 1)

old_bottom = "$('loginBtn').onclick=login;$('password').onkeydown=function(e){if(e.key==='Enter')login()};$('logoutBtn').onclick=logout;$('refreshBtn').onclick=refreshCurrent;$('searchBtn').onclick=renderApplications;$('q').oninput=renderApplications;$('statusFilter').onchange=renderApplications;$('closeDrawerBtn').onclick=closeDrawer;$('exportBtn').onclick=exportApplication;$('replyBtn').onclick=sendReply;$('viewer').onclick=function(e){if(e.target===$('viewer')||e.target.tagName==='IMG')$('viewer').classList.add('hidden')};document.querySelectorAll('.nav button').forEach(function(b){b.onclick=function(){go(b.dataset.page)}});"
new_bottom = old_bottom + "\nsetInterval(pollSupport,1000);"
if old_bottom not in s:
    raise SystemExit('bottom binding target not found')
s = s.replace(old_bottom, new_bottom, 1)

s = s.replace('小额周转贷 · v7.1.1', '小额周转贷 · v7.1.2', 1)
s = s.replace('v7.1.1 · GitHub Pages', 'v7.1.2 · 1秒客服刷新 · GitHub Pages', 1)

p.write_text(s, encoding='utf-8')
print('patched staff chat: 1s incremental polling + optimistic staff reply')
