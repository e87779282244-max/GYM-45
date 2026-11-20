# Главная «Сегодня»: следующая тренировка в одно нажатие, отдых, неделя по плану, питание за день.
# Запуск: python3 tests/home_today_check.py index.html [папка_скриншотов]
import asyncio,os,sys,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
HTML=os.path.abspath(sys.argv[1]);SHOT=sys.argv[2] if len(sys.argv)>2 else None
tmp=tempfile.mkdtemp();shutil.copy(HTML,tmp+'/index.html')
if os.path.isdir(os.path.dirname(HTML)+'/media'):os.symlink(os.path.dirname(HTML)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';show('home')");await pg.wait_for_timeout(100)
    ok('нет программы: «Выбрать программу» в карточке «Сегодня»',await pg.evaluate("el('dashToday').textContent.includes('Нет активной программы')&&!!el('tdPick')"))
    ok('дубля «Выбрать программу» в плитках нет, есть «Питание сегодня»',await pg.evaluate("![...document.querySelectorAll('#scr-home .dash-tile')].some(b=>b.textContent.includes('Выбрать программу'))&&!!el('dashFood')"))
    await pg.evaluate("document.querySelector('.tab[data-scr=\"workout\"]').click()");await pg.wait_for_timeout(100)
    ok('вкладка «Тренировка» без программы → выбор программы',await pg.evaluate("currentScreen==='programs'"))
    await pg.evaluate("show('home')")
    # активируем Y3T
    await pg.evaluate("const v=auSt();v.act={y3t:{start:localDate(),base:0}};auSave(v);show('programs');show('home')");await pg.wait_for_timeout(100)
    ok('по плану сегодня: Y3T, следующая тренировка названа',await pg.evaluate("el('dashToday').textContent.includes('Тренировка по плану')&&el('dashToday').querySelector('.td-main b').textContent.includes('Пульс на взлёт')&&el('dashToday').querySelector('.td-main span').textContent.length>3"))
    ok('день тренировки: блок «Готовность» виден',await pg.evaluate("getComputedStyle(document.querySelector('#scr-home .ready')).display!=='none'"))
    ok('неделя: 0 из 5 по плану',await pg.evaluate("el('dashToday').textContent.includes('Неделя: 0/5')"),await pg.evaluate("el('tdWeek').textContent"))
    if SHOT:await pg.screenshot(path=SHOT+'/home-today.png',full_page=True)
    await pg.evaluate("document.querySelector('.tab[data-scr=\"workout\"]').click()");await pg.wait_for_timeout(150)
    ok('вкладка «Тренировка» → сразу обзор следующей тренировки программы',await pg.evaluate("currentScreen==='day'&&dayView.p.au&&dayView.p.au.id==='y3t'"))
    await pg.evaluate("show('home')");await pg.wait_for_timeout(100)
    await pg.evaluate("el('tdGo').click()");await pg.wait_for_timeout(150)
    ok('«Начать» — сразу обзор дня этой тренировки',await pg.evaluate("currentScreen==='day'&&dayView.p.au&&dayView.p.au.id==='y3t'"))
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(100)
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>{s.done=true;if(!s.w)s.w=50;}));finishWorkout()");await pg.wait_for_timeout(150)
    await pg.evaluate("show('home')");await pg.wait_for_timeout(100)
    ok('после тренировки: «Отдых», следующая сессия названа, неделя 1 из 5',await pg.evaluate("el('dashToday').querySelector('.td-badge').textContent.includes('Отдых')&&el('dashToday').textContent.includes('Следующая сессия')&&el('tdNext').querySelector('.t').textContent.length>3&&el('dashToday').textContent.includes('Неделя: 1/5')"),await pg.evaluate("el('dashToday').textContent"))
    ok('день отдыха: блок «Готовность» скрыт',await pg.evaluate("getComputedStyle(document.querySelector('#scr-home .ready')).display==='none'"))
    ok('отдых, одна программа: строка с ней не повторяется, «Активные программы» скрыты',await pg.evaluate("el('dashToday').querySelectorAll('.td-row').length===0&&el('dashActive').hidden"),await pg.evaluate("el('dashToday').querySelectorAll('.td-row').length"))
    await pg.evaluate("const v=auSt();v.act.y3t2=v.act.y3t;auSave(v);")
    ok('две программы: блок виден, кнопок «Завершить» на главной нет',await pg.evaluate("!el('dashActive').hidden||mpList().length<2")and await pg.evaluate("!document.querySelector('#scr-home .mp-end')"))
    await pg.evaluate("const v=auSt();delete v.act.y3t2;auSave(v);show('programs');show('home')")
    # питание за день
    await pg.evaluate("localStorage.setItem(FOODK,JSON.stringify([{id:1,date:localDate(),name:'x',kcal:1450,p:90,f:40,c:150}]));show('programs');show('home')");await pg.wait_for_timeout(100)
    ok('питание за день на главной',await pg.evaluate("el('dashFoodT').textContent.includes('1')&&el('dashFoodT').textContent.includes('белок 90')&&!!el('tdFood')&&/1\\s?450/.test(el('tdFood').textContent)"),await pg.evaluate("el('tdFood').textContent"))
    ok('без горизонтальной прокрутки',await pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
