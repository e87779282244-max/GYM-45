# Справочник продуктов: дополнение (продукты по таблице состава + блюда по рецептуре) в поиске питания.
# Запуск: python3 tests/food_ref_check.py index.html
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
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300)
    ok('в справочнике ≥ 550 позиций, id уникальны',await pg.evaluate("(()=>{const A=ntAllFoods();return A.length>=550&&new Set(A.map(x=>x.id)).size===A.length})()"),await pg.evaluate("ntAllFoods().length"))
    ok('КБЖУ правдоподобны: ккал ≈ 4Б+9Ж+4У (±25 %), кроме алкоголя и кислых ягод',await pg.evaluate("[...NT_REF,...NT_OWN].filter(r=>r[1]!=='Алкоголь'&&!['Лимон','Клюква'].includes(r[2])).every(r=>{const c=4*r[4]+9*r[5]+4*r[6];return r[3]>0&&Math.abs(c-r[3])/r[3]<=0.25})"))
    for q,exp in [('манты','Манты с бараниной'),('бешбармак','Бешбармак'),('капучино','Капучино'),('ряженка','Ряженка 4%'),('нут','Нут, сухой'),('креветки','Креветки (мясо)'),('кумыс','Кумыс')]:
      ok(f'поиск «{q}»',await pg.evaluate("([q,e])=>ntAllFoods().some(f=>ntNorm(f.name).includes(q)&&f.name.startsWith(e))",[q,exp]))
    ok('манты — штуками по 50 г, капучино — стаканами',await pg.evaluate("(()=>{const A=ntAllFoods();return A.find(f=>f.name==='Манты с бараниной').piece===50&&A.find(f=>f.name.startsWith('Капучино')).cup===250})()"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
