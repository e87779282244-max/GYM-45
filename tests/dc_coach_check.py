# DC Training: кнопка «Описание программы»; подсказки в подходе — 15 вдохов с таймером 20 с между заходами, растяжка 60 с после третьего, потом отдых.
# Запуск: python3 tests/dc_coach_check.py index.html
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
    await E("authOpen(auAll().find(q=>q.id==='dc'))");await pg.wait_for_timeout(200)
    ok('у DC есть кнопка «Описание программы»',await E("!el('progGuideBtn').hidden&&el('progGuideBtn').textContent.includes('Описание программы')"))
    await E("el('progGuideBtn').click()");await pg.wait_for_timeout(150)
    t=await E("el('guideBody').innerText")
    ok('описание: расписание, отдых-пауза, 15 вдохов, растяжка, добивающий, прогресс, разгрузка',all(x in t for x in ['Расписание','Заход 1','15 глубоких вдохов','Растяжка под нагрузкой','добивающий подход','Прогресс','Разгрузка']))
    if SHOT:await pg.screenshot(path=SHOT+'/guide.png')
    await E("el('guideClose').click()");ok('«Понятно» закрывает',await E("el('guideModal').hidden"))
    ok('у программ без описания кнопки нет',await E("(()=>{const q=auAll().find(q=>!AU_GUIDE[q.id]);if(!q)return true;authOpen(q);return el('progGuideBtn').hidden})()"))
    # тренировка DC A1
    await E("(()=>{const p=auAll().find(q=>q.id==='dc');auPlanStart(p,{w:0,d:0});})()");await pg.wait_for_timeout(200)
    await E("el('dayStart').click()");await pg.wait_for_timeout(300)
    ok('первое упражнение — отдых-пауза',await E("/отдых-пауза$/.test(current.program.ex[current.idx][0])"),await E("current.program.ex[current.idx][0]"))
    async def chk(k):
      await E(f"(()=>{{const i=current.idx,S=current.sets[i];const w=S.map((s,j)=>[s,j]).filter(x=>!x[0].warm);const j=w[{k}][1];document.querySelector('#exList .wk-card .chk[data-s=\"'+j+'\"]')?document.querySelector('#exList .wk-card .chk[data-s=\"'+j+'\"]').click():[...document.querySelectorAll('.chk')].find(b=>b.dataset.s==String(j)&&b.closest('[data-i]')?.dataset.i==String(i)).click();}})()")
      await pg.wait_for_timeout(200)
    await chk(0)
    r=await E("[el('wkCoach').hidden,el('wkCoachT').textContent,el('wkRest').hidden,el('wkRest').querySelector('.wk-rest-l').textContent,restTotal]")
    ok('заход 1 отмечен → окно «15 глубоких вдохов», таймер 20 с',r[0]==False and r[1]=='15 глубоких вдохов' and r[3]=='15 вдохов' and r[4]==20,r)
    if SHOT:await pg.screenshot(path=SHOT+'/coach1.png')
    await E("el('wkRestSkip').click()");await pg.wait_for_timeout(200)
    ok('таймер кончился/пропуск → подсказка закрыта, подпись снова «Отдых»',await E("el('wkCoach').hidden&&el('wkRest').querySelector('.wk-rest-l').textContent==='Отдых'"))
    await chk(1);ok('заход 2 → снова 15 вдохов',await E("el('wkCoachT').textContent==='15 глубоких вдохов'&&el('wkCoachP').textContent.includes('Заход 2 готов')"))
    await E("el('wkRestSkip').click()");await pg.wait_for_timeout(150)
    await chk(2)
    r=await E("[el('wkCoach').hidden,el('wkCoachT').textContent,el('wkCoachP').textContent,restTotal]")
    ok('заход 3 → растяжка под нагрузкой 60 с, совет для груди',r[0]==False and r[1].startswith('Растяжка') and r[2].startswith('Грудь') and r[3]==60,r)
    if SHOT:await pg.screenshot(path=SHOT+'/coach2.png')
    i0=await E("current.idx")
    await E("el('wkRestSkip').click()");await pg.wait_for_timeout(200)
    ok('после растяжки — обычный отдых перед следующим упражнением (150 с)',await E("el('wkCoach').hidden&&!el('wkRest').hidden&&restTotal===150"),await E("restTotal"))
    await E("el('wkRestSkip').click()");await pg.wait_for_timeout(200)
    ok('после отдыха — следующее упражнение',await E(f"current.idx==={i0}+1"))
    # таймер вдохов сам истекает
    await chk(0);await E("restEnd=Date.now()+50");await pg.wait_for_timeout(700)
    ok('таймер вдохов истёк сам — подсказка ушла',await E("el('wkCoach').hidden&&el('wkRest').hidden"))
    ok('нигде нет слова «вдоводел»: добивающий подход называется «… · добивающий на 20»',await E("!document.body.innerText.includes('вдоводел')&&auAll().find(q=>q.id==='dc').weeks[0].days[1].ex.some(e=>e[0]==='Приседания со штангой · добивающий на 20')"))
    ok('после добивающего — растяжка (подсказка распознаёт подход)',await E("(()=>{const o=current.program.ex;const k=coachKind;current.program.ex=[['Приседания со штангой · добивающий на 20',1,20,50,null,'',0]];const r=k(0);current.program.ex=o;return r==='wm'})()"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
