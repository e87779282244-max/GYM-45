# Параллельные программы: начать другую тренировку посреди текущей — «Отложить и начать»; отложенная сохраняется
# со всеми отметками, на главной «Продолжить», после возврата и завершения записывается как обычно; облако не теряет.
# Запуск: python3 tests/park_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    # GVT 2.0 и стритлифтинг (ЛЗ) активны одновременно
    await E("""(()=>{const v=g2Store();const P=g2New({stage:0});P.st[0].setup=true;g2MainKeysOf(P,0).forEach(k=>P.st[0].ws[k]={w:60});v.progs.push(P);v.activeId=P.id;g2Save(v);})()""")
    await E("document.querySelector('.disc[data-disc=\"Стритлифтинг\"]').click()");await pg.wait_for_timeout(100)
    await E("[...el('streetDays').querySelectorAll('.disc')].find(b=>b.textContent.includes('Рождённый ползать')).click()");await pg.wait_for_timeout(100)
    await pg.fill('#lzRm_pull','20');await pg.fill('#lzRm_dip','30');await pg.click('#lzGo');await pg.wait_for_timeout(100)
    ok('две программы активны одновременно',await E("(()=>{const k=mpList().map(x=>x.k);return k.includes('gvt2')&&k.includes('lz')})()"))
    # начал GVT, отметил 3 подхода
    await E("show('gvt');g2Render();el('g2Open').click();el('dayStart').click()");await pg.wait_for_timeout(100)
    await E("current.sets[0][0].done=true;current.sets[0][1].done=true;current.sets[0][1].w=62.5;current.sets[1][0].done=true;saveDraft()")
    # открыл стритлифтинг и нажал «Начать»
    await E("const P=lzActive(),st=lzState(P);startWorkout(lzPlan(P,st),true);el('dayStart').click()");await pg.wait_for_timeout(100)
    ok('вопрос «Отложить и начать», тренировка не заменена молча',await E("!el('gvtModal').hidden&&el('gvtMbox').textContent.includes('Отложить')&&current.program.name.startsWith('GVT')"))
    await E("el('pkX').click()")
    ok('«Отмена» — GVT продолжается',await E("el('gvtModal').hidden&&current.program.name.startsWith('GVT')"))
    await E("el('dayStart').click()");await pg.wait_for_timeout(50);await E("el('pkGo').click()");await pg.wait_for_timeout(100)
    ok('«Отложить и начать»: идёт стритлифтинг',await E("current&&current.program.name.startsWith('Рождённый ползать')"))
    r=await E("(()=>{const L=parkList();return {n:L.length,done:wkDoneN(L[0]),w:L[0].sets[0][1].w,name:L[0].program.name}})()")
    ok('GVT отложена со всеми отметками (3 подхода, вес 62,5)',r['n']==1 and r['done']==3 and r['w']==62.5,r)
    # на главной — «Продолжить»
    await E("show('home');renderToday()")
    ok('на главной «⏸ Отложена: GVT» и «Продолжить»',await E("el('dashToday').textContent.includes('Отложена: GVT')&&!!el('dashToday').querySelector('[data-pk]')"))
    # закончил стритлифтинг
    await E("current.sets.forEach(se=>se.forEach(s=>s.done=true));finishWorkout()");await pg.wait_for_timeout(200)
    ok('стритлифтинг записан',await E("lzActive().recs.length===1"))
    # вернулся к GVT
    await E("show('home');renderToday();el('dashToday').querySelector('[data-pk]').click()");await pg.wait_for_timeout(100)
    r=await E("({name:current&&current.program.name,done:wkDoneN(current),w:current.sets[0][1].w,park:parkList().length,scr:currentScreen})")
    ok('«Продолжить»: GVT с теми же отметками, отложенных больше нет',r['name'].startswith('GVT') and r['done']==3 and r['w']==62.5 and r['park']==0 and r['scr']=='workout',r)
    await E("current.sets.forEach(se=>se.forEach(s=>{s.done=true;s.r=s.pr||10;}));finishWorkout()");await pg.wait_for_timeout(200)
    ok('GVT завершена и записана в программу',await E("g2Active().recs.length===1&&g2Active().recs[0].ex[0].sets[1].w===62.5"))
    # без отмеченных подходов — начинается сразу, без вопроса
    await E("el('gvtModal').hidden=true;show('gvt');g2Render();el('g2Open').click();el('dayStart').click()");await pg.wait_for_timeout(100)
    await E("const P=lzActive(),st=lzState(P);startWorkout(lzPlan(P,st),true);el('dayStart').click()");await pg.wait_for_timeout(100)
    ok('ничего не отмечено — новая начинается сразу, ничего не откладывается',await E("el('gvtModal').hidden&&current.program.name.startsWith('Рождённый ползать')&&parkList().length===0"))
    # облако: отложенная тренировка с другого устройства появляется
    r=await E("""(async()=>{const w=JSON.parse(JSON.stringify(current));w.startedAt="2026-01-01T10:00:00Z";w.parkedAt=w.startedAt;const snap=Object.assign(cloudSnapshot(),{parked:[w]});
      const doc={get:async()=>({exists:true,data:()=>snap}),set:async()=>{}};CLOUD={db:{doc:()=>doc},user:{}};await cloudInit();CLOUD=null;cloudReady=false;return [parkList().length,!!cloudSnapshot().parked]})()""")
    ok('облако: отложенная с другого устройства подтянулась, в снимке есть',r==[1,True],r)
    # удалить отложенную — двойным нажатием
    await E("current=null;clearDraft();show('home');renderToday();const b=el('dashToday').querySelector('[data-pkx]');b.click();b.click()")
    ok('✕ дважды — отложенная удалена',await E("parkList().length===0"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
