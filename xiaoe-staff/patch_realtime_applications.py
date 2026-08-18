from pathlib import Path
import re
import subprocess
import tempfile

BASE_COMMIT = '23ea8551a2218504b3d8a9d5ef0881bebbf1778d'
TARGET = Path('xiaoe-staff/index.html')

# Rebuild from the last known-good v7.1.3 staff page so login/auth behavior stays unchanged.
s = subprocess.check_output(
    ['git', 'show', f'{BASE_COMMIT}:xiaoe-staff/index.html'],
    text=True,
    encoding='utf-8'
)

marker = 'async function refreshCurrent(){'
timer_marker = 'setInterval(pollSupport,1000);'
if marker not in s:
    raise SystemExit('refreshCurrent marker not found in known-good base')
if timer_marker not in s:
    raise SystemExit('pollSupport timer marker not found in known-good base')

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
s = s.replace('</body>', '<!--staff-v714-known-good-login-rebuild:20260818-1016-->\n</body>', 1)

# Validate the exact inline JavaScript before the live staff page can be replaced.
m = re.search(r'<script>([\s\S]*?)</script>', s)
if not m:
    raise SystemExit('main inline script not found')
with tempfile.NamedTemporaryFile('w', suffix='.js', encoding='utf-8', delete=False) as f:
    f.write(m.group(1))
    js_path = f.name
subprocess.run(['node', '--check', js_path], check=True)

TARGET.write_text(s, encoding='utf-8')
print('Rebuilt v7.1.4 from known-good v7.1.3; login code preserved; JS syntax check passed.')
