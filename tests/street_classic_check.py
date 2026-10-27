# Стритлифтинг: «Классический цикл» — одна карточка, внутри 4 дня, тренировка пишется в раздел стритлифтинга.
# Запуск: python3 tests/street_classic_check.py index.html
import asyncio,os,sys,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
HTML=os.path.abspath(sys.argv[1])
tmp=tempfile.mkdtemp();shutil.copy(HTML,tmp+'/index.html')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    await pg.evaluate("document.querySelector('.disc[data-disc=\"Стритлифтинг\"]').click()");await pg.wait_for_timeout(100)
    ok('дни не лежат россыпью в списке',await pg.evaluate("![...el('streetDays').querySelectorAll('.disc')].some(b=>b.textContent.includes('День 1'))"))
    await pg.evaluate("[...el('streetDays').querySelectorAll('.disc')].find(b=>b.textContent.includes('Классический цикл')).click()");await pg.wait_for_timeout(100)
    ok('внутри 4 дня',await pg.evaluate("currentScreen==='bodyprog'&&!el('scr-bodyprog').hidden&&[...el('bodyDays').querySelectorAll('.disc')].filter(b=>/День \\d/.test(b.textContent)).length===4&&el('bodyName').textContent==='Классический цикл'"))
    await pg.evaluate("[...el('bodyDays').querySelectorAll('.disc')].find(b=>b.textContent.includes('День 1')).click()");await pg.wait_for_timeout(100)
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(100)
    await pg.evaluate("current.sets[0].forEach(s=>s.done=true);finishWorkout()");await pg.wait_for_timeout(150)
    ok('тренировка сохранена в разделе стритлифтинга',await pg.evaluate("(()=>{const h=safe.get().slice(-1)[0];return h.name==='День 1 · Подтягивания'&&h.sec==='street'})()"),await pg.evaluate("JSON.stringify(safe.get().slice(-1)[0].sec)"))
    await pg.evaluate("goBack()");await pg.wait_for_timeout(80)
    ok('без ошибок JS',not errs,errs)
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
