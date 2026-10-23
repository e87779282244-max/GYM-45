# GVT 2.0: замена упражнения без веса — окно стартового веса (ПМ этапа или 1ПМ → %), кнопка «Задать вес».
# Запуск: python3 tests/gvt_swap_check.py index.html [папка_скриншотов]
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
    await pg.evaluate("el('login').style.display='none'")
    await pg.evaluate("""(()=>{const P=g2New({});const v=g2Store();v.progs=v.progs||[];v.progs.push(P);v.activeId=P.id;
      g2MainKeysOf(P,0).forEach(k=>{P.st[0].ws[k]={w:G2X[k].bw?5:40};});P.st[0].setup=true;g2Save(v);
      const PP=g2Active(),sl=g2NextSlot(PP);startWorkout(g2Build(PP,sl),true);el('dayStart').click();})()""")
    await pg.wait_for_timeout(200)
    ok('тренировка GVT открыта',await pg.evaluate("!!(current&&current.program.g2)"))
    i=await pg.evaluate("current.program.gx.findIndex(g=>g.key==='dDecl')")
    await pg.evaluate(f"g2SwapOpen({i})");await pg.evaluate("el('gvtMbox').querySelector('[data-k=bench]').click()");await pg.wait_for_timeout(150)
    ok('после замены на жим штанги без веса — окно стартового веса',await pg.evaluate("!el('gvtModal').hidden&&!!el('g2aw')&&!!el('g2arm')&&el('gvtMbox').innerText.includes('60 %')"))
    if O:await pg.screenshot(path=O+'/askw.png')
    await pg.evaluate("el('g2arm').value='100';el('g2aGo').click()");await pg.wait_for_timeout(150)
    ok('1ПМ 100 → 60 кг во всех подходах',await pg.evaluate(f"current.sets[{i}].every(s=>s.pw===60&&s.w===60)"),await pg.evaluate(f"current.sets[{i}][0].pw"))
    ok('вес сохранён в программе для жима',await pg.evaluate("g2Active().st[0].ws.bench.w===60"))
    # кнопка «Задать вес» видна, если веса нет
    await pg.evaluate(f"current.sets[{i}].forEach(s=>{{s.pw=0;s.w=0}});current.idx=0;renderWorkout()")
    ok('при пустом весе есть кнопка «Задать вес»',await pg.evaluate("!!el('exList').querySelector('[data-setw]')"))
    if O:await pg.screenshot(path=O+'/setw.png')
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f"\n{sum(R)}/{len(R)} PASS");sys.exit(0 if all(R) else 1)
asyncio.run(m())
