# Питание: умные блюда (состав кнопками) и меры с граммами вместо «порции».
# Запуск: python3 tests/nt_smart_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
SHOT=os.environ.get('SHOT')
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(500);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    await E("FOOD_DAY=null;renderFood();show('food');ntTab('diary')");await pg.wait_for_timeout(200)
    async def search(q):
      await pg.fill('#ntQ',q);await pg.wait_for_timeout(150)
    await search('яичница')
    r=await E("[...el('ntHits').querySelectorAll('.nt-hit')].map(b=>b.textContent)")
    ok('«яичница»: первым — умное блюдо «собрать состав», старой «порции 250 г» нет',r and r[0].startswith('Яичница (глазунья)') and not any(x.startswith('Яичница') and 'ккал' in x for x in r),r)
    await E("el('ntHits').querySelector('.nt-hit-smart').click()");await pg.wait_for_timeout(150)
    qs=await E("[...el('ntSmartQ').querySelectorAll('.nt-sq>span')].map(s=>s.textContent)")
    ok('спрашивает: сколько яиц, на чём жарил, добавки',qs[:3]==['Сколько яиц','На чём жарил','Добавки · можно несколько'],qs)
    # 3 яйца, масло 1 ст. л., сыр
    await E("""(()=>{const g=[...el('ntSmartQ').querySelectorAll('.nt-sq')];const pick=(gi,t)=>[...g[gi].querySelectorAll('button')].find(b=>b.textContent.startsWith(t)).click();
      pick(0,'3');})()""")
    await E("[...el('ntSmartQ').querySelectorAll('.nt-sq')][1].querySelectorAll('button')[2].click()")
    await E("[...[...el('ntSmartQ').querySelectorAll('.nt-sq')][2].querySelectorAll('button')].find(b=>b.textContent.startsWith('Сыр')).click()")
    res=await E("el('ntSmartRes').textContent")
    # 150 г яиц 214,5 + масло 10 г 89,9 + сыр 20 г 71,2 = 375,6
    ok('3 яйца + 1 ст. л. масла + сыр = 376 ккал, 180 г',('376 ккал' in res) and ('≈180 г' in res),res[:160])
    ok('видно состав по ингредиентам',('Яйцо 150 г' in res) and ('Растительное масло 10 г' in res) and ('Сыр твёрдый 20 г' in res))
    await E("el('ntSmartAdd').click()");await pg.wait_for_timeout(150)
    d=await E("NT_DRAFT.map(i=>[i.name,Math.round(i.kcal),i.g])")
    ok('в приёме: «Яичница из 3 яиц + сыр», 376 ккал',d==[['Яичница из 3 яиц + сыр',376,180]],d)
    # запоминает выбор
    await search('глазунья');await E("el('ntHits').querySelector('.nt-hit-smart').click()");await pg.wait_for_timeout(100)
    ok('в следующий раз — тот же выбор уже нажат',await E("el('ntSmartRes').textContent.includes('376 ккал')"))
    # гречка: готовая vs сухая
    await search('гречка');await E("el('ntHits').querySelector('.nt-hit-smart').click()");await pg.wait_for_timeout(100)
    r1=await E("el('ntSmartRes').textContent")
    await E("[...[...el('ntSmartQ').querySelectorAll('.nt-sq')][0].querySelectorAll('button')].find(b=>b.textContent==='Сухой · 100 г').click()")
    r2=await E("el('ntSmartRes').textContent")
    ok('гречка готовая 200 г ≈ 250 ккал, сухая 100 г = 313 ккал',('250 ккал' in r1) and ('313 ккал' in r2),[r1[:70],r2[:70]])
    # суп по тарелке
    await search('борщ');r=await E("[...el('ntHits').querySelectorAll('.nt-hit')].map(b=>b.textContent)")
    ok('«борщ» → «Суп (тарелка)» с выбором тарелки',r[0].startswith('Суп (тарелка)'),r)
    # меры с граммами
    await search('плов');await E("[...el('ntHits').querySelectorAll('.nt-hit')].find(b=>b.textContent.startsWith('Плов')).click()");await pg.wait_for_timeout(100)
    u=await E("[...el('ntQUnit').options].map(o=>o.textContent)")
    sel=await E("el('ntQUnit').selectedOptions[0].textContent")
    ok('плов: тарелки с граммами, по умолчанию обычная 300 г',u[:3]==['Небольшая тарелка · 200 г','Обычная тарелка · 300 г','Большая тарелка · 400 г'] and sel=='Обычная тарелка · 300 г',u)
    ok('нигде нет слова «Порции»',not any('Порци' in x for x in u))
    await E("el('ntQAdd').click()");await pg.wait_for_timeout(100)
    ok('в приёме у плова видно «обычная тарелка · 300 г»',await E("NT_DRAFT[1].qty==='обычная тарелка'&&NT_DRAFT[1].g===300"),await E("NT_DRAFT[1]"))
    await search('яйцо');await E("[...el('ntHits').querySelectorAll('.nt-hit')].find(b=>/^Яйц/.test(b.textContent)&&!b.classList.contains('nt-hit-smart')).click()");await pg.wait_for_timeout(100)
    ok('яйцо: «Штуки · 1 яйцо ≈ 50 г без скорлупы»',await E("[...el('ntQUnit').options].some(o=>o.textContent==='Штуки · 1 яйцо ≈ 50 г без скорлупы')"),await E("[...el('ntQUnit').options].map(o=>o.textContent)"))
    await search('лагман');await E("[...el('ntHits').querySelectorAll('.nt-hit')].find(b=>b.textContent.startsWith('Лагман')).click()");await pg.wait_for_timeout(100)
    ok('лагман: тарелки 280/400/520 г вместо «порции»',await E("[...el('ntQUnit').options].map(o=>o.textContent).slice(0,3).join('|')")=='Небольшая тарелка · 280 г|Обычная тарелка · 400 г|Большая тарелка · 520 г')
    # запись в дневник
    await pg.fill('#ntQ','');await E("el('ntDraftSave').click()");await pg.wait_for_timeout(200)
    r=await E("(()=>{const x=foodGet().slice(-1)[0];return [x.kcal,x.items.length,!!x.items[0].parts,x.name]})()")
    ok('записалось в дневник, у яичницы сохранён состав',r[0]>376 and r[1]==2 and r[2],r)
    if SHOT:
      await search('омлет');await E("el('ntHits').querySelector('.nt-hit-smart').click()");await pg.wait_for_timeout(150)
      await E("el('ntBuilder').scrollIntoView()");await pg.screenshot(path=SHOT,full_page=False)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
