# GVT: после сворачивания/разворачивания приложения анимации упражнений возвращаются (режим «тесно» не залипает).
# Запуск: python3 tests/g2_resume_check.py index.html
import asyncio,sys,os,re,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
HELP=re.search(r'HELP="""(.*?)"""',open('tests/g2_waves_check.py',encoding='utf-8').read(),re.S).group(1)
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
VIS="(()=>{const m=document.querySelector('.g2-card .g2-media');return !!m&&m.getBoundingClientRect().height>40})()"
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(**p.devices[DEV]);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(400);await pg.evaluate("el('login').style.display='none'")
    await pg.evaluate(HELP)
    await pg.evaluate("(()=>{T.fresh(0,{});return T.open()||(()=>{const m=el('gvtModal');if(!m.hidden&&el('g2c6Go')){el('g2c6Go').click();return T.begin();}return 'no'})()})()")
    await pg.evaluate("el('gvtModal').hidden=true;current.sets.forEach(ss=>ss.forEach(s=>{s.w=s.w||60;s.pw=s.pw||60}));show('workout');renderWorkout()");await pg.wait_for_timeout(600)
    ok(DEV+': анимации видны',await pg.evaluate(VIS))
    vp=pg.viewport_size
    # имитация возврата из фона: iOS на миг отдаёт маленький экран
    await pg.set_viewport_size({'width':vp['width'],'height':260});await pg.wait_for_timeout(300)
    ok(DEV+': на крошечном экране картинки убраны (тесно)',await pg.evaluate("document.querySelector('.g2-card').classList.contains('g2-tight')"))
    await pg.set_viewport_size(vp);await pg.evaluate("document.dispatchEvent(new Event('visibilitychange'));dispatchEvent(new Event('pageshow'))");await pg.wait_for_timeout(1300)
    ok(DEV+': после возврата анимации снова видны',await pg.evaluate(VIS))
    ok(DEV+': без ошибок JS',not errs,errs[:2]);await b.close()
for DEV in ['iPhone 13','iPhone 14 Pro Max']:asyncio.run(m())
print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
