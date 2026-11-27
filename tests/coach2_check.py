# Подсказки, этап 2: описание у всех программ; плашка «Как делать» до первого подхода; переключатель в профиле (таймеры остаются);
# «после отказа добил» в Blood & Guts → история и «Прошлый раз»; цепочка «растяжка → отдых» после сворачивания идёт от конца растяжки.
# Запуск: python3 tests/coach2_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
SHOT=os.environ.get('SHOT')
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(400);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    miss=await E("auAll().filter(q=>!AU_GUIDE[q.id]).map(q=>q.id)")
    ok('у всех программ есть «Описание программы»',not miss,miss)
    bad=await E("""auAll().filter(q=>{authOpen(q);if(el('progGuideBtn').hidden)return true;el('progGuideBtn').click();const t=el('guideBody').innerText;el('guideClose').click();return !(t.length>350&&/Как делать/.test(t));}).map(q=>q.id)""")
    ok('кнопка видна и описание открывается у каждой',not bad,bad)
    # плашка до первого подхода — Completely Massive, отдых-пауза
    await E("(()=>{const p=auAll().find(q=>q.id==='jpcm');auPlanStart(p,{w:0,d:0});})()");await pg.wait_for_timeout(200)
    await E("el('dayStart').click()");await pg.wait_for_timeout(300)
    k=await E("(()=>{const i=current.program.ex.findIndex(e=>/отдых-пауза$/.test(e[0]));goEx(i);return i})()");await pg.wait_for_timeout(150)
    ok('перед первым заходом — плашка «Как делать: отдых-пауза…»',await E("(()=>{const h=document.querySelector('.coach-how');return !!h&&/Отдых-пауза/.test(h.textContent)})()"))
    if SHOT:await pg.screenshot(path=SHOT+'/how.png')
    await E(f"current.sets[{k}].filter(x=>!x.warm)[0].done=true;renderWorkout()");await pg.wait_for_timeout(100)
    ok('после первого захода плашка уходит',await E("!document.querySelector('.coach-how')"))
    await E(f"current.sets[{k}].forEach(x=>x.done=false);renderWorkout()")
    # переключатель
    ok('в профиле есть «Подсказки тренера», по умолчанию включено',await E("el('pfCoach').checked===true"))
    await E("el('pfCoach').click()");await pg.wait_for_timeout(100)
    ok('выключено → сохранено',await E("localStorage.getItem('gym45_coach_v1')==='off'"))
    await E("renderWorkout()");ok('выключено → плашки нет',await E("!document.querySelector('.coach-how')"))
    await E(f"""(()=>{{const i={k},S=current.sets[i],j=S.indexOf(S.filter(x=>!x.warm)[0]);S[j].done=true;restStop();window._r=wkCoach(i,j);}})()""")
    r=await E("[_r,el('wkCoach').hidden,el('wkRest').hidden?0:restTotal]")
    ok('выключено → окна нет, но таймер 20 с между заходами работает',r==[True,True,20],r)
    await E("restStop()")
    r=await E("(()=>{const i=current.idx;current.program.ex[i]=['Разгибания ног · дроп-сет',2,22,40,null,'20–25 повт.',120];current.sets[i]=[{w:1,r:1,done:true},{w:1,r:1,done:false}];return [wkCoach(i,0)]})()")
    ok('выключено → совет перед дроп-сетом не берёт таймер (обычный отдых)',r==[False],r)
    await E("el('pfCoach').click()");ok('включено обратно',await E("localStorage.getItem('gym45_coach_v1')==='on'&&coachOn()"))
    # цепочка таймеров после сворачивания
    await E("restStop();const i=current.idx;current.program.ex[i]=['Сгибание ног',2,10,30,null,'До отказа. Затем растяжка 60–90 с',60];current.sets[i]=[{w:1,r:1,done:true},{w:1,r:1,done:true}];wkCoach(i,1)")
    ok('растяжка 60 с запущена',await E("restTotal===60&&!el('wkRest').hidden"))
    await E("clearInterval(restIv);restEnd=Date.now()-30000;restTick()");await pg.wait_for_timeout(100)
    left=await E("Math.round((restEnd-Date.now())/1000)")
    ok('телефон был заблокирован 30 с после растяжки → отдых идёт от её конца (осталось ~программный−30)',await E("restTotal")>0 and abs(left-(await E("restTotal")-30))<=2,(left,await E("restTotal")))
    await E("restStop()")
    # Blood & Guts: «после отказа добил»
    await E("current=null;(()=>{const p=auAll().find(q=>q.id==='bg');auPlanStart(p,{w:1,d:0});})()");await pg.wait_for_timeout(200)
    await E("el('dayStart').click()");await pg.wait_for_timeout(300)
    ok('Blood & Guts: под подходом выбор «Ничего / Форсированные / Негатив»',await E("document.querySelectorAll('.fx-b').length===3"))
    if SHOT:await pg.screenshot(path=SHOT+'/fx.png')
    await E("document.querySelector('.fx-b[data-fx=\"f\"]').click()")
    ok('выбрано «Форсированные» — сохранено на рабочем подходе',await E("(()=>{const w=current.sets[current.idx].filter(x=>!x.warm);return w[w.length-1].fx==='f'})()"))
    nm=await E("current.program.ex[current.idx][0]")
    await E("(()=>{current.sets.forEach(se=>se.forEach(s=>{if(!s.warm)s.done=true;}));finishWorkout();})()");await pg.wait_for_timeout(300)
    ok('в истории подход помечен fx',await E(f"(()=>{{const h=safe.get();const x=h[h.length-1];return (x.log[{nm!r}]||[]).some(s=>s.fx==='f')}})()"))
    ok('«Прошлый раз» знает про форсированные',await E(f"lastResult({nm!r}).sets.some(s=>s.fx==='f')"))
    await E("current=null;(()=>{const p=auAll().find(q=>q.id==='bg');auPlanStart(p,{w:0,d:0});})()");await pg.wait_for_timeout(200)
    await E("el('dayStart').click()");await pg.wait_for_timeout(300)
    ok('во вкатке (без форсированных) выбора нет',await E("!document.querySelector('.fx-b')"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
