# Звук таймера: после сворачивания (Web Audio «заморожен») сигнал не пропадает — запасной звук, новый Web Audio по первому касанию.
# Запуск: python3 tests/sound_resume_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(500);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    await pg.touchscreen.tap(200,400);await pg.wait_for_timeout(300)
    ok('после касания Web Audio работает',await E("AC&&AC.state==='running'"))
    await E("window.__osc=0;const O=AudioContext.prototype.createOscillator;AudioContext.prototype.createOscillator=function(){window.__osc++;return O.call(this)};window.__fb=0;const P=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(){if(this===AC_FB&&!this.muted)window.__fb++;return P.call(this)};0")
    await E("beep(1046,0.2,0.35)");ok('обычный сигнал — через Web Audio',await E("__osc===1&&__fb===0"))
    # «свернули»: iOS замораживает Web Audio
    await E("AC.suspend()");await pg.wait_for_timeout(100);await E("AC.resume=()=>Promise.reject(new Error('interrupted'));document.dispatchEvent(new Event('visibilitychange'))");await pg.wait_for_timeout(700)
    ok('после возврата Web Audio помечен «замороженным»',await E("AC_STALE===true&&AC.state!=='running'"))
    await E("restEnd=Date.now()-1;restTick()") if await E("typeof restTick==='function'&&typeof restEnd!=='undefined'") else await E("beep(1046,0.2,0.35)")
    await pg.wait_for_timeout(200)
    ok('конец отдыха без касания — звучит запасной сигнал',await E("__fb>=1"),await E("__fb"))
    old=await E("(window.__oldAC=AC,1)")
    await pg.touchscreen.tap(200,400);await pg.wait_for_timeout(400)
    ok('первое касание — создан новый Web Audio, он работает',await E("AC!==window.__oldAC&&AC.state==='running'&&!AC_STALE"))
    await E("__osc=0;beep(880,0.1,0.3)");ok('дальше снова сигналы через Web Audio',await E("__osc===1"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
