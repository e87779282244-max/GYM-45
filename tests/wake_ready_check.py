# Экран не гаснет во время тренировки (Wake Lock); готовность держится до конца дня; в программах с расчётом весов — честная подсказка.
# Запуск: python3 tests/wake_ready_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
MOCK="""window.__wl={req:0,rel:0,on:false};Object.defineProperty(navigator,'wakeLock',{value:{request:async()=>{__wl.req++;__wl.on=true;const L={h:[],addEventListener(e,f){this.h.push(f)},release:async function(){__wl.rel++;__wl.on=false;this.h.forEach(f=>f())}};return L;}},configurable:true});"""
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context();await ctx.add_init_script(MOCK);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';coolOffer=function(){}")
    await pg.wait_for_timeout(3200)
    ok('без тренировки экран может гаснуть',await pg.evaluate("!__wl.on"))
    await pg.evaluate("startWorkout({name:'Т',focus:'т',sec:'body',ex:[['Жим штанги лёжа',3,'8',60]]},false);el('dayStart').click()");await pg.wait_for_timeout(700)
    ok('во время тренировки экран не гаснет',await pg.evaluate("__wl.on"))
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>s.done=true));finishWorkout()");await pg.wait_for_timeout(3500)
    ok('после тренировки — снова обычный режим',await pg.evaluate("!__wl.on&&__wl.rel>=1"))
    # готовность
    await pg.evaluate("document.querySelector('.ready .seg-b[data-ready=\"Устал\"]').click()")
    await pg.reload();await pg.wait_for_timeout(400)
    ok('после перезагрузки «Устал» сохранился',await pg.evaluate("readiness==='Устал'&&el('readyState').textContent==='Устал'"))
    await pg.evaluate("el('login').style.display='none';(()=>{const P=g2New({});const v=g2Store();v.progs.push(P);v.activeId=P.id;g2MainKeysOf(P,0).forEach(k=>{P.st[0].ws[k]={w:G2X[k].bw?5:40};});P.st[0].setup=true;g2Save(v);startWorkout(g2Build(g2Active(),g2NextSlot(g2Active())),true);})()");await pg.wait_for_timeout(150)
    t=await pg.evaluate("el('dayReady').textContent")
    ok('в программе с расчётом весов — честная подсказка',('не меняется' in t) and ('−10 %' not in t),t)
    await pg.evaluate("localStorage.setItem('gym45_ready_v1',JSON.stringify({d:'2020-01-01',v:'Устал'}))");await pg.reload();await pg.wait_for_timeout(400)
    ok('на следующий день — снова «Норма»',await pg.evaluate("readiness==='Норма'"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
