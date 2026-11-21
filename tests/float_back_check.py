# Плавающая «Назад»: появляется, когда кнопка в шапке ушла за верх, ведёт туда же, прячется наверху и при смене экрана.
# Запуск: python3 tests/float_back_check.py index.html
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
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(500);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate;on="el('floatBack').classList.contains('on')"
    for scr in ['programs','gvt','food','progress']:
      await E(f"show('home');show('{scr}');scrollTo(0,0)");await pg.wait_for_timeout(250)
      ok(f'{scr}: наверху плавающей нет',not await E(on))
      await E("scrollTo(0,document.documentElement.scrollHeight)");await pg.wait_for_timeout(250)
      ok(f'{scr}: прокрутил вниз — плавающая видна',await E(on))
      if SHOT and scr=='gvt':
        await E("scrollTo(0,700)");await pg.wait_for_timeout(250);await pg.screenshot(path=SHOT)
      await E("el('floatBack').click()");await pg.wait_for_timeout(250)
      ok(f'{scr}: нажатие → назад на главную, плавающая спряталась',await E(f"currentScreen==='home'&&!{on}"),await E("currentScreen"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
