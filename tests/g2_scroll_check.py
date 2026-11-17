# GVT: текущий подход всегда виден в таблице подходов после отметки (разные iPhone)
# Запуск: python3 tests/g2_scroll_check.py index.html
import asyncio,sys,os,re,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
HELP=re.search(r'HELP="""(.*?)"""',open('tests/g2_waves_check.py',encoding='utf-8').read(),re.S).group(1)
R=[]
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(**p.devices[DEV]);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(400);await pg.evaluate("el('login').style.display='none'")
    await pg.evaluate(HELP)
    _o=(await pg.evaluate("(()=>{T.fresh(0,{});return T.open()||(()=>{const m=el('gvtModal');if(!m.hidden&&el('g2c6Go')){el('g2c6Go').click();return T.begin();}return 'no'})()})()"))
    await pg.evaluate("el('gvtModal').hidden=true;current.sets.forEach(ss=>ss.forEach(s=>{s.w=s.w||60;s.pw=s.pw||60}));show('workout');renderWorkout()");await pg.wait_for_timeout(500)
    res=[]
    for k in range(17):
      await pg.evaluate("(()=>{const on=document.querySelector('.g2-cell.on .chk');on&&on.click();})()");await pg.wait_for_timeout(900)
      v=await pg.evaluate("""(()=>{const on=document.querySelector('.g2-cell.on'),box=document.querySelector('.g2-sets');if(!on)return 'none';const a=on.getBoundingClientRect(),bb=box.getBoundingClientRect();
        return [Math.round(a.top-bb.top),Math.round(bb.bottom-a.bottom),Math.round(bb.height),a.top>=bb.top-1&&a.bottom<=bb.bottom+1&&a.bottom<=innerHeight]})()""")
      res.append(v)
    vis=all(isinstance(x,list) and x[3] for x in res);print(('PASS ' if vis else 'FAIL ')+DEV+': текущий подход виден после каждой отметки (17 отметок)');R.append(vis)
    R.append(not errs);await b.close()
for DEV in ['iPhone 13','iPhone 14 Pro Max','iPhone SE']:asyncio.run(m())
print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
