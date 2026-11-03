# «Техасский рейнджер»: неотмеченный подход → «не смог / не делал»; прибавка не меньше шага штанги (жим стоя +2,5,
# без повтора прежнего веса); «Пропустить лёгкий день»; старые записи считаются как раньше.
# Запуск: python3 tests/tx_fix_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
HELP="""(()=>{window.T={
 mk(cfg){localStorage.removeItem(TXK);const v=txStore();const P={id:"t1",createdAt:"x",updatedAt:"x",start:localDate(),cfg:Object.assign({days:3,mode:"std",pc:"pc",t:{sq:100,bp:80,pr:50,dl:140,pc:60}},cfg||{}),recs:[]};v.progs=[P];v.activeId="t1";txSave(v);return P;},
 /* f(lift,kind,set) → повторы; null — не отмечен. Через обычное завершение тренировки */
 day(f){const P=txActive(),st=txState(P);startWorkout(txPlan(P,st),true);current=null;el('dayStart').click();const p=current.program;
   p.tx.rows.forEach((R,i)=>{current.sets[i].forEach(s=>{if(s.warm){s.done=true;return;}const x=R.lift?f(R.lift,p.tx.kind,s):s.r;if(x===null)s.done=false;else{s.done=true;s.r=x;}});});
   finishWorkout();el('gvtModal').hidden=true;return {kind:p.tx.kind,w:Object.fromEntries(p.tx.rows.map((R,i)=>[R.lift,p.preset[i].filter(s=>!s.warm).map(s=>s.w)]).filter(x=>x[0]))};},
 all(l,k,s){return s.need||s.r;}};})()"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'");await pg.evaluate(HELP)
    E=pg.evaluate
    # ---- неотмеченная становая в понедельник → вопрос
    await E("T.mk();T.day((l,k,s)=>k==='vd'&&l==='dl'?null:T.all(l,k,s))")
    ok('после тренировки — вопрос «Не смог / Не делал»',await E("(()=>{const r=txActive().recs[0];return r.lifts.dl.unk===true})()"))
    await E("show('tx');renderTx()")
    ok('на экране программы — «Ответить»',await E("!!el('txUnk')"))
    await E("el('txUnk').click()");await E("el('gvtMbox').querySelector('[data-o=skip]').click()")
    await E("T.day((l,k,s)=>k==='vd'&&l==='dl'?null:T.all(l,k,s))")  # ld
    await E("T.day(T.all)")  # id
    await E("T.day((l,k,s)=>k==='vd'&&l==='dl'?null:T.all(l,k,s))")  # vd неделя 2
    r=await E("(()=>{const P=txActive(),r=P.recs.slice(-1)[0];w5=null;return r.lifts.dl.unk})()")
    await E("txAskUnk(txActive().recs.slice(-1)[0].uid);el('gvtMbox').querySelector('[data-o=skip]').click()")
    ok('«Не делал» дважды подряд — становая без отката (140)',await E("txState(txActive()).t.dl")==140,await E("txState(txActive()).t.dl"))
    await E("T.mk();T.day((l,k,s)=>k==='vd'&&l==='dl'?null:T.all(l,k,s))");await E("txAskUnk(txActive().recs[0].uid);el('gvtMbox').querySelector('[data-o=fail]').click()")
    await E("T.day(T.all);T.day(T.all);T.day((l,k,s)=>k==='vd'&&l==='dl'?null:T.all(l,k,s))");await E("txAskUnk(txActive().recs.slice(-1)[0].uid);el('gvtMbox').querySelector('[data-o=fail]').click()")
    ok('«Не смог» дважды подряд — откат −10 % (140 → 125)',await E("txState(txActive()).t.dl")==125,await E("txState(txActive()).t.dl"))
    # ---- жим стоя +2,5 на каждом рекорде, без повтора веса
    await E("T.mk()")
    w=await E("(()=>{const out=[];for(let i=0;i<24;i++){const d=T.day(T.all);if(d.kind==='id'&&d.w.pr)out.push(d.w.pr[0]);}return out})()")
    ok('жим стоя на рекорде: 50 → 52,5 → 55 → 57,5 (каждый раз +2,5)',w==[50,52.5,55,57.5],w)
    ok('в подсказке рекорда «+2,5 кг»',await E("(()=>{const P=txActive(),st=txState(P);const p=txPlan(P,st,'id');return p.ex.find(e=>e[0]==='Жим штанги стоя'||e[0]==='Жим штанги лёжа')[5].includes('+2,5 кг')})()"))
    r=await E("(()=>{T.mk({days:4});const out=[];for(let i=0;i<16;i++){const d=T.day(T.all);if(d.kind==='d3')out.push(d.w.pr[0]);}return out})()")
    ok('4 дня: жим стоя 3×3 растёт на 2,5 каждую неделю, без повторов',r==[50,52.5,55,57.5],r)
    # старые записи (до изменения) — прибавка как была
    r=await E("""(()=>{T.mk();const v=txStore(),P=v.progs[0];P.recs=[{uid:"o",kind:"id",week:2,finishedAt:"2026-10-20T10:00:00Z",updatedAt:"x",lifts:{pr:{w:50,prog:true,sets:1,reps:[5],need:[5]}}}];txSave(v);return txState(txActive()).t.pr})()""")
    ok('старая запись до изменения — +1,25 как раньше (50 → 51,25)',r==51.25,r)
    r=await E("(()=>{const P=txActive(),st=txState(P);return txPlan(P,st,'id').preset.map(ss=>ss.filter(s=>!s.warm).map(s=>s.w))})()")
    ok('старый вес 51,25 на рекорде — 52,5 (вверх), не повтор 50',any(x==[52.5] for x in r),r)
    # ---- пропустить лёгкий день
    await E("T.mk();T.day(T.all);show('tx');renderTx()")
    ok('после объёмного дня — кнопка «Пропустить лёгкий день»',await E("!!el('txSkipLd')"))
    await E("el('txSkipLd').click()")
    r=await E("(()=>{const st=txState(txActive());return [st.next,st.week,!!el('txSkipLd')]})()")
    ok('пропуск: следующая — рекорд, та же неделя, кнопки больше нет',r==['id',1,False],r)
    await E("T.day(T.all)")
    r=await E("(()=>{const st=txState(txActive());return [st.next,st.week,st.t.sq]})()")
    ok('после рекорда — новая неделя, прогрессия как обычно (присед +5)',r==['vd',2,105],r)
    ok('в истории пропуск отмечен',await E("(()=>{renderTx();return el('txBody')?el('txBody').textContent.includes('пропущен'):document.body.textContent.includes('пропущен')})()"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
