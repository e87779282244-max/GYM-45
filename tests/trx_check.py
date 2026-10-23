# Раздел TRX: кнопка направления, список программ, круги, запись в историю.
# Запуск: python3 tests/trx_check.py index.html [папка_скриншотов]
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
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';show('programs')");await pg.wait_for_timeout(150)
    ok('кнопка «TRX» среди направлений',await pg.evaluate("[...document.querySelectorAll('#scr-programs .disc[data-disc]')].map(b=>b.dataset.disc).join(',')==='Бодибилдинг,Пауэрлифтинг,Стритлифтинг,Кроссфит,Стрит воркаут,TRX'"))
    await pg.evaluate("document.querySelector('.disc[data-disc=\"TRX\"]').click()");await pg.wait_for_timeout(120)
    ok('открывается экран TRX',await pg.evaluate("currentScreen==='trx'&&el('trxProgs').children.length===1"))
    if SHOT:await pg.screenshot(path=SHOT+'/trx-list.png')
    await pg.evaluate("el('trxProgs').querySelector('.disc').click()");await pg.wait_for_timeout(120)
    ok('программа: 10 тренировок',await pg.evaluate("el('bodyDays').querySelectorAll('.disc').length===10&&el('progEyebrow').textContent.startsWith('TRX')"))
    ok('нет повторов упражнений внутри дня',await pg.evaluate("TRX_PROGS.every(p=>p.days.every(d=>new Set(d.ex.map(e=>e[0])).size===d.ex.length))"))
    ok('круги: внутри круга отдых 5 с, после круга — 30 с (Ab Blast)',await pg.evaluate("(()=>{const e=TRX_PROGS[0].days[0].ex;return e.length===3&&e.every(x=>x[1]===5)&&e[0][6]===5&&e[2][6]===30})()"))
    ok('300 повторов в тренировке 8',await pg.evaluate("TRX_PROGS[0].days[7].ex.reduce((a,e)=>a+e[1]*e[2],0)===300"))
    if SHOT:await pg.screenshot(path=SHOT+'/trx-prog.png')
    await pg.evaluate("el('bodyDays').querySelectorAll('.disc')[1].click()");await pg.wait_for_timeout(120)
    if SHOT:await pg.screenshot(path=SHOT+'/trx-day.png')
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(120)
    ok('тренировка: подсказка круга',await pg.evaluate("!!el('exList').querySelector('.ex-note')&&el('exList').querySelector('.ex-note').innerText.includes('Круг A1')"))
    if SHOT:await pg.screenshot(path=SHOT+'/trx-workout.png')
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));finishWorkout()");await pg.wait_for_timeout(150)
    last=json.loads(await pg.evaluate("JSON.stringify(safe.get().slice(-1)[0])"))
    ok('в истории — раздел trx',last.get('sec')=='trx' and last.get('name')=='TRX 2 · Full Body Blast',(last.get('sec'),last.get('name')))
    ok('аналитика знает раздел TRX',await pg.evaluate("AN_SEC_LBL.trx==='TRX'&&AN_SECS.some(x=>x[0]==='trx')"))
    ok('без горизонтальной прокрутки',await pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f'\n{sum(R)}/{len(R)} PASS');sys.exit(0 if all(R) else 1)
asyncio.run(m())
