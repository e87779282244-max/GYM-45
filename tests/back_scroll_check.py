# «Назад» возвращает на то же место списка (прокрутка сохраняется).
# Запуск: python3 tests/back_scroll_check.py index.html [папка_скриншотов]
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
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';show('programs');show('body')");await pg.wait_for_timeout(150)
    await pg.evaluate("[...el('bodyProgs').querySelectorAll('.disc')].find(b=>b.textContent.includes('Фулбади для новичков')).scrollIntoView({block:'center'})");await pg.wait_for_timeout(100)
    y0=await pg.evaluate("window.scrollY")
    ok('список прокручен вниз',y0>500,y0)
    await pg.evaluate("[...el('bodyProgs').querySelectorAll('.disc')].find(b=>b.textContent.includes('Фулбади для новичков')).click()");await pg.wait_for_timeout(150)
    ok('новый экран открывается сверху',await pg.evaluate("window.scrollY===0&&currentScreen==='bodyprog'"))
    await pg.evaluate("document.querySelector('#scr-bodyprog .back-btn').click()");await pg.wait_for_timeout(200)
    y1=await pg.evaluate("window.scrollY")
    ok('«Назад» — на то же место списка',abs(y1-y0)<5 and await pg.evaluate("currentScreen==='body'"),(y0,y1))
    # два уровня: список → программа → день → назад → назад
    await pg.evaluate("[...el('bodyProgs').querySelectorAll('.disc')].find(b=>b.textContent.includes('Heavy Duty')).scrollIntoView({block:'center'})");await pg.wait_for_timeout(80)
    y2=await pg.evaluate("window.scrollY")
    await pg.evaluate("[...el('bodyProgs').querySelectorAll('.disc')].find(b=>b.textContent.includes('Heavy Duty')).click()");await pg.wait_for_timeout(150)
    await pg.evaluate("el('bodyDays').querySelectorAll('.disc')[2].scrollIntoView({block:'center'})");await pg.wait_for_timeout(80)
    y3=await pg.evaluate("window.scrollY")
    await pg.evaluate("[...el('bodyDays').querySelectorAll('.disc')].filter(b=>b.textContent.includes('Heavy Duty ·'))[1].click()");await pg.wait_for_timeout(150)
    await pg.evaluate("document.querySelector('#scr-day .back-btn').click()");await pg.wait_for_timeout(200)
    y4=await pg.evaluate("window.scrollY")
    ok('из дня — назад к программе на то же место',await pg.evaluate("currentScreen==='bodyprog'") and abs(y4-y3)<5,(y3,y4))
    await pg.evaluate("document.querySelector('#scr-bodyprog .back-btn').click()");await pg.wait_for_timeout(200)
    y5=await pg.evaluate("window.scrollY")
    ok('ещё раз назад — список на месте Heavy Duty',await pg.evaluate("currentScreen==='body'") and abs(y5-y2)<5,(y2,y5))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f'\n{sum(R)}/{len(R)} PASS');sys.exit(0 if all(R) else 1)
asyncio.run(m())
