# Звук таймеров: звук разблокируется касанием (iPhone), отдых: 3-2-1 и сигнал в конце.
# Запуск: python3 tests/sound_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(has_touch=True,is_mobile=True,viewport={'width':390,'height':844});pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    ok('до касания звук не создан',await pg.evaluate("AC===null"))
    await pg.tap('body');await pg.wait_for_timeout(200)
    ok('после касания звук включён',await pg.evaluate("!!AC&&AC.state==='running'"),await pg.evaluate("AC&&AC.state"))
    await pg.evaluate("window.__b=[];const _b=beep;beep=function(f,d,v,t){__b.push(f);return _b(f,d,v,t)};startWorkout({name:'Т',focus:'т',sec:'body',ex:[['Жим штанги лёжа',3,'8',60]]},false);el('dayStart').click()")
    await pg.evaluate("document.querySelectorAll('#exList .chk')[0].click()");await pg.wait_for_timeout(100)
    await pg.evaluate("restEnd=Date.now()+3500")
    await pg.wait_for_timeout(4300)
    b_=await pg.evaluate("__b")
    ok('отдых: 3 коротких сигнала и финальный',b_.count(880)==3 and 1046 in b_ and 1320 in b_,b_)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
