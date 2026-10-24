# Питание: 50 готовых блюд в справочнике «Собрать приём пищи».
# Запуск: python3 tests/dishes_check.py index.html [папка_скриншотов]
import asyncio,os,sys,shutil,tempfile,http.server,threading,functools
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
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    ok('50 блюд в справочнике, id уникальны',await pg.evaluate("(()=>{const a=ntAllFoods(),d=a.filter(f=>/^d_/.test(f.id));return d.length===50&&new Set(a.map(f=>f.id)).size===a.length})()"))
    ok('названия не дублируют старые продукты',await pg.evaluate("(()=>{const n=ntAllFoods().map(f=>f.name);return new Set(n).size===n.length})()"))
    ok('ккал как в таблице (сырники 218, шашлык 290)',await pg.evaluate("(()=>{const a=ntAllFoods();return a.find(f=>f.name==='Сырники').kcal===218&&a.find(f=>f.name==='Шашлык свиной').kcal===290})()"))
    await pg.evaluate("show('food')");await pg.wait_for_timeout(100)
    await pg.evaluate("el('ntQ').value='суп';ntSearch()")
    ok('поиск «суп»: 4 блюда со словом «суп»',await pg.evaluate("el('ntHits').querySelectorAll('.nt-hit').length===4"),await pg.evaluate("el('ntHits').innerText"))
    await pg.evaluate("el('ntQ').value='сырники';ntSearch();el('ntHits').querySelector('.nt-hit').click()");await pg.wait_for_timeout(80)
    ok('по умолчанию 1 порция 250 г = 545 ккал',await pg.evaluate("el('ntQUnit').value==='piece'&&el('ntQUnit').options[0].text==='Порции'&&el('ntPickRes').textContent.includes('545')"),await pg.evaluate("el('ntPickRes').innerText"))
    if SHOT:await pg.screenshot(path=SHOT+'/dish-pick.png',full_page=False)
    await pg.evaluate("ntDraftAdd()");await pg.wait_for_timeout(80)
    ok('в приёме: «1 порц.»',await pg.evaluate("el('ntDraft').textContent.includes('1 порц.')&&el('ntDraft').textContent.includes('Сырники')"))
    await pg.evaluate("el('ntQ').value='пельмени';ntSearch();el('ntHits').querySelector('.nt-hit').click()")
    ok('старые продукты со штуками не изменились',await pg.evaluate("NT_PICK.id!=='x_dumpl'||el('ntQUnit').options[0].text==='Штуки'"))
    ok('без ошибок JS',not errs,errs)
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
