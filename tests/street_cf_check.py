# Стритлифтинг (Calisthetics) и кроссфит (Phil Team): списки, запуск, история.
# Запуск: python3 tests/street_cf_check.py index.html [папка_скриншотов]
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
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';show('programs')");await pg.wait_for_timeout(100)
    await pg.evaluate("document.querySelector('.disc[data-disc=\"Стритлифтинг\"]').click()");await pg.wait_for_timeout(120)
    ok('стритлифтинг: классический цикл на месте + 4 программы',await pg.evaluate("currentScreen==='street'&&STREET.every(d=>[...el('streetDays').querySelectorAll('.disc')].some(b=>b.textContent.includes(d.name)))&&STREET_PROGS.length===4&&el('streetDays').querySelectorAll('.disc').length===STREET.length+4"))
    await pg.evaluate("document.querySelector('.disc[data-disc=\"Стритлифтинг\"]')&&(show('programs'),document.querySelector('.disc[data-disc=\"Стритлифтинг\"]').click())");await pg.wait_for_timeout(120)
    ok('повторное открытие не дублирует список',await pg.evaluate("el('streetDays').querySelectorAll('.disc').length===STREET.length+4"))
    if SHOT:await pg.screenshot(path=SHOT+'/street.png',full_page=True)
    await pg.evaluate("[...el('streetDays').querySelectorAll('.disc')].find(b=>b.textContent.includes('Метод 5×5')).click()");await pg.wait_for_timeout(120)
    ok('5×5: 4 тренировки',await pg.evaluate("el('bodyDays').querySelectorAll('.disc').length===4"))
    await pg.evaluate("el('bodyDays').querySelectorAll('.disc')[2].click()");await pg.wait_for_timeout(100);await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(150)
    ok('сессия B: своя строка цели',await pg.evaluate("el('exList').querySelector('.target').textContent.includes('5-5-5-5-3')"))
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));finishWorkout()");await pg.wait_for_timeout(150)
    ok('история: раздел street',await pg.evaluate("safe.get().slice(-1)[0].sec==='street'"))
    ok('комплекс 1 — суперсет подтягивания → брусья',await pg.evaluate("(()=>{const d=STREET_PROGS[3].days[0];current={program:{ex:d.ex}};const g=wkGroup(0);current=null;return g&&g.join()==='0,1'})()"))
    ok('Блатов: 8 тренировок 5×2…5×5',await pg.evaluate("STREET_PROGS[2].days.length===8&&STREET_PROGS[2].days.map(d=>d.ex[0][2]).join()==='2,2,3,3,4,4,5,5'"))
    await pg.evaluate("show('programs');document.querySelector('.disc[data-disc=\"Кроссфит\"]').click()");await pg.wait_for_timeout(150)
    ok('кроссфит: кнопка программы на месяц',await pg.evaluate("currentScreen==='cross'&&!!el('cfProgBtn')&&el('crossDays').querySelectorAll('#cfProgBtn').length===1"))
    if SHOT:await pg.screenshot(path=SHOT+'/cross.png')
    await pg.evaluate("el('cfProgBtn').click()");await pg.wait_for_timeout(120)
    ok('Phil Team: 24 тренировки',await pg.evaluate("el('bodyDays').querySelectorAll('.disc').length===24"))
    ok('нет повторов блоков внутри дня',await pg.evaluate("CF_PROG.days.every(d=>new Set(d.ex.map(e=>e[0])).size===d.ex.length)"))
    await pg.evaluate("el('bodyDays').querySelectorAll('.disc')[0].click()");await pg.wait_for_timeout(100);await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(150)
    ok('блок: время и круги в строке цели',await pg.evaluate("el('exList').querySelector('.target').textContent.includes('2 круга — отметь')"))
    if SHOT:await pg.screenshot(path=SHOT+'/cf-block.png')
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));finishWorkout()");await pg.wait_for_timeout(150)
    ok('история: раздел cross',await pg.evaluate("safe.get().slice(-1)[0].sec==='cross'"))
    ok('без горизонтальной прокрутки',await pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f'\n{sum(R)}/{len(R)} PASS');sys.exit(0 if all(R) else 1)
asyncio.run(m())
