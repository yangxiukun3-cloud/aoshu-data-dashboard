from pathlib import Path

p = Path('xiaoe-staff/index.html')
s = p.read_text(encoding='utf-8')

if 'async function pollApplications()' in s:
    print('Realtime application polling already present; no change needed.')
    raise SystemExit(0)

marker = 'async function refreshCurrent(){'
timer_marker = 'setInterval(pollSupport,1000);'

if marker not in s:
    raise SystemExit('refreshCurrent marker not found')
if timer_marker not in s:
    raise SystemExit('pollSupport timer marker not found')

patch = r'''var applicationPolling=false;
async function pollApplications(){
  if(!S.user||applicationPolling||document.hidden)return;
  if(S.current!=='applications'&&S.current!=='dashboard')return;
  var drawer=$('drawer');
  if(drawer&&!drawer.classList.contains('hidden'))return;
  var ae=document.activeElement;
  if(ae&&/^(INPUT|TEXTAREA|SELECT)$/.test(ae.tagName))return;

  applicationPolling=true;
  var y=window.scrollY||0;
  var tw=document.querySelector('#applicationsPage .tablewrap');
  var sx=tw?tw.scrollLeft:0,sy=tw?tw.scrollTop:0;
  var before={};
  S.apps.forEach(function(a){before[String(a.id)]=1});

  try{
    await loadCore();
    if(S.current==='applications')renderApplications();
    loadDashboard();
    var fresh=S.apps.filter(function(a){return !a.trashed_at&&!before[String(a.id)]});
    $('cloudState').textContent='真实云端实时同步 · '+new Date().toLocaleTimeString('zh-CN',{hour12:false});
    if(fresh.length)toast('收到新申请：'+fresh[0].application_no+(fresh.length>1?' 等'+fresh.length+'笔':''));
  }catch(e){
    console.warn('application realtime poll',e);
  }finally{
    requestAnimationFrame(function(){
      window.scrollTo(0,y);
      if(tw){tw.scrollLeft=sx;tw.scrollTop=sy}
    });
    applicationPolling=false;
  }
}
'''

s = s.replace(marker, patch + marker, 1)
s = s.replace(
    timer_marker,
    timer_marker + "\nsetInterval(pollApplications,1000);\ndocument.addEventListener('visibilitychange',function(){if(!document.hidden)pollApplications()});\nwindow.addEventListener('focus',pollApplications);",
    1,
)
s = s.replace('小额周转贷 · v7.1.3', '小额周转贷 · v7.1.4', 1)
s = s.replace(
    'v7.1.3 · 回收站 · 1秒客服刷新 · GitHub Pages',
    'v7.1.4 · 回收站 · 1秒申请刷新 · 1秒客服刷新 · GitHub Pages',
    1,
)

p.write_text(s, encoding='utf-8')
print('Patched staff application list with safe 1s realtime polling.')
