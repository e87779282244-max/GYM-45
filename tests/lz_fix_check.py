# «Рождённый ползать»: 7–8 повторов → +2,5 кг, меньше 7 → тот же вес (вес на экране растёт сразу, без повторов);
# прежние записи — по правилу автора; «Пропустить день»; неотмеченные подходы тяжёлого дня → «не смог / не делал».
# Запуск: python3 tests/lz_fix_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
HELP="""(()=>{window.T={
 mk(){localStorage.removeItem(LZK);const v=lzStore();const P={id:"l1",createdAt:"x",updatedAt:"x",start:localDate(),cfg:{pull:{rm:25},dip:{rm:40},mu:"bar"},recs:[]};v.progs=[P];v.activeId="l1";lzSave(v);},
 /* следующая тренировка через обычное завершение: f(lift,setIndex) → повторы; null — не отмечен */
 day(f){const P=lzActive(),st=lzState(P);startWorkout(lzPlan(P,st),true);current=null;el('dayStart').click();const p=current.program;
   p.lz.rows.forEach((R,i)=>{let j=0;current.sets[i].forEach(s=>{if(s.warm||!R.lift){s.done=true;return;}const x=f(R.lift,j++);if(x===null)s.done=false;else{s.done=true;s.r=x;}});});
   const w=p.lz.rows.map((R,i)=>R.lift==="pull"?current.sets[i].filter(s=>!s.warm)[0].w:null).filter(x=>x!=null)[0];
   finishWorkout();el('gvtModal').hidden=true;return {kind:p.lz.kind,pull:w};}};})()"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'");await pg.evaluate(HELP)
    E=pg.evaluate
    # ---- 7 повторов → +2,5 каждый тяжёлый день, вес на экране растёт сразу
    await E("T.mk()")
    seq=await E("(()=>{const out=[];for(let i=0;i<9;i++){const d=T.day(()=>7);if(d.kind!=='wed')out.push(d.pull);}return out})()")
    ok('7 повторов: подтягивания 10 → 12,5 → 15 → 17,5 → 20 → 22,5 (без повторов веса)',seq==[10,12.5,15,17.5,20,22.5],seq)
    await E("T.mk()")
    seq=await E("(()=>{const out=[];for(let i=0;i<6;i++){const d=T.day(()=>6);if(d.kind!=='wed')out.push(d.pull);}return out})()")
    ok('6 повторов: вес тот же — добирай повторы',seq==[10,10,10,10],seq)
    # ---- прежние записи — как раньше
    r=await E("""(()=>{T.mk();const v=lzStore(),P=v.progs[0];P.recs=[{uid:"o",kind:"mon",finishedAt:"2026-10-30T10:00:00Z",updatedAt:"x",lifts:{pull:{w:10,sets:3,reps:[8,8,7]},dip:{w:15,sets:3,reps:[8,8,8]}}}];lzSave(v);const st=lzState(lzActive());return [st.lifts.pull.W,lzPlan(lzActive(),st,'fri').preset.map(ss=>ss.filter(s=>!s.warm&&s.need).map(s=>s.w)).filter(x=>x.length)]})()""")
    ok('запись до 04.11: 7 повторов → +1,25 (10 → 11,25), на экране 12,5 (вверх), не повтор 10',r[0]==11.25 and [12.5,12.5,12.5] in r[1],r)
    # ---- пропустить день
    await E("T.mk();T.day(()=>8);show('lz');renderLz()")
    ok('кнопка «Пропустить …»',await E("!!el('lzSkip')&&el('lzSkip').textContent.includes('Ср')"))
    await E("el('lzSkip').click();el('lzSkip').click()")
    r=await E("(()=>{const s=lzState(lzActive());return [s.next,s.week]})()")
    ok('пропуск среды → следующая пятница той же недели',r==['fri',1],r)
    await E("show('lz');renderLz();el('lzSkip').click();el('lzSkip').click()")
    r=await E("(()=>{const s=lzState(lzActive());return [s.next,s.week,s.lifts.pull.W]})()")
    ok('пропуск пятницы → понедельник новой недели, вес не меняется',r==['mon',2,12.5],r)
    ok('в истории «пропущен»',await E("(()=>{renderLz();return el('lzBody').textContent.includes('пропущен')})()"))
    # ---- неотмеченный подход → вопрос
    await E("T.mk();T.day((l,j)=>l==='pull'&&j===2?null:8)")
    ok('после тяжёлой с неотмеченным подходом — вопрос',await E("lzActive().recs[0].lifts.pull.unk===true"))
    await E("show('lz');renderLz()")
    ok('на экране — «Ответить»',await E("!!el('lzUnk')"))
    await E("el('lzUnk').click();el('gvtMbox').querySelector('[data-o=skip]').click()")
    ok('«Не делал» → считаются отмеченные 8/8 → +2,5',await E("lzState(lzActive()).lifts.pull.W")==12.5,await E("lzState(lzActive()).lifts.pull.W"))
    await E("T.mk();T.day((l,j)=>l==='pull'&&j===2?null:8)");await E("lzAskUnk(lzActive().recs[0].uid);el('gvtMbox').querySelector('[data-o=fail]').click()")
    ok('«Не смог» → вес тот же',await E("lzState(lzActive()).lifts.pull.W")==10)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
