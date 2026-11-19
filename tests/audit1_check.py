# Аудит, пакет 1: №14 (GVT: день этапа ещё не делали), №35 (вес, введённый в облегчённом GVT), №12 (UTC-дата в циклах),
# №6 (проценты от 1ПМ — вниз), №8 (5×5 без 1ПМ), №30 (пустые раунды в кроссфите), №4 (сбой записи истории),
# №17 (повторы-диапазон в своей программе), №29 (HIIT 100 · отдых 0).
# Запуск: python3 tests/audit1_check.py index.html
import asyncio,sys,os,re,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
HELP=re.search(r'HELP="""(.*?)"""',open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'g2_waves_check.py'),encoding='utf-8').read(),re.S).group(1)
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(timezone_id='Asia/Bishkek');pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(400);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate;await E(HELP)
    # №14
    r=await E("""(()=>{readiness='Норма';T.fresh(0,{});T.run([]);T.run([]);const v=g2Store(),P=v.progs[0],tr=P.recs.filter(r=>r.kind==='train');
      tr[0].date=addDays(localDate(),-19);tr[1].date=addDays(localDate(),-2);tr[1].brk=15;g2Save(v);const sl=g2NextSlot(g2Active());
      return [sl.day,g2DayGap(g2Active(),sl)]})()""")
    ok('№14 GVT: первое «В» на этапе после перерыва — перерыв учтён (17 дн.)',r[0]==2 and r[1]>=15,r)
    r=await E("(()=>{T.open();return !el('gvtModal').hidden&&el('gvtMbox').textContent.includes('Легче на 15 %')})()")
    ok('№14 → предлагает «Легче на 15 %»',r)
    await E("el('gvtModal').hidden=true;current=null;clearDraft()")
    # №35
    r=await E("""(()=>{readiness='Норма';T.fresh(0,{});T.run([]);readiness='Устал';const P0=g2Active(),sl=g2NextSlot(P0);T.open();
      const p=current.program,i=p.gx.findIndex(G=>G.main&&!G.bw),k=p.gx[i].key;g2AskWeight(i);el('g2aw').value='100';el('g2aGo').click();
      const P=g2Active(),st=P.st[p.g2.stage].ws[k];return [current.sets[i].find(s=>!s.done).w,st.W0!=null?st.W0:st.w, st.plan?st.plan[1]:null]})()""")
    ok('№35 «Устал»: ввёл 100 внутри занятия — сегодня на 10 % легче, база этапа не тронута',r[1]==100 and r[0] is not None and r[0]<100 and r[0]>=85,r)
    await E("readiness='Норма';current=null;clearDraft()")
    # №12 — 5/3/1: тренировка в 00:30 по Бишкеку (UTC — ещё вчера)
    r=await E("""(()=>{const d=new Date();d.setHours(0,30,0,0);const iso=d.toISOString();return [localDate(d),iso.slice(0,10),brkLast.length]})()""")
    loc,utc,_=r
    r2=await E(f"""(()=>{{const v={{progs:[{{id:'t',recs:[{{finishedAt:'{utc}T18:30:00.000Z'}}]}}],activeId:'t'}};const save=w5Active;w5Active=()=>v.progs[0];const L=brkLast({{w5:1}});w5Active=save;return L}})()""")
    ok('№12 время завершения в UTC (18:30Z) → местная дата следующего дня',r2==loc,[r2,loc,utc])
    # №6, №8
    r=await E("[rmW(90,75,2.5),rmW(100,72.5,2.5),rmW(101,50,1)]")
    ok('№6 таблица 1ПМ: 90 × 75 % = 67,5 (не 68); 72,5 вниз',r==[67.5,72.5,50],r)
    r=await E("""(()=>{localStorage.setItem(RMK,JSON.stringify({}));const a=plW('Жим лёжа',75);localStorage.setItem(RMK,JSON.stringify({'Жим лёжа':90}));const b=plW('Жим лёжа',75),c=plW('Жим лёжа',72.5);return [a,b,c]})()""")
    ok('№8 5×5 без 1ПМ — веса нет (не от выдуманных 80 кг); с 1ПМ 90 → 67,5 и 65 (вниз под блины)',r[0] is None and r[1]==67.5 and r[2]==65,r)
    # №30
    r=await E("(()=>{const x=document.createElement('input');x.id='zzz';document.body.appendChild(x);x.value='';const t=String(x.value).trim();return t===''?'NaN':Number(t)})()")
    src=open(H,encoding='utf-8').read()
    ok('№30 кроссфит: пустое поле — не 0',"return t===\"\"?NaN:Number" in src)
    # №4 — память заполнена
    r=await E("""(()=>{safe.set([]);const prog={name:'Тест',focus:'BAZA',ex:[['Жим штанги лёжа',2,'8–10',60]],sec:'body'};current=null;clearDraft();startWorkout(prog,false);el('dayStart').click();
      current.sets[0].forEach(s=>{s.done=true;s.r=10;s.w=60;});const orig=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k===KEY)throw new Error('QuotaExceededError');return orig.call(this,k,v);};
      finishWorkout();const kept=!!current,draft=!!localStorage.getItem(DRAFTK);Storage.prototype.setItem=orig;finishWorkout();return [kept,draft,(safe.get()||[]).length,!current]})()""")
    ok('№4 запись истории не удалась — тренировка и черновик на месте; повтор записывает ровно одну',r==[True,True,1,True],r)
    # №17
    r=await E("""(()=>{safe.set([]);const prog={name:'Моя',focus:'моя программа',ex:[['Жим гантелей сидя',2,'8–12',null]],sec:'body'};current=null;clearDraft();startWorkout(prog,false);el('dayStart').click();
      current.sets[0].forEach(s=>{s.done=true;s.w=20;});finishWorkout();const h=safe.get().slice(-1)[0];return [h.vol,h.log['Жим гантелей сидя'].map(x=>x.r)]})()""")
    ok('№17 своя программа: повторы не ввёл — тоннаж по нижней границе (2 × 20 × 8 = 320)',r[0]==320 and r[1]==[8,8],r)
    # №29
    r=await E("""(()=>{const d=hiitDays(5)[0];const e=d.ex.find(x=>/HIIT 100/.test(x[0]));current=null;clearDraft();startWorkout({name:'H',focus:'HIIT',ex:[e],sec:'body'},false);el('dayStart').click();
      current.idx=0;restStart();const a=el('wkRest').hidden;const e5=hiitDays(4)[0].ex.find(x=>/HIIT 100/.test(x[0]));return [e[6],a,e5[6]]})()""")
    ok('№29 HIIT 100, 6-я неделя: отдых 0 — таймер не запускается; 5-я неделя — 10 с',r[0]<0 and r[1] is True and r[2]==10,r)
    await E("current=null;clearDraft()")
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
