# GVT 2.0: окно этапа по ритму пользователя (дни отдыха, повторы волн), «Продолжить этап» продлевает окно,
# отставание в днях и занятиях; первая тренировка после перерыва (14 дн. −10 %, 15+ дн. −15 %) без сбоя прогрессии.
# Запуск: python3 tests/g2_window_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools,re
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
# программа на этапе I: n занятий, интервал rest; последнее занятие — gap дней назад
SETUP="""((n,rest,gap)=>{localStorage.removeItem(G2K);const v=g2Store();const P=g2New({stage:0,rest:rest});P.st[0].setup=true;
  g2MainKeysOf(P,0).forEach(k=>P.st[0].ws[k]={w:60});
  const iv=rest+1,last=addDays(localDate(),-gap);for(let i=0;i<n;i++){const d=addDays(last,-(n-1-i)*iv);P.recs.push({uid:"r"+i,stage:0,kind:"train",day:i%3,date:d,finishedAt:d+"T10:00:00Z",updatedAt:d+"T10:00:00Z",
    ex:[{key:"flyInc",main:false,sets:[{done:true,w:20,r:12}]}],dec:[]});}
  P.st[0].pos=n;v.progs.push(P);v.activeId=P.id;g2Save(v);show("gvt");g2Render();})"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    # ---- дни отдыха 2, этап I, строго по графику: 12 занятий за 34 дня — окна хватает (54 дня), плашки нет
    await E(SETUP+"(12,2,1)")
    t=await E("el('gvtBody').textContent")
    ok('дни отдыха 2, по графику: плашки нет, окно 54 дня','истёк' not in t and '(54 дн.)' in t,re.search(r'Окно этапа[^)]*\)',t).group(0) if re.search(r'Окно этапа[^)]*\)',t) else t[:200])
    # ---- отстал: 6 занятий, последнее 20 дней назад → окно истекло, отставание
    await E(SETUP+"(6,1,40)")
    t=await E("el('gvtBody').textContent")
    m_=re.search(r'Плановый срок.*?Невыполненное',t,re.S)
    ok('плашка показывает отставание в днях и занятиях',m_ and 'отстаёшь на' in m_.group(0) and 'Осталось занятий: 12' in m_.group(0),m_.group(0) if m_ else t[:300])
    ok('нет отрицательных значений',not re.search(r'-\d',m_.group(0) if m_ else ''))
    # ---- «Продолжить этап» → плашка исчезает, «продлён до»
    await E("el('g2Cont').click()");await pg.wait_for_timeout(100)
    t=await E("el('gvtBody').textContent")
    until=await E("g2Active().st[0].ext.until")
    exp=await E("addDays(localDate(),12*2-1)")
    ok('«Продолжить этап»: продлён на 12 занятий × 2 дня, плашки нет','истёк' not in t and 'продлён до' in t and until==exp,[until,exp])
    # срок продления прошёл — плашка снова
    await E("(()=>{const v=g2Store();v.progs[0].st[0].ext.until=addDays(localDate(),-1);g2Save(v);g2Render();})()")
    ok('после нового срока плашка появляется снова','истёк' in await E("el('gvtBody').textContent"))
    # ---- смена дней отдыха пересчитывает окно
    w1=await E("(()=>{const P=g2Active();delete P.st[0].ext;return g2Win(P,0,g2StageFirst(P,0)).days})()")
    w2=await E("(()=>{const P=g2Active();delete P.st[0].ext;P.rest=3;return g2Win(P,0,g2StageFirst(P,0)).days})()")
    ok('окно = занятия этапа × (дни отдыха + 1): 18×2=36, 18×4=72',[w1,w2]==[36,72],[w1,w2])

    # ---- перерыв 13 дней — без вопроса
    await E(SETUP+"(4,1,13)");await E("el('g2Open').click()")
    ok('13 дней — тренировка открывается сразу',await E("el('gvtModal').hidden&&!!dayView&&dayView.p.g2&&!dayView.p.g2.brk"))
    # ---- 14 дней — −10 %
    await E(SETUP+"(3,1,14)");await E("dayView=null;el('g2Open').click()")
    ok('14 дней — предложение «легче на 10 %»',await E("!el('gvtModal').hidden&&el('g2BrkY').textContent.includes('10 %')"))
    await E("el('g2BrkY').click()")
    r=await E("({w:dayView.p.preset[0][0].w,acc:dayView.p.preset[2][0].w,brk:dayView.p.g2.brk,f:dayView.p.focus})")
    ok('−10 %: жим гантелей 60 → 54 (шаг 2), фокус с пометкой',r['w']==54 and r['brk']==10 and 'после перерыва −10 %' in r['f'],r)
    ok('вспомогательные тоже легче: 20 → 18',r['acc']==18,r)
    # ---- 20 дней — −15 %, и прогрессия не меняется
    await E(SETUP+"(3,1,20)");await E("dayView=null;el('g2Open').click()")
    ok('15+ дней — предложение «легче на 15 %»',await E("el('g2BrkY').textContent.includes('15 %')"))
    await E("el('g2BrkY').click();current=null;beginWorkout(dayView.p,dayView.computed)")
    r=await E("""(()=>{const w0=JSON.stringify(g2Active().st[0].ws);current.sets.forEach(ss=>ss.forEach(s=>{s.done=true;s.r=s.pr||10;}));const rec=g2Record();current=null;
      const P=g2Active();return {same:JSON.stringify(P.st[0].ws)===w0,pos:P.st[0].pos,brk:rec.brk,dec:rec.dec.map(d=>d.type),prev:(g2PrevEx(P,0,'flyInc')||{sets:[{w:0}]}).sets[0].w}})()""")
    ok('после облегчённой: рабочие веса не изменились, занятие засчитано',r['same'] and r["pos"]==4 and r['brk']==15 and r['dec']==['brk'],r)
    ok('облегчённая не становится образцом для вспомогательных (остаётся 20)',r['prev']==20,r)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
