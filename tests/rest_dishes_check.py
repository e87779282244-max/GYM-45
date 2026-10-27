# Питание: 105 блюд ресторана «Хинкали club» + 56 блюд кафе «Хобз» (КБЖУ на 100 г, из таблиц пользователя).
# Запуск: python3 tests/rest_dishes_check.py index.html
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
    ok('105 + 56 блюд, id уникальны',await pg.evaluate("(()=>{const a=ntAllFoods();return a.filter(f=>/^r_/.test(f.id)).length===105&&a.filter(f=>/^k_/.test(f.id)).length===56&&new Set(a.map(f=>f.id)).size===a.length})()"))
    ok('названия уникальны',await pg.evaluate("(()=>{const n=ntAllFoods().map(f=>f.name);return new Set(n).size===n.length})()"))
    ok('КБЖУ как в таблице (хачапури по-аджарски 276, шакшука 124.8)',await pg.evaluate("(()=>{const a=ntAllFoods();const h=a.find(f=>f.name==='Хачапури по-аджарски (Хинкали club)'),s=a.find(f=>f.name==='Шакшука (Хобз)');return h.kcal===276&&h.p===11.5&&s.kcal===124.8&&s.c===12.6})()"))
    await pg.evaluate("show('food')");await pg.wait_for_timeout(100)
    await pg.evaluate("el('ntQ').value='хачапури аджарски';ntSearch();el('ntHits').querySelector('.nt-hit').click()");await pg.wait_for_timeout(80)
    await pg.evaluate("el('ntQAmt').value='350';ntPickCalc()")
    ok('350 г хачапури = 966 ккал, мера — граммы',await pg.evaluate("el('ntQUnit').value==='g'&&el('ntPickRes').textContent.includes('966')&&el('ntPickRes').textContent.includes('Хинкали club')"),await pg.evaluate("el('ntPickRes').innerText"))
    await pg.evaluate("el('ntQ').value='хобз';ntSearch()")
    ok('поиск по названию заведения',await pg.evaluate("el('ntHits').querySelectorAll('.nt-hit').length===12"))
    ok('без ошибок JS',not errs,errs)
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
