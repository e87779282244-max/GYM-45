# Рабочий стол «Bento v3»: шапка, карточка дня, вода/питание, командный центр с логотипом GYM 45, плавающий док.
# Запуск: python3 tests/home_bento_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(500);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    await E("show('home');renderToday()");await pg.wait_for_timeout(300)
    wd=["Воскресенье","Понедельник","Вторник","Среда","Четверг","Пятница","Суббота"]
    r=await E("el('homeEyebrow').textContent")
    ok('шапка: «GYM 45 • день недели»',r.startswith('GYM 45 • ') and r.split('• ')[1] in wd,r)
    ok('колокольчик напоминаний — в шапке',await E("!!el('tdCal')&&el('homeActs').contains(el('tdCal'))"))
    r=await E("[el('homeThemeL').textContent,(el('homeMenu').click(),document.documentElement.getAttribute('data-theme')),el('homeThemeL').textContent,(el('homeMenu').click(),el('homeThemeL').textContent)]")
    ok('кнопка темы: Песочная ↔ Тёмная',r==['Песочная','dark','Тёмная','Песочная'],r)
    ok('нет программы: значок «Нет программы», стрелка ведёт к выбору',await E("el('dashToday').querySelector('.td-badge').textContent.includes('Нет программы')&&!!el('tdPick')"))
    await E("el('tdPick').click()");ok('стрелка → «Программы»',await E("currentScreen==='programs'"))
    await E("show('home')");await pg.wait_for_timeout(200)
    r=await E("(()=>{const i=document.querySelector('#scr-home .cmd-brand img');return [!!i,i&&i.naturalWidth,i&&Math.round(i.getBoundingClientRect().height),document.querySelector('#scr-home .cmd-brand').textContent]})()")
    ok('командный центр: наш логотип загружен и виден, «GYM 45 PRO · Challenge accepted · Инструменты»',r[0] and r[1]>0 and r[2]>=20 and 'GYM 45' in r[3] and 'PRO' in r[3] and 'Инструменты' in r[3],r)
    tools=await E("[...document.querySelectorAll('#scr-home .tool')].map(b=>[b.dataset.go,b.querySelector('b').textContent])")
    ok('4 плитки инструментов',[t[0] for t in tools]==['programs','nutrition','progress','onerm'],tools)
    for go,scr in [('programs','programs'),('progress','progress')]:
      await E(f"show('home');document.querySelector('#scr-home .tool[data-go=\"{go}\"]').click()");await pg.wait_for_timeout(150)
      ok(f'плитка {go} открывает экран',await E(f"currentScreen==='{scr}'"),await E("currentScreen"))
    # активная программа, день отдыха
    await E("const v=auSt();v.act={y3t:{start:localDate(),base:0}};auSave(v);show('programs');show('home')");await pg.wait_for_timeout(200)
    ok('день тренировки: «Тренировка • дата», кнопка «Начать»',await E("el('dashToday').querySelector('.td-badge').textContent.includes('Тренировка')&&el('tdGo').textContent.includes('Начать')"))
    await E("el('tdGo').click()");await pg.wait_for_timeout(150);await E("el('dayStart').click()");await pg.wait_for_timeout(100)
    await E("current.sets.forEach(se=>se.forEach(s=>{s.done=true;if(!s.w)s.w=50;}));finishWorkout()");await pg.wait_for_timeout(200)
    await E("if(el('coolSkip'))el('coolSkip').click();document.querySelectorAll('.gvt-modal').forEach(x=>x.hidden=true);show('home')");await pg.wait_for_timeout(200)
    r=await E("[el('dashToday').querySelector('.td-badge').textContent,el('tdNext').querySelector('.td-meta em').textContent,el('tdNext').querySelector('.t').textContent]")
    ok('отдых: «Отдых • дата», следующая сессия с датой-чипом',r[0].startswith('Отдых') and len(r[1])>4 and len(r[2])>3,r)
    await E("el('tdNextGo').click()");await pg.wait_for_timeout(150)
    ok('стрелка → план следующей тренировки',await E("currentScreen!=='home'"),await E("currentScreen"))
    # питание: «+ Добавить приём» — дневник и поиск продукта
    await E("localStorage.setItem(NTK_T,JSON.stringify({sex:'male',age:45,weight:95,height:180,activity:'moderate',goal:'lose',updatedAt:1}));show('home');renderToday()");await pg.wait_for_timeout(200)
    r=await E("[...el('tdFood').querySelectorAll('.mc b')].map(x=>x.textContent)")
    ok('питание: Белки / Жиры / Углеводы',r==['Белки','Жиры','Углеводы'],r)
    await E("el('tdMealAdd').click()");await pg.wait_for_timeout(700)
    ok('«+ Добавить приём» → дневник питания',await E("currentScreen==='food'&&NT_TAB==='diary'"))
    # док
    await E("show('home')");await pg.wait_for_timeout(150)
    r=await E("(()=>{const t=document.querySelector('.tab.on'),n=document.querySelector('.nav-inner').getBoundingClientRect();return [t.dataset.scr,getComputedStyle(t).backgroundColor,Math.round(innerHeight-n.bottom),Math.round(n.left)]})()")
    ok('док: плавающая «таблетка», активная вкладка залита',r[0]=='home' and r[1] not in ('rgba(0, 0, 0, 0)','transparent') and r[2]>=8 and r[3]>=10,r)
    ok('без горизонтальной прокрутки',await E("document.documentElement.scrollWidth<=innerWidth+1"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
