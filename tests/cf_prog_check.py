# Кроссфит как программа: уровень с частотой в неделю и датой следующей тренировки, конец круга → следующий уровень
# или ещё круг; Phil Team ведётся по плану (активация, «следующая», прогресс 24 тренировок).
# Запуск: python3 tests/cf_prog_check.py index.html [папка_скриншотов]
import asyncio,os,sys,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
HTML=os.path.abspath(sys.argv[1]);SHOT=sys.argv[2] if len(sys.argv)>2 else None
tmp=tempfile.mkdtemp();shutil.copy(HTML,tmp+'/index.html')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    # ---- уровень «Новичок», 2 р/нед ----
    await pg.evaluate("renderCross();show('cross');cfOpenCat('beg')");await pg.wait_for_timeout(100)
    ok('до активации: выбор частоты и кнопка',await pg.evaluate("!!el('mpCfPer')&&!!el('mpCfGo')&&el('mpCfPer').querySelector('.on').dataset.v==='3'"))
    await pg.evaluate("el('mpCfPer').querySelector('[data-v=\"2\"]').click();el('mpCfGo').click()");await pg.wait_for_timeout(100)
    ok('активна, 2 р/нед, следующая — сегодня',await pg.evaluate("cfProg().per===2&&el('cfCatList').textContent.includes('Следующая тренировка — сегодня')&&!!el('mpCfNext')"))
    if SHOT:await pg.screenshot(path=SHOT+'/cf-active.png',full_page=True)
    # записать результат первого комплекса → следующая через 3 дня
    await pg.evaluate("(()=>{const s=cfGet(),p=cfProg(),d=cfProgNext(p);s.res.push({id:'r1',wod:d.id,v:'rx',sc:'done',ts:Date.now(),pr:true});cfSave(s);})()")
    nd=await pg.evaluate("(()=>{const p=cfProg(),d=new Date();d.setDate(d.getDate()+3);return [cfProgNextDate(p)===localDate(d),cfProgUniq(p),mpList().find(x=>x.k==='cf').next===localDate(d)]})()")
    ok('после тренировки: следующая через 3 дня (2 р/нед), на главном та же дата',nd==[True,1,True],nd)
    await pg.evaluate("cfRenderCat();el('mpCfPer').querySelector('[data-v=\"4\"]').click()");await pg.wait_for_timeout(80)
    ok('смена частоты на 4 → пауза 2 дня',await pg.evaluate("cfProg().per===4&&cfProgGap(cfProg())===2"))
    # пройти весь круг
    await pg.evaluate("(()=>{const s=cfGet(),p=cfProg();cfProgList(p).forEach((d,i)=>s.res.push({id:'x'+i,wod:d.id,v:'rx',sc:'done',ts:Date.now()+i}));cfSave(s);cfRenderCat();})()");await pg.wait_for_timeout(80)
    ok('круг пройден: предложение «Опытный» и «Ещё круг»',await pg.evaluate("cfProgRoundDone(cfProg())&&!!el('mpCfUp')&&el('mpCfUp').textContent.includes('Опытный')&&!!el('mpCfAgain')&&mpList().find(x=>x.k==='cf').next===null"))
    if SHOT:await pg.screenshot(path=SHOT+'/cf-round.png',full_page=True)
    await pg.evaluate("el('mpCfAgain').click()");await pg.wait_for_timeout(80)
    ok('ещё круг: круг 2, счётчик с нуля, прошлый круг в архиве',await pg.evaluate("cfProg().round===2&&cfProgUniq(cfProg())===0&&parGet().some(a=>a.prog==='cf:beg'&&/Круг 1 пройден/.test(a.verdict))"))
    await pg.evaluate("(()=>{const s=cfGet(),p=cfProg();cfProgList(p).forEach((d,i)=>s.res.push({id:'y'+i,wod:d.id,v:'rx',sc:'done',ts:Date.now()+100+i}));cfSave(s);cfRenderCat();})()")
    await pg.evaluate("el('mpCfUp').click()");await pg.wait_for_timeout(80)
    ok('переход на «Опытный»: тот же ритм 4 р/нед, круг 1',await pg.evaluate("(()=>{const p=cfProg();return p.lvl==='int'&&p.per===4&&p.round===1&&CF_CUR_CAT==='int'&&!!el('mpCfNext')})()"))
    up=await pg.evaluate("(()=>{const s=cfGet();s.prog={lvl:'elite',ts:Date.now()+1e6,start:localDate(),per:3,round:1};cfSave(s);const p=cfProg();cfProgList(p).forEach((d,i)=>s.res.push({id:'z'+i,wod:d.id,v:'rx',sc:'done',ts:Date.now()+2e6+i}));cfSave(s);CF_CUR_CAT='elite';cfRenderCat();return [!!el('mpCfUp'),!!el('mpCfAgain')]})()")
    ok('«Профи»: только «Ещё круг»',up==[False,True],up)
    # ---- Phil Team ----
    await pg.evaluate("renderCross();show('cross');el('cfProgBtn').click()");await pg.wait_for_timeout(100)
    ok('Phil Team: 4 недели по 6 дней, кнопка «Начать программу»',await pg.evaluate("CF_PROG.weeks.length===4&&CF_PROG.weeks.every(w=>w.days.length===6)&&!!document.querySelector('.au-start')&&el('auWk').querySelectorAll('button').length===4"))
    await pg.evaluate("document.querySelector('.au-start').click()");await pg.wait_for_timeout(100)
    ok('активна: следующая — сегодня, Н1 · Пн; на главном',await pg.evaluate("document.querySelector('.au-plan').textContent.includes('сегодня')&&document.querySelector('.au-go').textContent.includes('Н1 · Пн')&&mpList().some(x=>x.k==='au:phil')"))
    await pg.evaluate("document.querySelector('.au-go').click()");await pg.wait_for_timeout(100)
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(100)
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>s.done=true));finishWorkout()");await pg.wait_for_timeout(150)
    h=await pg.evaluate("JSON.stringify(safe.get().slice(-1)[0].au)+' '+safe.get().slice(-1)[0].sec")
    ok('тренировка записана в Phil Team (кроссфит)',h=='{"id":"phil","w":0} cross',h)
    st=await pg.evaluate("(()=>{const nn=auPlanNext(CF_PROG),d=new Date();d.setDate(d.getDate()+1);return [nn.w,nn.d,auCount('phil'),auPlanDate(CF_PROG)===localDate(d)]})()")
    ok('дальше Н1 · Вт, завтра; 1 из 24',st==[0,1,1,True],st)
    await pg.evaluate("authOpen(CF_PROG)");await pg.wait_for_timeout(100)
    ok('экран программы: прогресс 1/24 и «Н1 · Вт» завтра',await pg.evaluate("document.querySelector('.au-prog').textContent.includes('1 / 24')&&document.querySelector('.au-go').textContent.includes('Н1 · Вт')"))
    if SHOT:await pg.screenshot(path=SHOT+'/phil.png',full_page=True)
    ok('без ошибок JS',not errs,errs)
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
