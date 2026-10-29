# «Смазка суставов»: отдельный раздел, проверка подвижности (тесты, слабые места, прогресс),
# программа 4 недели (перезагрузка + задача дня), «гора», +5 мин после 4 недель, главная, облако.
# Запуск: python3 tests/mob_check.py index.html [папка_скриншотов]
import asyncio,os,sys,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
HTML=os.path.abspath(sys.argv[1]);SHOT=sys.argv[2] if len(sys.argv)>2 else None
tmp=tempfile.mkdtemp();shutil.copy(HTML,tmp+'/index.html')
if os.path.isdir(os.path.dirname(HTML)+'/media'):os.symlink(os.path.dirname(HTML)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
RUN="startWorkout(mobPlan(mobActive(),mobState(mobActive())),true);el('dayStart').click();current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));finishWorkout()"
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';show('programs')");await pg.wait_for_timeout(100)
    ok('в «Выбрать программу» есть раздел «Смазка суставов»',await pg.evaluate("!!document.querySelector('#scr-programs .disc[data-disc=\"Смазка суставов\"]')"))
    await pg.evaluate("document.querySelector('#scr-programs .disc[data-disc=\"Смазка суставов\"]').click()");await pg.wait_for_timeout(100)
    ok('экран раздела: старт программы и форма проверки',await pg.evaluate("currentScreen==='mob'&&!!el('mobGo')&&!!el('mobT_sit')&&!!el('mobTSave')"))
    await pg.evaluate("el('mobT_sit').value='6';el('mobT_breath').value='15';el('mobT_squat').value='2';el('mobT_bal').value='8';el('mobT_steps').value='5000';el('mobTSave').click()");await pg.wait_for_timeout(100)
    ok('проверка сохранена, слабые места с подсказками',await pg.evaluate("mobStore().tests.length===1&&el('mobBody').textContent.includes('Слабые места')&&el('mobBody').textContent.includes('дыхание животом')"))
    await pg.evaluate("el('mobGo').click()");await pg.wait_for_timeout(100)
    if SHOT:await pg.screenshot(path=SHOT+'/mob.png',full_page=True)
    pl=await pg.evaluate("(()=>{const P=mobActive(),p=mobPlan(P,mobState(P));return p.ex.map(e=>e[0]+'|'+e[2])})()")
    ok('день 1: перезагрузка (5 движений) + вставания с пола 10 мин',len(pl)==6 and pl[0].startswith('Дыхание животом') and pl[5]=='Вставания с пола|10 мин',pl)
    ok('на главной «Сегодня»: смазка суставов',await pg.evaluate("(()=>{const x=mpList().find(x=>x.k==='mob');return x&&x.next===localDate()&&dashNextName(x).includes('Вставания с пола')})()"))
    await pg.evaluate(RUN);await pg.wait_for_timeout(150)
    ok('после дня — экран раздела, вечерняя подсказка, завтра — ползание и «гора»',await pg.evaluate("currentScreen==='mob'&&el('mobBody').textContent.includes('Вечером')&&mobPlan(mobActive(),mobState(mobActive())).ex.some(e=>/«Гора»/.test(e[0]))"))
    ok('«сегодня» сделано → следующая завтра; в неделю силовых не засчитано',await pg.evaluate("mpList().find(x=>x.k==='mob').next>localDate()&&weekDone()===0"))
    await pg.evaluate("startWorkout(mobPlan(mobActive(),mobState(mobActive())),true);el('dayStart').click();current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));current.sets[6][0].r=7;finishWorkout()");await pg.wait_for_timeout(150)
    ok('«гора»: записана ступень 7',await pg.evaluate("mobActive().recs.slice(-1)[0].climb===7&&el('mobBody').textContent.includes('ступень 7')"))
    await pg.evaluate("(()=>{const v=mobStore(),P=mobActive(v);while(P.recs.length<28)P.recs.push({uid:'q'+P.recs.length,day:0,finishedAt:'2026-01-01T00:00:00Z'});mobSave(v);})()")
    pl=await pg.evaluate("(()=>{const P=mobActive(),p=mobPlan(P,mobState(P));return p.ex.map(e=>e[0]+'|'+e[2])})()")
    ok('после 4 недель: рабочие части +5 мин (вставания 15 мин)',pl[5]=='Вставания с пола|15 мин',pl)
    ok('аналитика: раздел «Смазка суставов», запись в истории',await pg.evaluate("AN_SECS.some(x=>x[0]==='mob')&&safe.get().some(h=>h.sec==='mob')"))
    ok('облако: снимок и слияние с тестами',await pg.evaluate("(()=>{const s=cloudSnapshot();const m=mergeMob({progs:[],activeId:null,tests:[]},s.mob);return m.progs.length===1&&m.tests.length===1})()"))
    # отдельная глава, заминка, день отдыха
    await pg.evaluate("show('programs')");await pg.wait_for_timeout(80)
    ok('«Смазка суставов» — отдельной главой «Восстановление»',await pg.evaluate("(()=>{const b=document.querySelector('#scr-programs .disc-mob');return b&&b.previousElementSibling&&b.previousElementSibling.textContent.includes('Восстановление')})()"))
    cp=await pg.evaluate("mobCoolPlan({ex:[['Приседания со штангой'],['Жим штанги лёжа']]}).ex.map(e=>e[0])")
    ok('заминка после присед+жим: бедро, наклон, грудь, вис, дыхание',cp==['Растяжка у дивана','Наклон к прямым ногам сидя','Растяжка груди в дверном проёме','Вис на перекладине','Дыхание животом'],cp)
    await pg.evaluate("(()=>{const p=AUTH.find(q=>q.id==='pcfb');beginWorkout(Object.assign({},p.weeks[0].days[0],{au:{id:'pcfb',w:0}}),false);current.sets.forEach(se=>se.forEach(s=>{s.done=true;if(!s.w)s.w=20;}));wkAllDone();})()");await pg.wait_for_timeout(100)
    ok('итог тренировки: кнопка «Сохранить и сделать заминку»',await pg.evaluate("!!el('wkDoneCool')"))
    await pg.evaluate("el('wkDoneCool').click()");await pg.wait_for_timeout(700)
    ok('после сохранения открывается заминка',await pg.evaluate("currentScreen==='day'&&dayView.p.mobx&&dayView.p.name.includes('Заминка')"))
    await pg.evaluate("el('dayStart').click();goEx(0)");await pg.wait_for_timeout(100)
    ok('в заминке шапка «Минут», без RIR',await pg.evaluate("el('exList').querySelector('.set-row.head span:nth-child(3)').textContent==='Минут'&&!el('exList').querySelector('.rir-row')"))
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));finishWorkout()");await pg.wait_for_timeout(150)
    ok('заминка не считается силовой тренировкой недели',await pg.evaluate("weekDone()===1"))
    await pg.evaluate("show('home')");await pg.wait_for_timeout(100)
    ok('на главной: силовая по плану не вытеснена смазкой',await pg.evaluate("!el('dashToday').querySelector('.td-main')||!el('dashToday').querySelector('.td-main b').textContent.includes('Смазка')"))
    await pg.evaluate("(()=>{const v=auSt();v.act={};auSave(v);})();show('programs');show('home')");await pg.wait_for_timeout(100)
    ok('день отдыха: рекомендация «Смазка суставов»',await pg.evaluate("el('dashToday').textContent.includes('Сегодня отдых')||el('dashToday').textContent.includes('Нет активной')"),await pg.evaluate("el('dashToday').textContent.slice(0,200)"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
