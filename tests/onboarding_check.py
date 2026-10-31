# Первый запуск: анкета (цель, опыт, дни) → рекомендация и открытие программы; не показывается тем, у кого уже есть данные.
# Запуск: python3 tests/onboarding_check.py index.html [папка_скриншотов]
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);O=sys.argv[2] if len(sys.argv)>2 else None;tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2);await ctx.add_init_script("window.__onbTest=1");pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'");await pg.wait_for_timeout(1600)
    ok('новый человек — анкета открылась',await pg.evaluate("!el('onb').hidden&&el('onb').textContent.includes('Какая цель')"))
    if O:await pg.screenshot(path=O+'/o1.png')
    await pg.click('.onb-o[data-v=mass]');await pg.click('.onb-o[data-v=\"1\"]')
    if O:await pg.screenshot(path=O+'/o2.png')
    await pg.click('.onb-o[data-v=\"4\"]');await pg.wait_for_timeout(100)
    ok('масса · средний · 4 дня → «Штурм без пощады»',await pg.evaluate("el('onb').querySelector('h2').textContent.startsWith('Штурм без пощады')"),await pg.evaluate("el('onb').querySelector('h2').textContent"))
    if O:await pg.screenshot(path=O+'/o3.png')
    await pg.click('#onbGo');await pg.wait_for_timeout(300)
    ok('программа открыта',await pg.evaluate("el('onb').hidden&&currentScreen!=='home'"),await pg.evaluate("currentScreen"))
    ok('анкета сохранена',await pg.evaluate("onbSt().goal==='mass'&&onbSt().days==='4'"))
    # все сочетания дают существующие программы
    bad=await pg.evaluate("""(()=>{const bad=[];['mass','str','cut','fit'].forEach(g=>['0','1','2'].forEach(e=>['2','3','4','5','6'].forEach(d=>{onbPick({goal:g,exp:e,days:d}).forEach(([id])=>{const I=onbInfo(id);if(I.name===id)bad.push(g+e+d+':'+id);});})));return bad;})()""")
    ok('все 60 вариантов ведут на существующие программы',not bad,bad[:5])
    # открытие всех типов программ без ошибок
    for pid in ['pl5','tx','w531','cj','gvt','fbn','hiit','pbx2']:
      await pg.evaluate(f"onbGo('{pid}')");await pg.wait_for_timeout(150)
    ok('все рекомендации открываются без ошибок',not errs,errs[:3])
    await pg.reload();await pg.wait_for_timeout(2000)
    ok('второй раз сам не показывается',await pg.evaluate("el('onb').hidden"))
    await pg.evaluate("show('programs');el('onbAgain').click()")
    ok('можно пройти заново из «Программ»',await pg.evaluate("!el('onb').hidden"))
    await pg.click('.onb-skip')
    # у кого есть история — не показывается
    ctx2=await b.new_context();await ctx2.add_init_script("window.__onbTest=1");pg2=await ctx2.new_page()
    await pg2.goto(URL);await pg2.evaluate("safe.set([{date:'2026-10-01',name:'A',log:{}}]);localStorage.removeItem('gym45_onb_v1')");await pg2.reload();await pg2.wait_for_timeout(300);await pg2.evaluate("el('login').style.display='none'");await pg2.wait_for_timeout(1600)
    ok('с историей тренировок анкета не появляется',await pg2.evaluate("el('onb').hidden"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
