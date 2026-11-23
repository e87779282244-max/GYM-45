# Завершение тренировки: «Завершить ✓» с неотмеченными подходами спрашивает и сохраняет; после сохранения — заминка;
# после замены упражнения тренировка остаётся активной («Продолжить», «Завершить программу» работает).
# Запуск: python3 tests/finish_cool_check.py index.html
import asyncio,re,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
R=[]
HELP=re.search(r'HELP="""(.*?)"""',open('tests/g2_waves_check.py',encoding='utf-8').read(),re.S).group(1)
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def start(b):
  pg=await b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
  await pg.evaluate("(()=>{const p=auAll().find(q=>q.id==='wl');auPlanStart(p,auPlanNext(p)||{w:0,d:0});})()");await pg.wait_for_timeout(200)
  await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(300)
  await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>{s.done=!s.warm;s.w=s.w||20;s.r=s.r||10}))")
  return pg,errs
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    pg,errs=await start(b);E=pg.evaluate
    await E("const se=current.sets[current.sets.length-1];se.filter(s=>!s.warm)[0].done=false;current.idx=current.sets.length-1;saveDraft();renderWorkout()")
    await E("el('wkNext').click()");await pg.wait_for_timeout(200)
    ok('«Завершить ✓» с неотмеченным подходом — вопрос, а не молчаливый переход',await E("currentScreen==='workout'&&!el('gvtModal').hidden&&!!el('wkFinY')"),await E("el('gvtMbox').innerText.slice(0,80)"))
    await E("el('wkFinN').click()");ok('«Вернуться» — остаёмся в тренировке',await E("el('gvtModal').hidden&&!!current&&currentScreen==='workout'"))
    await E("el('wkNext').click()");await pg.wait_for_timeout(150);await E("el('wkFinY').click()");await pg.wait_for_timeout(900)
    ok('«Завершить и сохранить» — сохранено, предложена заминка',await E("!current&&!el('coolModal').hidden&&!!el('coolGo')"))
    await pg.close()
    pg,errs2=await start(b);E=pg.evaluate
    await E("current.program.ex[0][0]='Жим гантелей лёжа';saveDraft();dayView={p:current.program,computed:true};renderDay();show('day')");await pg.wait_for_timeout(150)
    ok('после замены упражнения обзор дня: «Продолжить программу»',await E("el('dayStart').textContent")=='Продолжить программу')
    await E("el('dayFinish').click()");await pg.wait_for_timeout(900)
    ok('«Завершить программу» сохраняет и предлагает заминку',await E("!current&&!el('coolModal').hidden"))
    # GVT: часть подходов не отмечена, программа «изменилась» (замена упражнения / облегчение после перерыва)
    pg3=await b.new_page(viewport={'width':390,'height':844});errs3=[];pg3.on('pageerror',lambda e:errs3.append(str(e)));E=pg3.evaluate
    await pg3.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg3.wait_for_timeout(300);await E("el('login').style.display='none'")
    await E(HELP);await E("(()=>{T.fresh(0,{});return T.open()||(()=>{const m=el('gvtModal');if(!m.hidden&&el('g2c6Go')){el('g2c6Go').click();return T.begin();}return 'no'})()})()")
    await E("el('gvtModal').hidden=true;current.sets.forEach(ss=>ss.forEach(s=>{s.w=s.w||60;s.pw=s.pw||60;s.done=true}));current.sets[current.sets.length-1][0].done=false;")
    await E("const P2=JSON.parse(JSON.stringify(current.program));P2.ex[0][0]='Жим гантелей лёжа';P2.focus+=' · после перерыва −15 %';dayView={p:P2,computed:true};current.idx=current.program.g2.units.length-1;saveDraft();show('workout');renderWorkout()");await pg3.wait_for_timeout(300)
    await E("el('wkNext').click()");await pg3.wait_for_timeout(200)
    ok('GVT: «Завершить ✓» с неотмеченным — вопрос',await E("!el('gvtModal').hidden&&!!el('wkFinY')"))
    await E("el('wkFinN').click();renderDay();show('day')");await pg3.wait_for_timeout(150)
    ok('GVT: обзор дня — «Продолжить программу», а не новая тренировка',await E("el('dayStart').textContent")=='Продолжить программу')
    await E("el('dayStart').click()");await pg3.wait_for_timeout(200)
    ok('GVT: «Продолжить» — та же тренировка, без «Отложить и начать»',await E("currentScreen==='workout'&&el('gvtModal').hidden"))
    await E("renderDay();show('day');el('dayFinish').click()");await pg3.wait_for_timeout(1200)
    ok('GVT: «Завершить программу» сохраняет и предлагает заминку',await E("!current&&!el('coolModal').hidden"),await E("[!!current,el('coolModal').hidden,currentScreen]"))
    ok('без ошибок JS',not errs and not errs2 and not errs3,(errs+errs2+errs3)[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
