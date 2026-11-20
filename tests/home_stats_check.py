# Рабочий стол: вода (кольцо %, нажатие +стакан, долгое — раздел «Вода») и питание (ккал + Б/Ж/У к норме).
# Запуск: python3 tests/home_stats_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(500);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    await E("""(()=>{localStorage.setItem(NTK_T,JSON.stringify({sex:'male',age:45,weight:95,height:180,activity:'moderate',goal:'lose',updatedAt:1}));
      const t=localDate();foodSet([{date:t,kcal:1450,p:95,f:40,c:150,name:'x'}]);const s=wtSt();s.days={};s.mode='glass';wtSave(s);show('home');renderToday();})()""")
    await pg.wait_for_timeout(300)
    r=await E("(()=>{const w=el('tdWater'),f=el('tdFood'),m=el('tdMac');return [!!w,!!f,w&&w.textContent,f&&f.textContent+(m?m.textContent:'')]})()")
    ok('на рабочем столе — вода и питание',r[0] and r[1],r)
    ok('питание: ккал из нормы и Б/Ж/У к норме','1\xa0450' in r[3] and 'Б' in r[3] and 'У' in r[3],r[3])
    await pg.tap('#tdWater');await pg.wait_for_timeout(300)
    r=await E("[wtDrunk(),currentScreen,el('tdWater').textContent]")
    ok('нажатие на воду: +250 мл, остаёмся на рабочем столе',r[0]==250 and r[1]=='home' and '0,25' in r[2],r)
    box=await pg.locator('#tdWater').bounding_box()
    await pg.mouse.move(box['x']+20,box['y']+20);await pg.mouse.down();await pg.wait_for_timeout(800);await pg.mouse.up();await pg.wait_for_timeout(400)
    r=await E("[wtDrunk(),currentScreen]")
    ok('долгое нажатие: открывает раздел «Вода», без лишнего стакана',r==[250,'food'],r)
    await E("show('home');renderToday()");await pg.tap('#tdFood');await pg.wait_for_timeout(300)
    ok('нажатие на питание — дневник',await E("currentScreen==='food'&&NT_TAB==='diary'"))
    await E("localStorage.removeItem(NTK_T);show('home');renderToday()")
    r=await E("el('tdFood').textContent")
    ok('нормы нет — «Рассчитать норму»','Рассчитать норму' in r,r)
    await E("show('home');(()=>{localStorage.setItem(NTK_T,JSON.stringify({sex:'male',age:45,weight:95,height:180,activity:'moderate',goal:'lose',updatedAt:1}));renderToday();scrollTo(0,0)})()")

    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}')
