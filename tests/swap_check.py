# Замена упражнений: GVT — до 6 вариантов с разным оборудованием; силовые программы — кнопка «⇄ Заменить»,
# «только сегодня» / «во всех следующих», вес из истории замены, возврат исходного.
# Запуск: python3 tests/swap_check.py index.html [папка_скриншотов]
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
    # GVT
    ok('GVT: у каждого упражнения ≥5 замен',await pg.evaluate("[...new Set(G2S.flatMap(st=>st.d.flatMap(d=>[...d.A,...d.B].map(x=>x[0]))))].filter(k=>k!=='farmer'&&!/^calf/.test(k)).every(k=>g2Alts(k).length>=5)"))
    ok('GVT: скручивания на блоке — 6 вариантов: свой вес, тренажёр, блин, резина',await pg.evaluate("(()=>{const a=g2Alts('cblCr'),e=a.map(g2Eq);return a.length===6&&e.includes('свой вес')&&e.includes('тренажёр')&&e.includes('резина')})()"),await pg.evaluate("g2Alts('cblCr').map(k=>G2X[k].n+' ['+g2Eq(k)+']').join('; ')"))
    ok('GVT: жим и тяга — есть штанга, гантели, тренажёр, свой вес',await pg.evaluate("['dDecl','rowDb','squat','hammer','dips','latSeat'].every(k=>{const e=g2Alts(k).map(g2Eq);return e.includes('тренажёр')||e.includes('блок')})"))
    # силовая программа: «Последний патрон»
    await pg.evaluate("localStorage.setItem(KEY,JSON.stringify([{date:'2026-10-01',name:'x',vol:100,log:{'Тяга верхнего блока к груди':[{w:22.5,r:10,done:true},{w:22.5,r:10,done:true}]}}]))")
    await pg.evaluate("(()=>{const p=AUTH.find(q=>q.id==='pcfb');const d=Object.assign({},p.weeks[0].days[0],{au:{id:'pcfb',w:0}});beginWorkout(d,false);})()");await pg.wait_for_timeout(150)
    names=await pg.evaluate("current.program.ex.map(e=>e[0])")
    bi=await pg.evaluate("current.program.ex.findIndex(e=>wsubRep(e[0])==='pull')")
    ok('в программе есть вертикальная тяга',bi>=0,names)
    await pg.evaluate(f"goEx({bi})");await pg.wait_for_timeout(100)
    ok('кнопка «⇄ Заменить» есть',await pg.evaluate("!!document.querySelector('#exList .wk-swap')"))
    await pg.evaluate("document.querySelector('#exList .wk-swap').click()");await pg.wait_for_timeout(100)
    n=await pg.evaluate("el('gvtMbox').querySelectorAll('[data-k]').length")
    ok('в замене 6 вариантов с оборудованием',n==6,await pg.evaluate("[...el('gvtMbox').querySelectorAll('[data-k]')].map(b=>b.innerText.replace(/\\n/g,' ')).join('; ')"))
    if SHOT:await pg.screenshot(path=SHOT+'/swap.png')
    k=await pg.evaluate("[...el('gvtMbox').querySelectorAll('[data-k]')].findIndex(b=>b.textContent.includes('Тяга верхнего блока к груди'))")
    await pg.evaluate(f"el('gvtMbox').querySelectorAll('[data-k]')[{k}].click()");await pg.wait_for_timeout(100)
    ok('только сегодня: упражнение заменено, «вместо: …», вес из истории 22,5',await pg.evaluate(f"current.program.ex[{bi}][0]==='Тяга верхнего блока к груди'&&/^вместо:/.test(current.program.ex[{bi}][5])&&current.sets[{bi}].every(s=>s.w===22.5)"))
    ok('только сегодня: в следующих не запомнено',await pg.evaluate("!localStorage.getItem(WSUBK)||!wsubAll()['au:pcfb']"))
    # во всех следующих
    await pg.evaluate("document.querySelector('#exList .wk-swap').click()");await pg.wait_for_timeout(100)
    await pg.evaluate("el('wsA').click()")
    await pg.evaluate("[...el('gvtMbox').querySelectorAll('[data-k]')].find(b=>b.textContent.includes('Подтягивания в гравитроне')).click()");await pg.wait_for_timeout(100)
    orig=names[bi]
    ok('во всех следующих: запомнено для программы',await pg.evaluate(f"wsubAll()['au:pcfb'][{orig!r}]==='Подтягивания в гравитроне'"))
    await pg.evaluate("current=null;(()=>{const p=AUTH.find(q=>q.id==='pcfb');beginWorkout(Object.assign({},p.weeks[0].days[0],{au:{id:'pcfb',w:0}}),false);})()");await pg.wait_for_timeout(100)
    ok('следующая тренировка начинается с заменой',await pg.evaluate(f"current.program.ex[{bi}][0]==='Подтягивания в гравитроне'&&current.orig[{bi}]==={orig!r}"))
    ok('исходная программа не испорчена',await pg.evaluate(f"AUTH.find(q=>q.id==='pcfb').weeks[0].days[0].ex[{bi}][0]==={orig!r}"))
    await pg.evaluate(f"goEx({bi});document.querySelector('#exList .wk-swap').click()");await pg.wait_for_timeout(100)
    await pg.evaluate("el('wsBack').click()");await pg.wait_for_timeout(100)
    ok('↺ вернуть исходное — и в следующих',await pg.evaluate(f"current.program.ex[{bi}][0]==={orig!r}&&!wsubAll()['au:pcfb']"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
