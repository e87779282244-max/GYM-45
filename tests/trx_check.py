# TRX убран из направлений (решение владельца 27.10.2026): кнопки нет, старые тренировки TRX остаются в истории
# и в аналитике (вкладка «TRX» появляется, только если такие тренировки есть). Все экраны подключены к навигации.
# Запуск: python3 tests/trx_check.py index.html
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
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';show('programs')");await pg.wait_for_timeout(150)
    d=await pg.evaluate("[...document.querySelectorAll('#scr-programs .disc[data-disc]')].map(b=>b.dataset.disc).join(',')")
    ok('направления без TRX',d=='Бодибилдинг,Пауэрлифтинг,Стритлифтинг,Кроссфит,Стрит воркаут',d)
    ok('все экраны подключены к навигации',await pg.evaluate("(()=>{const ids=new Set(Object.values(scr).map(x=>x&&x.id));return [...document.querySelectorAll('section.screen')].every(s=>ids.has(s.id))})()"))
    await pg.evaluate("show('progress')");await pg.wait_for_timeout(150)
    ok('аналитика без вкладки TRX, если нет таких тренировок',await pg.evaluate("!!el('anDisc')&&![...el('anDisc').querySelectorAll('button')].some(b=>b.dataset.v==='trx')"))
    await pg.evaluate("localStorage.setItem(KEY,JSON.stringify([{date:'2026-10-01',name:'TRX 2 · Full Body Blast',vol:0,sec:'trx',log:{'Отжимания в TRX':[{w:0,r:10,done:true}]}}]));show('home');show('progress')");await pg.wait_for_timeout(150)
    ok('старая тренировка TRX в истории и во вкладке аналитики',await pg.evaluate("safe.get().length===1&&[...el('anDisc').querySelectorAll('button')].some(b=>b.dataset.v==='trx')"))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)} PASS');sys.exit(0 if all(R) else 1)
