# Питание: штрихкод — поиск в Open Food Facts (ответ подменён), сохранение в «Мои продукты», ввод с упаковки, если нет в базе.
# Запуск: python3 tests/nt_barcode_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools,json
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
FOUND={"status":1,"product":{"code":"4600000000017","product_name_ru":"Творог 5%","brands":"Простоквашино","serving_quantity":180,"nutriments":{"energy-kcal_100g":121,"proteins_100g":17.2,"fat_100g":5,"carbohydrates_100g":1.8}}}
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    calls=[]
    async def route(r):
      u=r.request.url;calls.append(u)
      if '4600000000017' in u:await r.fulfill(status=200,content_type='application/json',body=json.dumps(FOUND),headers={'access-control-allow-origin':'*'})
      else:await r.fulfill(status=200,content_type='application/json',body=json.dumps({"status":0}),headers={'access-control-allow-origin':'*'})
    await pg.route('https://world.openfoodfacts.org/**',route)
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(500);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    await E("FOOD_DAY=null;renderFood();show('food');ntTab('diary')")
    ok('у поиска есть кнопка штрихкода',await E("!!el('ntScan')&&el('ntScan').offsetWidth>40"))
    await E("el('ntScan').click()");await pg.wait_for_timeout(300)
    ok('окно штрихкода открылось, без камеры — можно ввести цифры',await E("!el('bcModal').hidden&&!!el('bcCode')"),await E("el('bcMsg').textContent"))
    await pg.fill('#bcCode','4600000000017');await E("el('bcFind').click()");await pg.wait_for_timeout(500)
    ok('найден в Open Food Facts: «Творог 5% · Простоквашино», 121 ккал',await E("NT_PICK&&NT_PICK.name==='Творог 5% · Простоквашино'&&NT_PICK.kcal===121&&NT_PICK.bc==='4600000000017'"),await E("NT_PICK&&[NT_PICK.name,NT_PICK.kcal]"))
    ok('мера «порция с упаковки 180 г», источник Open Food Facts',await E("[...el('ntQUnit').options].some(o=>o.text.includes('180 г'))&&el('ntPickRes').textContent.includes('Open Food Facts')"),await E("[...el('ntQUnit').options].map(o=>o.text)"))
    ok('сохранён в «Мои продукты»',await E("ntCustom().items.some(i=>i.bc==='4600000000017')"))
    n=len(calls)
    await E("el('ntScan').click()");await pg.wait_for_timeout(200);await pg.fill('#bcCode','4600000000017');await E("el('bcFind').click()");await pg.wait_for_timeout(300)
    ok('второй раз — без интернета, из своих продуктов',len(calls)==n and await E("NT_PICK&&NT_PICK.bc==='4600000000017'"))
    # нет в базе → ввод с упаковки, штрихкод запоминается
    await E("el('ntScan').click()");await pg.wait_for_timeout(200);await pg.fill('#bcCode','4870000000002');await E("el('bcFind').click()");await pg.wait_for_timeout(500)
    ok('нет в базе → открылась форма «Свой продукт»',await E("el('bcModal').hidden&&el('ntCustomWrap').open&&NT_BC_PENDING==='4870000000002'"))
    await E("el('ntCName').value='Курут местный';el('ntCP').value='32';el('ntCF').value='16';el('ntCC').value='9';el('ntCSave').click()");await pg.wait_for_timeout(200)
    await E("el('ntScan').click()");await pg.wait_for_timeout(200);await pg.fill('#bcCode','4870000000002');await E("el('bcFind').click()");await pg.wait_for_timeout(300)
    ok('после ввода — находится по штрихкоду',await E("NT_PICK&&NT_PICK.name==='Курут местный'"))
    await E("el('ntScan').click()");await pg.wait_for_timeout(200);await E("el('bcClose').click()")
    ok('«Закрыть» закрывает окно',await E("el('bcModal').hidden"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
