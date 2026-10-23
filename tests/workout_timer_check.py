# Экран тренировки: общее время с начала (м:сс / ч:мм:сс) и шкала выполненных подходов.
# Запуск: python3 tests/workout_timer_check.py index.html [папка_скриншотов]
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);O=sys.argv[2] if len(sys.argv)>2 else None;tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(300)
    await pg.evaluate("el('login').style.display='none';show('body');authSetWeek(AUTH[0],0);authOpen(AUTH[0]);el('bodyDays').querySelectorAll('.disc')[0].click();el('dayStart').click()")
    await pg.wait_for_timeout(200)
    ok('экран тренировки открыт, таймер виден',await pg.evaluate("currentScreen==='workout'&&!el('wkTime').hidden&&el('wkTime').offsetHeight>0"))
    await pg.evaluate("current.startedAt=new Date(Date.now()-(25*60+7)*1000).toISOString();current.sets[0].forEach(s=>s.done=true);current.sets[1][0].done=true;renderWorkout()")
    await pg.wait_for_timeout(1200)
    t=await pg.evaluate("el('wkTimeT').textContent");ok('время с начала ~25:08',t.startswith('25:0'),t)
    st=await pg.evaluate("el('wkTimeSets').textContent");ok('счётчик подходов 4/29',st.startswith('4/'),st)
    ok('шкала заполнена пропорционально',await pg.evaluate("parseInt(el('wkTimeBar').style.width)>0"),await pg.evaluate("el('wkTimeBar').style.width"))
    await pg.evaluate("current.startedAt=new Date(Date.now()-(3600+5*60)*1000).toISOString()");await pg.wait_for_timeout(1100)
    t=await pg.evaluate("el('wkTimeT').textContent");ok('больше часа — ч:мм:сс',t.startswith('1:05:'),t)
    if O:await pg.evaluate("current.startedAt=new Date(Date.now()-(25*60+7)*1000).toISOString();window.scrollTo(0,0)");await pg.wait_for_timeout(1100);await pg.screenshot(path=O+'/wk.png') if O else None
    ok('без горизонтальной прокрутки',await pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f"\n{sum(R)}/{len(R)} PASS");sys.exit(0 if all(R) else 1)
asyncio.run(m())
