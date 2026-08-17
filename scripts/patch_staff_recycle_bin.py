from pathlib import Path
import re

P = Path('xiaoe-staff/index.html')
s = P.read_text('utf-8')


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'{label} target not found')
    return text.replace(old, new, 1)


def sub_once(text, pattern, repl, label):
    out, n = re.subn(pattern, lambda _m: repl, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f'{label} target not found ({n})')
    return out

# Version markers.
s = s.replace('小额周转贷 · v7.1.2', '小额周转贷 · v7.1.3', 1)
s = s.replace('v7.1.2 · 1秒客服刷新 · GitHub Pages', 'v7.1.3 · 回收站 · 1秒客服刷新 · GitHub Pages', 1)

# Small action buttons.
s = replace_once(
    s,
    '.download-note{font-size:12px;color:#7a2e0e;margin-top:8px}',
    '.download-note{font-size:12px;color:#7a2e0e;margin-top:8px}.row-actions{display:flex;gap:6px;flex-wrap:wrap;min-width:180px}.mini-btn{border:0;border-radius:8px;padding:7px 9px;font-size:12px;font-weight:800;cursor:pointer}.mini-btn.save{background:#eef3f8;color:#314155}.mini-btn.trash{background:#fff4dd;color:#8a5b00}.mini-btn.restore{background:#eaf8ef;color:#16734b}.mini-btn.delete{background:#fff0f0;color:#b42318}',
    'action styles'
)

# Navigation: add recycle bin.
s = replace_once(
    s,
    '<button data-page="applications">申请审核</button><button data-page="support">客服聊天 <span id="supportUnread" class="nav-count hidden">0</span></button>',
    '<button data-page="applications">申请审核</button><button data-page="trash">回收站 <span id="trashCount" class="nav-count hidden">0</span></button><button data-page="support">客服聊天 <span id="supportUnread" class="nav-count hidden">0</span></button>',
    'trash nav'
)

# Applications table: add operation column and recycle-bin page.
old_apps = '<section id="applicationsPage" class="hidden"><div class="toolbar"><input id="q" placeholder="申请号 / 客户姓名 / 手机尾号"><select id="statusFilter"><option value="">全部审核状态</option><option>待人工审核</option><option>已通过</option><option>未通过</option></select><button id="searchBtn" class="btn">查询</button></div><div class="tablewrap"><table><thead><tr><th>申请号</th><th>客户</th><th>类型</th><th>申请金额</th><th>期限</th><th>审核状态</th><th>授信金额</th><th>贷款状态</th><th>打款状态</th><th>提交时间</th></tr></thead><tbody id="appRows"></tbody></table></div></section>'
new_apps = '<section id="applicationsPage" class="hidden"><div class="toolbar"><input id="q" placeholder="申请号 / 客户姓名 / 手机尾号"><select id="statusFilter"><option value="">全部审核状态</option><option>待人工审核</option><option>已通过</option><option>未通过</option></select><button id="searchBtn" class="btn">查询</button></div><div class="tablewrap"><table><thead><tr><th>申请号</th><th>客户</th><th>类型</th><th>申请金额</th><th>期限</th><th>审核状态</th><th>授信金额</th><th>贷款状态</th><th>打款状态</th><th>提交时间</th><th>操作</th></tr></thead><tbody id="appRows"></tbody></table></div></section>\n<section id="trashPage" class="hidden"><div class="notice">回收站中的申请已从客户 APP 隐藏。恢复后重新显示；永久删除不可撤销，且不会删除客户账号。</div><div class="tablewrap" style="margin-top:14px"><table><thead><tr><th>申请号</th><th>客户</th><th>申请金额</th><th>审核状态</th><th>移入时间</th><th>操作</th></tr></thead><tbody id="trashRows"></tbody></table></div></section>'
s = replace_once(s, old_apps, new_apps, 'applications table')

# State/load query must include trash metadata.
s = replace_once(
    s,
    "var appSel='id,customer_id,application_no,apply_amount,requested_term,purpose_code,status,approved_amount,approved_term,loan_status,allow_reapply,submitted_at,reviewed_at,updated_at';",
    "var appSel='id,customer_id,application_no,apply_amount,requested_term,purpose_code,status,approved_amount,approved_term,loan_status,allow_reapply,submitted_at,reviewed_at,updated_at,trashed_at,trashed_by_auth_user_id';",
    'app select fields'
)

# Page switching.
s = sub_once(
    s,
    r"function go\(page\)\{.*?\}\nasync function loadAll",
    """function go(page){S.current=page;document.querySelectorAll('.nav button').forEach(function(b){b.classList.toggle('active',b.dataset.page===page)});['dashboard','applications','trash','support','sms'].forEach(function(x){$(x+'Page').classList.toggle('hidden',x!==page)});$('pageTitle').textContent={dashboard:'仪表盘',applications:'申请审核',trash:'回收站',support:'客服聊天',sms:'短信记录'}[page];if(page==='applications')renderApplications();if(page==='trash')renderTrash();if(page==='support')loadSupport();if(page==='sms')loadSms(false)}
async function loadAll""",
    'page switch'
)

# Dashboard counts only active applications; update recycle-bin badge.
s = sub_once(
    s,
    r"function loadDashboard\(\)\{.*?\}\nfunction renderApplications\(\)\{.*?\}\nvar FIELDS=",
    """function loadDashboard(){var active=S.apps.filter(function(a){return !a.trashed_at}),pending=0,passed=0,payout=0;active.forEach(function(a){if(a.status==='待人工审核'||a.status==='待审核')pending++;if(a.status==='已通过')passed++;var p=S.payouts[String(a.id)];if(p&&(p.payout_status==='待打款'||p.payout_status==='打款处理中'))payout++});$('mTotal').textContent=active.length;$('mPending').textContent=pending;$('mPassed').textContent=passed;$('mPayout').textContent=payout;var t=S.apps.filter(function(a){return !!a.trashed_at}).length,b=$('trashCount');b.textContent=t;b.classList.toggle('hidden',t===0);updateSupportBadge()}
function renderApplications(){var query=$('q').value.trim().toLowerCase(),sf=$('statusFilter').value;var rows=S.apps.filter(function(a){if(a.trashed_at)return false;var c=S.customers[String(a.customer_id)]||{};var hay=[a.application_no,c.display_name,c.customer_key,c.phone_last4].join(' ').toLowerCase();return (!query||hay.indexOf(query)>=0)&&(!sf||a.status===sf)});$('appRows').innerHTML=rows.map(function(a){var c=S.customers[String(a.customer_id)]||{},p=S.payouts[String(a.id)]||{},typ=a.purpose_code==='SPECIAL_LOAN'?'特色贷':'普通贷款';return '<tr><td><span class=\"link\" data-open=\"'+esc(a.id)+'\">'+esc(a.application_no)+'</span></td><td>'+esc(c.display_name||c.customer_key||'客户')+'<br><span class=\"muted small\">尾号 '+esc(c.phone_last4||'—')+'</span></td><td>'+typ+'</td><td>'+money(a.apply_amount)+'</td><td>'+esc(a.requested_term)+'个月</td><td><span class=\"badge '+badgeClass(a.status)+'\">'+esc(a.status)+'</span></td><td>'+money(a.approved_amount)+'</td><td>'+esc(a.loan_status||'—')+'</td><td>'+esc(p.payout_status||'—')+'</td><td>'+dt(a.submitted_at)+'</td><td><div class=\"row-actions\"><button class=\"mini-btn save\" data-download=\"'+esc(a.id)+'\">下载保存</button><button class=\"mini-btn trash\" data-trash=\"'+esc(a.id)+'\">移入回收站</button></div></td></tr>'}).join('')||'<tr><td colspan=\"11\" class=\"muted\">暂无匹配申请</td></tr>';document.querySelectorAll('[data-open]').forEach(function(x){x.onclick=function(){openDetail(x.dataset.open)}});document.querySelectorAll('[data-download]').forEach(function(x){x.onclick=function(e){e.stopPropagation();downloadApplicationById(x.dataset.download)}});document.querySelectorAll('[data-trash]').forEach(function(x){x.onclick=function(e){e.stopPropagation();moveToTrash(x.dataset.trash)}})}
function renderTrash(){var rows=S.apps.filter(function(a){return !!a.trashed_at}).sort(function(a,b){return new Date(b.trashed_at)-new Date(a.trashed_at)});$('trashRows').innerHTML=rows.map(function(a){var c=S.customers[String(a.customer_id)]||{};return '<tr><td><span class=\"link\" data-open-trash=\"'+esc(a.id)+'\">'+esc(a.application_no)+'</span></td><td>'+esc(c.display_name||c.customer_key||'客户')+'<br><span class=\"muted small\">尾号 '+esc(c.phone_last4||'—')+'</span></td><td>'+money(a.apply_amount)+'</td><td><span class=\"badge '+badgeClass(a.status)+'\">'+esc(a.status)+'</span></td><td>'+dt(a.trashed_at)+'</td><td><div class=\"row-actions\"><button class=\"mini-btn save\" data-download-trash=\"'+esc(a.id)+'\">下载保存</button><button class=\"mini-btn restore\" data-restore=\"'+esc(a.id)+'\">恢复</button><button class=\"mini-btn delete\" data-permanent-delete=\"'+esc(a.id)+'\">永久删除</button></div></td></tr>'}).join('')||'<tr><td colspan=\"6\" class=\"muted\">回收站为空</td></tr>';document.querySelectorAll('[data-open-trash]').forEach(function(x){x.onclick=function(){openDetail(x.dataset.openTrash)}});document.querySelectorAll('[data-download-trash]').forEach(function(x){x.onclick=function(e){e.stopPropagation();downloadApplicationById(x.dataset.downloadTrash)}});document.querySelectorAll('[data-restore]').forEach(function(x){x.onclick=function(e){e.stopPropagation();restoreApplication(x.dataset.restore)}});document.querySelectorAll('[data-permanent-delete]').forEach(function(x){x.onclick=function(e){e.stopPropagation();permanentDeleteApplication(x.dataset.permanentDelete)}})}
var FIELDS=""",
    'dashboard/list rendering'
)

# Inject recycle-bin actions before support loader.
needle = 'async function loadSupport(silent)'
actions = r'''async function downloadApplicationById(id){var previous=S.detail;try{var full=await api('loan_applications?select=*&id=eq.'+encodeURIComponent(id)+'&limit=1'),a=full&&full[0];if(!a)throw new Error('申请不存在');var cr=await api('customers?select=*&id=eq.'+encodeURIComponent(a.customer_id)+'&limit=1'),c=cr&&cr[0]||S.customers[String(a.customer_id)]||{};var rs=await Promise.all([api('review_events?select=*&application_id=eq.'+a.id+'&order=created_at.desc'),api('payout_records?select=*&application_id=eq.'+a.id+'&order=id.desc')]);var pack=safeJson(a.encrypted_application,{}),custProfile=safeJson(c.encrypted_profile,{}),profile=Object.assign({},custProfile,pack.profile||{});S.detail={a:a,c:c,pack:pack,profile:profile,reviews:rs[0]||[],payouts:rs[1]||[]};exportApplication()}catch(e){toast('下载保存失败：'+e.message)}finally{S.detail=previous}}
async function moveToTrash(id){var a=S.apps.find(function(x){return String(x.id)===String(id)});if(!a)return;if(!confirm('确认将申请 '+a.application_no+' 移入回收站？\n移入后客户 APP 将不再显示这笔申请。'))return;var now=new Date().toISOString();try{await api('loan_applications?id=eq.'+encodeURIComponent(id),{method:'PATCH',body:{trashed_at:now,trashed_by_auth_user_id:S.user&&S.user.id?S.user.id:null,updated_at:now}});await bestEffortAudit('MOVE_APPLICATION_TO_TRASH',a.application_no,{application_id:a.id,customer_id:a.customer_id});toast('已移入回收站');await loadCore();renderApplications();renderTrash();loadDashboard()}catch(e){toast('移入回收站失败：'+e.message)}}
async function restoreApplication(id){var a=S.apps.find(function(x){return String(x.id)===String(id)});if(!a)return;if(!confirm('确认恢复申请 '+a.application_no+'？\n恢复后客户 APP 将重新显示这笔申请。'))return;var now=new Date().toISOString();try{await api('loan_applications?id=eq.'+encodeURIComponent(id),{method:'PATCH',body:{trashed_at:null,trashed_by_auth_user_id:null,updated_at:now}});await bestEffortAudit('RESTORE_APPLICATION_FROM_TRASH',a.application_no,{application_id:a.id,customer_id:a.customer_id});toast('申请已恢复');await loadCore();renderApplications();renderTrash();loadDashboard()}catch(e){toast('恢复失败：'+e.message)}}
async function permanentDeleteApplication(id){var a=S.apps.find(function(x){return String(x.id)===String(id)});if(!a||!a.trashed_at){toast('只有回收站中的申请才能永久删除');return}if(!confirm('永久删除申请 '+a.application_no+'？\n该操作不可撤销，将删除这笔申请的业务关联记录，但不会删除客户账号。'))return;var verify=prompt('为防止误删，请输入“永久删除”四个字确认：');if(verify!=='永久删除'){toast('已取消永久删除');return}try{var q=encodeURIComponent(id);await api('repayment_events?application_id=eq.'+q,{method:'DELETE'});await api('repayment_plans?application_id=eq.'+q,{method:'DELETE'});await api('fund_exceptions?application_id=eq.'+q,{method:'DELETE'});await api('file_records?application_id=eq.'+q,{method:'DELETE'});await api('payout_records?application_id=eq.'+q,{method:'DELETE'});await api('review_events?application_id=eq.'+q,{method:'DELETE'});await api('sms_outbox?application_id=eq.'+q,{method:'DELETE'});await api('support_messages?application_id=eq.'+q,{method:'DELETE'});await api('system_messages?application_id=eq.'+q,{method:'DELETE'});await api('loan_applications?id=eq.'+q,{method:'DELETE'});await bestEffortAudit('PERMANENT_DELETE_APPLICATION',a.application_no,{application_id:a.id,customer_id:a.customer_id,customer_account_deleted:false});toast('申请已永久删除；客户账号保留');await loadCore();renderApplications();renderTrash();loadDashboard()}catch(e){toast('永久删除未完成：'+e.message+'。申请仍保留在回收站，可再次执行。')}}
'''
if needle not in s:
    raise SystemExit('support loader insertion target not found')
s = s.replace(needle, actions + needle, 1)

# Refresh behavior includes trash page.
s = replace_once(
    s,
    "async function refreshCurrent(){await loadAll();if(S.current==='applications')renderApplications();if(S.current==='support')renderThreads();if(S.current==='sms')await loadSms(false)}",
    "async function refreshCurrent(){await loadAll();if(S.current==='applications')renderApplications();if(S.current==='trash')renderTrash();if(S.current==='support')renderThreads();if(S.current==='sms')await loadSms(false)}",
    'refresh trash'
)

# Startup/list refresh should update trash count/page when relevant.
s = replace_once(
    s,
    "await Promise.all([loadCore(),loadSupport(true),loadSms(true)]);renderApplications();loadDashboard();",
    "await Promise.all([loadCore(),loadSupport(true),loadSms(true)]);renderApplications();renderTrash();loadDashboard();",
    'load all trash render'
)

# Sanity checks.
for marker in ['data-page="trash"','id="trashRows"','data-trash','data-restore','data-permanent-delete','MOVE_APPLICATION_TO_TRASH','PERMANENT_DELETE_APPLICATION','trashed_at']:
    if marker not in s:
        raise SystemExit('missing marker: '+marker)

P.write_text(s, encoding='utf-8')
print('Patched staff backend with download, recycle bin, restore, and permanent delete.')
