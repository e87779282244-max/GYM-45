# Готовность: Устал/Норма/Заряжен → веса, подходы, лёгкий день.
# Запуск: python3 tests/readiness_check.py index.html [папка_скриншотов]
import asyncio,json,os,sys,shutil,tempfile,http.server,threading,functools
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
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    await pg.evaluate("localStorage.setItem('gym45_rm_v1',JSON.stringify({'Жим лёжа':125,'Приседания со штангой':150,'Становая тяга':180}))")
    ready=lambda v:pg.evaluate(f"show('home');document.querySelector('.seg-b[data-ready=\"{v}\"]').click()")
    await ready('Устал')
    ok('подсказка «Устал»',await pg.evaluate("el('readyNote').textContent.includes('−10')"))
    # Фалеев, база, Вт — тяжёлый жим 5×8
    await pg.evaluate("show('programs');document.querySelector('.disc[data-disc=\"Пауэрлифтинг\"]').click()");await pg.wait_for_timeout(150)
    await pg.evaluate("[...el('pwrPrograms').querySelectorAll('.disc')].find(b=>b.textContent.includes('Последний герой')).click()");await pg.wait_for_timeout(150)
    await pg.evaluate("el('auWk').querySelectorAll('button')[1].click()");await pg.wait_for_timeout(100)
    await pg.evaluate("[...el('bodyDays').querySelectorAll('.disc')].find(b=>b.textContent.includes('Вт · тяжёлый жим')).click()");await pg.wait_for_timeout(150)
    ok('день: план → сегодня и −1 подход',await pg.evaluate("el('dayList').textContent.includes('82,5 → 75 кг')&&el('dayList').textContent.includes('подходов 5 → 4')"),await pg.evaluate("el('dayList').textContent.slice(0,160)"))
    ok('предложен лёгкий день',await pg.evaluate("!!el('dayReady').querySelector('.day-alt')&&el('dayReady').textContent.includes('лёгкие присед и жим')"))
    if SHOT:await pg.screenshot(path=SHOT+'/ready_day.png')
    await pg.evaluate("el('dayReady').querySelector('.day-alt').click()");await pg.wait_for_timeout(120)
    ok('переход на лёгкий день',await pg.evaluate("dayView.p.name.includes('лёгкие')&&dayView.p.fixed===1&&dayView.p.au&&dayView.p.ex.length===2"))
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(150)
    ok('лёгкий: подходы не урезаны, вес −10 %',await pg.evaluate("current.sets[0].length===5&&current.sets[1][0].w===Math.round(FAL_PROG.weeks[1].days[3].ex[1][3]*0.9/2.5)*2.5"),await pg.evaluate("[current.sets[1][0].w,FAL_PROG.weeks[1].days[3].ex[1][3]]"))
    ok('карточка: строка готовности',await pg.evaluate("!!document.querySelector('#exList .rdy-line')"))
    if SHOT:await pg.screenshot(path=SHOT+'/ready_wk.png')
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));finishWorkout()");await pg.wait_for_timeout(150)
    # Заряжен: пауэрлифтинг без изменений, бодибилдинг +5 %
    await ready('Заряжен')
    await pg.evaluate("show('programs');document.querySelector('.disc[data-disc=\"Пауэрлифтинг\"]').click()");await pg.wait_for_timeout(150)
    await pg.evaluate("[...el('pwrPrograms').querySelectorAll('.disc')].find(b=>b.textContent.includes('Последний герой')).click()");await pg.wait_for_timeout(150)
    await pg.evaluate("el('auWk').querySelectorAll('button')[1].click()");await pg.wait_for_timeout(100)
    await pg.evaluate("[...el('bodyDays').querySelectorAll('.disc')].find(b=>b.textContent.includes('Вт · тяжёлый жим')).click()");await pg.wait_for_timeout(150)
    ok('Заряжен в цикле: план не меняется',await pg.evaluate("el('dayList').textContent.includes('5 подходов')&&el('dayList').textContent.includes('82,5 кг')&&!el('dayList').textContent.includes('82,5 → ')&&el('dayReady').textContent.includes('план без изменений')"))
    ok('Заряжен в бодибилдинге: +5 %',await pg.evaluate("rScaleW(100,{sec:'body'})===105&&rScaleW(100,{fixed:1})===100"))
    await ready('Норма')
    ok('Норма: всё по плану',await pg.evaluate("rScaleW(100,{})===100&&rScaleSets(5,['Жим лёжа'])===5&&el('readyNote').textContent==='всё по программе'"))
    await ready('Устал')
    ok('Устал: изоляцию не урезаем',await pg.evaluate("rScaleSets(4,['Подъём гантелей на бицепс'])===4&&rScaleSets(4,['Становая тяга'])===3&&rScaleSets(2,['Становая тяга'])===2"))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f'\n{sum(R)}/{len(R)} PASS');sys.exit(0 if all(R) else 1)
asyncio.run(m())
