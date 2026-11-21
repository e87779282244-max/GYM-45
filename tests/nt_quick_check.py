# Питание, быстрый ввод: повторить вчерашний приём, мои блюда, частое, избранное.
# Запуск: python3 tests/nt_quick_check.py index.html
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
    # вчера: завтрак из двух позиций (дважды за 2 дня — станет «частым»)
    await E("""(()=>{const t=localDate(),y=localDate(new Date(Date.now()-864e5)),y2=localDate(new Date(Date.now()-2*864e5));
      const it=[{id:'s_fried',name:'Яичница из 3 яиц + сыр',g:180,qty:'',kcal:376,p:23.7,f:29.8,c:1.2},{id:'x_wbread',name:'Хлеб белый',g:30,qty:'1 шт.',kcal:76,p:2.4,f:0.9,c:14.7}];
      localStorage.setItem(FOODK,JSON.stringify([{id:'a',date:y2,meal:'Завтрак',name:'Завтрак: x',kcal:452,p:26,f:31,c:16,src:'builder',items:it},{id:'b',date:y,meal:'Завтрак',name:'Завтрак: x',kcal:452,p:26,f:31,c:16,src:'builder',items:it},{id:'c',date:y,meal:'Обед',name:'Обед: Плов',kcal:615,p:21,f:27,c:72}]));})()""")
    await E("FOOD_DAY=null;renderFood();show('food');ntTab('diary');el('ntMeal').value='Завтрак';el('ntMeal').dispatchEvent(new Event('change'))");await pg.wait_for_timeout(200)
    rows=await E("[...el('ntQuick').querySelectorAll('.nt-qrow>span')].map(s=>s.textContent)")
    ok('над поиском: «Повторить» и «Частое»',rows[:2]==['Повторить','Частое'],rows)
    ok('«↻ Вчерашний завтрак · 452 ккал»',await E("[el('ntQuick').querySelector('[data-a=rep] b').textContent,el('ntQuick').querySelector('[data-a=rep] small').textContent]")==['↻ Вчерашний завтрак','452 ккал'])
    await E("el('ntQuick').querySelector('[data-a=rep]').click()");await pg.wait_for_timeout(100)
    ok('повтор — 2 позиции в приёме, 452 ккал, одно нажатие',await E("NT_DRAFT.length===2&&Math.round(NT_DRAFT.reduce((a,i)=>a+i.kcal,0))===452"))
    ok('частое: «Яичница из 3 яиц + сыр · 180 г»',await E("[...el('ntQuick').querySelectorAll('[data-a=fr] b')].map(b=>b.textContent).includes('Яичница из 3 яиц + сыр · 180 г')"),await E("el('ntQuick').innerText"))
    # мои блюда
    await E("el('ntMyOpen').click()");await E("el('ntMyName').value='Мой завтрак';el('ntMySave').click()");await pg.wait_for_timeout(100)
    ok('сохранено «Мой завтрак»',await E("ntQ().dishes[0].name==='Мой завтрак'&&ntQ().dishes[0].items.length===2"))
    await E("el('ntDraftSave').click()");await pg.wait_for_timeout(200)
    await E("[...el('ntQuick').querySelectorAll('[data-a=my]')][0].click()");await pg.wait_for_timeout(100)
    ok('«Мой завтрак» → в приём одним нажатием',await E("NT_DRAFT.length===2"))
    await E("el('ntDraftSave').click()");await pg.wait_for_timeout(150)
    ok('обед вчера «итогом» тоже повторяется',await E("el('ntMeal').value='Обед';el('ntMeal').dispatchEvent(new Event('change'));el('ntQuick').querySelector('[data-a=rep]').click();NT_DRAFT.length===1&&NT_DRAFT[0].kcal===615&&NT_DRAFT[0].name==='Плов'"))
    await E("NT_DRAFT.length=0;ntDraftRender()")
    # избранное
    await pg.fill('#ntQ','овсянка');await pg.wait_for_timeout(100);await E("el('ntHits').querySelector('.nt-hit-smart').click()");await E("el('ntFavSmart').click()")
    ok('звёздочка: «★ В избранном»',await E("el('ntFavSmart').textContent")=='★ В избранном')
    await pg.fill('#ntQ','кефир');await pg.wait_for_timeout(100);await E("[...el('ntHits').querySelectorAll('.nt-hit')][0].click()");await E("el('ntFavPick').click()")
    await pg.fill('#ntQ','');await pg.wait_for_timeout(100);await E("el('ntPickBox').hidden=true;ntQuickRender()")
    fv=await E("[...el('ntQuick').querySelectorAll('[data-a=fv] b')].map(b=>b.textContent)")
    ok('избранное: кефир и овсянка',len(fv)==2 and fv[1]=='Овсяная каша' and 'ефир' in fv[0],fv)
    await E("[...el('ntQuick').querySelectorAll('[data-a=fv]')][1].click()");await pg.wait_for_timeout(100)
    ok('нажатие на избранное открывает выбор состава',await E("!el('ntSmartBox').hidden&&NT_SMART_CUR.rec.id==='s_oat'"))
    ok('избранное и мои блюда уходят в облако',await E("!!cloudSnapshot().nutrition.quick&&cloudSnapshot().nutrition.quick.dishes.length===1"))
    if SHOT:
      await pg.fill('#ntQ','');await E("el('ntSmartBox').hidden=true;NT_SMART_CUR=null;el('ntMeal').value='Завтрак';ntQuickRender();el('ntBuilder').scrollIntoView()");await pg.wait_for_timeout(150);await pg.screenshot(path=SHOT)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
