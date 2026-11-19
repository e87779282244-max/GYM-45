# Кроссфит и воркаут после перерыва 14+ дней: сами ничего не меняем — предлагаем «Снизить уровень» / «Начать сначала» / «Продолжить как есть».
# Спрашиваем один раз на перерыв; результаты не теряются (при «сначала» — архив).
# Запуск: python3 tests/softbrk_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(400);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate;W=lambda:pg.wait_for_timeout(150)
    modal="(()=>({open:!el('gvtModal').hidden&&!!el('sbRe'),t:el('gvtMbox').textContent,low:!!el('sbLow')}))()"
    # --- кроссфит: второй уровень, последний комплекс 20 дней назад
    await E("""(()=>{const s=cfGet();const lv=CF_CATS[1].k;const ts=Date.now()-20*864e5;s.prog={lvl:lv,ts:ts-1000,start:addDays(localDate(),-21),per:3,round:1};
      const d=CFW.find(x=>cfCatOf(x)===lv);s.res=[{id:'r1',wod:d.id,name:d.name,date:addDays(localDate(),-20),ts:ts,sc:'time',t:300}];cfSave(s);parSet([]);el('gvtModal').hidden=true;cfOpenCat(lv);})()""");await W()
    r=await E(modal)
    ok('кроссфит: перерыв 20 дн. — предложение снизить уровень / начать сначала',r['open'] and r['low'] and 'Перерыв 20 дн.' in r['t'] and 'Сами ничего не меняем' in r['t'],r['t'][:120])
    r=await E("(()=>{el('sbLow').click();const p=cfProg(),s=cfGet();return [p.lvl===CF_CATS[0].k,s.res.length,(parGet()||[]).length+(typeof mpArchGet==='function'?0:0)]})()")
    ok('«Снизить уровень» → активен уровень ниже, результат комплекса сохранён',r[0] and r[1]==1,r)
    await E("show('home');cfOpenCat(cfProg().lvl)");await W()
    ok('после выбора больше не спрашивает',await E("el('gvtModal').hidden"))
    # --- кроссфит: перерыв 10 дней — не спрашивает
    await E("""(()=>{const s=cfGet();const lv=CF_CATS[1].k;const ts=Date.now()-10*864e5;s.prog={lvl:lv,ts:ts-1000,start:addDays(localDate(),-11),per:3,round:1};
      const d=CFW.find(x=>cfCatOf(x)===lv);s.res=[{id:'r2',wod:d.id,name:d.name,date:addDays(localDate(),-10),ts:ts,sc:'time',t:300}];cfSave(s);show('home');cfOpenCat(lv);})()""");await W()
    ok('кроссфит: перерыв 10 дн. — без вопроса',await E("el('gvtModal').hidden"))
    # --- «Выживший»: уровень «Мастер», последний выполненный день — 20 дней назад
    await E("""(()=>{const t=skGet();t.start=addDays(localDate(),-25);t.lvl='m';t.done={'5':{p:100}};skSave(t);show('home');skView=null;renderSotka();show('sotka');})()""");await W()
    r=await E(modal)
    ok('«Выживший»: перерыв 20 дн. — предложение «Снизить уровень: Продвинутый»',r['open'] and 'Продвинутый' in r['t'],r['t'][:140])
    await E("el('sbGo').click()");r=await E("(()=>{const t=skGet();return [t.lvl,t.start===addDays(localDate(),-25),Object.keys(t.done).length]})()")
    ok('«Продолжить как есть» — ничего не меняется',r==['m',True,1],r)
    await E("show('home');show('sotka')");await W()
    ok('и больше не спрашивает',await E("el('gvtModal').hidden"))
    # --- «100 отжиманий»: «Начать сначала» → архив и сброс
    await E("""(()=>{const id='push100',t=ppGet(id);t.start=addDays(localDate(),-30);t.done={'1':{p:100},'3':{p:100}};t.t={t0:12};ppSave(id,t);parSet([]);show('home');openPP(id);})()""");await W()
    r=await E(modal)
    ok('«100 отжиманий»: перерыв 28 дн. — «Начать сначала» (снижать нечего)',r['open'] and not r['low'] and 'Перерыв 28 дн.' in r['t'],r['t'][:120])
    await E("el('sbRe').click()");r=await E("(()=>{const t=ppGet('push100');return [t.start,(parGet()||[]).length,t.t.t0]})()")
    ok('«Начать сначала» → цикл в архиве, программа ждёт нового старта, стартовый тест сохранён',r[0] is None and r[1]==1 and r[2]==12,r)
    # --- «Похороны лени»: снизить ступени
    await E("""(()=>{const s=rrGet();const k=Object.keys(s.sl)[0];s.sl[k].i=2;s.sessions=6;s.start=addDays(localDate(),-40);rrSave(s);const x=JSON.parse(localStorage.getItem(RRK));x.upd=Date.now()-16*864e5;localStorage.setItem(RRK,JSON.stringify(x));
      show('home');renderRR();show('rr');})()""");await W()
    r=await E(modal)
    ok('«Похороны лени»: перерыв 16 дн. — предложение на ступень ниже',r['open'] and r['low'],r['t'][:120])
    await E("el('sbLow').click()");r=await E("(()=>{const s=rrGet();const k=Object.keys(s.sl)[0];return [s.sl[k].i,s.sessions]})()")
    ok('«Снизить уровень» → ступень 2 → 1, тренировки не сброшены',r==[1,6],r)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
