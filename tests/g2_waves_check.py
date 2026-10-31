# GVT 2.0, этапы IV–V: отложенные решения по весу и завершение волн.
# Устаревшие решения не откатывают прогресс; срыв без решения → «повтор» по умолчанию; завершённое упражнение (6/6)
# не ставится в день; счётчики не уходят за план; вес 6-го появления подтверждается до старта; переход этапа закрывает нерешённое.
# Запуск: python3 tests/g2_waves_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools,re
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
HELP="""(()=>{window.T={
 fresh(stage,ws){const v={progs:[],activeId:null};const P=g2New({stage:stage,step:2.5});P.st[stage].setup=true;Object.assign(P.st[stage].ws,ws||{});v.progs.push(P);v.activeId=P.id;g2Save(v);return P.id;},
 plan(P,si,k,w){return G2S[si].algo==="agvt"?g2PlanAG(P,si,k,w):g2PlanP4(P,si,k,w);},
 ws(si,k){return g2Active().st[si].ws[k];},
 /* открыть тренировку как кнопкой «Открыть тренировку», отметить подходы и записать */
 /* «Начать программу» на экране дня */
 begin(){if(!dayView||!dayView.p||!dayView.p.g2)return false;current=null;beginWorkout(dayView.p,dayView.computed);return !!(current&&current.program&&current.program.g2);},
 open(){g2Render();el("gvtModal").hidden=true;dayView=null;const b=el("g2Open");if(!b)return false;b.click();return T.begin();},
 finish(fail){const w=current.program;current.sets.forEach((ss,i)=>ss.forEach(s=>{s.done=true;s.w=s.w||100;s.r=fail.includes(w.gx[i].key)?Math.max(0,s.pr-1):s.pr;}));
   const rec=g2Record();current=null;try{localStorage.removeItem(DRAFTK)}catch(e){}return rec;},
 run(fail){if(!T.open()){const m=el("gvtModal");if(!m.hidden&&el("g2c6Go")){el("g2c6Go").click();if(!T.begin())return null;}else return null;}return T.finish(fail||[]);}
};})()"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    if not await pg.evaluate("typeof DRAFTK!=='undefined'"):await pg.evaluate("window.DRAFTK='__none__'")
    await pg.evaluate(HELP)
    E=pg.evaluate

    # ---- 1. полный проход этапа IV: срыв без решения → повтор по умолчанию, лишних 10×3 нет
    await E("""(()=>{const id=T.fresh(3);const v=g2Store(),P=v.progs[0];g2MainKeysOf(P,3).forEach(k=>{P.st[3].ws[k]={ptr:1,plan:T.plan(P,3,k,100),scheme:"543",W0:100};});g2Save(v);})()""")
    log=await E("""(()=>{const out=[];for(let i=0;i<60;i++){const A=g2Active();if(!A||A.stage!==3)break;const r=T.run(i===0?["pullLean"]:[]);if(!r)break;
      out.push({n:r.num,keys:r.ex.filter(e=>e.main).map(e=>e.key+":"+e.ptr)});}return out;})()""")
    first=await E("g2Active().recs[0].dec.find(d=>d.type==='wave_fail')")
    ok('срыв без решения → при следующем открытии записан «повтор» по умолчанию',first and first['done'] and first['choice']=='repeat' and first.get('auto'),first)
    ok('этап IV пройден за 37 занятий (36 + 1 повтор) и перешёл на V',len(log)==37 and await E("g2Active().stage===4"),len(log))
    extra=[x for x in log if any(k.endswith(':7') for k in x['keys'])]
    bInc=[x for x in log if any(k.startswith('bInc:') for k in x['keys'])]
    ok('завершённое упражнение (жим) не получает лишнего 10×3',len(bInc)==6 and not extra,[x['keys'] for x in bInc])
    ok('последний день — только отстающее упражнение',log[-1]['keys']==['pullLean:6'],log[-1])

    # ---- 2. день без завершённого: окно, итог, прогресс завершённого не трогается
    await E("""(()=>{T.fresh(3);const v=g2Store(),P=v.progs[0];g2MainKeysOf(P,3).forEach(k=>{P.st[3].ws[k]={ptr:7,plan:T.plan(P,3,k,100),scheme:"543",W0:100,conf6:true};});
      P.st[3].ws.pullLean.ptr=5;P.st[3].pos=36;g2Save(v);})()""")
    ok('открывается тренировка', await E("T.open()"))
    pr=await E("({names:current.program.ex.map(e=>e[0]),units:current.program.g2.units,focus:current.program.focus,step:el('wkStep').textContent,solo:!!document.querySelector('.g2-card.solo')})")
    ok('в дне нет жима, A2 идёт отдельным блоком',len(pr['names'])==3 and pr['units']==[[0],[1,2]] and 'Основное упражнение A2' in pr['step'] and pr['solo'],pr)
    ok('в заголовке видно, что жим 6 из 6 пройден','6 из 6 пройдено' in pr['focus'],pr['focus'])
    ok('заголовок без «37 из 36»',not re.search(r'занятие 37 из 36',pr['focus']) and 'план 36' in pr['focus'],pr['focus'])
    rec=await E("T.finish([])")
    ok('завершённое не меняется и по нему нет решений',await E("T.ws(3,'bInc').ptr===7") and all(d['key']!='bInc' for d in rec['dec']),rec['dec'])

    # ---- 3. счётчики экрана программы при повторах
    await E("""(()=>{T.fresh(3);const v=g2Store(),P=v.progs[0];g2MainKeysOf(P,3).forEach(k=>{P.st[3].ws[k]={ptr:7,plan:T.plan(P,3,k,100),scheme:"543",W0:100,conf6:true};});
      P.st[3].ws.pullLean.ptr=5;P.st[3].ws.squat.ptr=6;P.st[3].pos=38;P.recs.push({uid:"o1",stage:3,kind:"train",date:"2026-01-01",ex:[],dec:[]});g2Save(v);g2Render();})()""")
    txt=await E("el('gvtBody').textContent")
    bad=[m_ for m_ in re.findall(r'(\d+)\s*из\s*(\d+)',txt) if int(m_[0])>int(m_[1])]
    ok('на экране нет «N из M» с N > M',not bad,bad)
    ok('показано «Занятие 39 · план 36» и появления',('Занятие 39 · план 36' in txt) and re.search(r'Появления: \d+ из 72',txt),txt[:200])
    ok('ближайшие занятия не пустые и только отстающие дни',await E("(()=>{const r=[...el('gvtBody').querySelectorAll('.rm-row .v')].map(x=>x.textContent);return r.includes('Грудь и спина · вариант 1')&&r.includes('Ноги · вариант 1')})()"))
    ok('полоса не больше 100 %',await E("parseFloat(el('gvtBody').querySelector('.gvt-bar i').style.width)<=100"))
    ok('остаток считается по отстающим (3 занятия)',await E("g2Left(g2Active(),3)===3"))

    # ---- 4. устаревшие решения
    await E("""(()=>{T.fresh(3);const v=g2Store(),P=v.progs[0];P.st[3].ws.pullLean={ptr:3,plan:T.plan(P,3,'pullLean',100),scheme:"543",W0:100};
      P.recs.push({uid:"s1",stage:3,kind:"train",variant:"Грудь и спина · вариант 1",status:"partial",setsDone:39,setsPlanned:40,ton:1,durMin:60,ex:[],
        dec:[{key:"pullLean",type:"wave_fail",ptr:1,cur:100,next:2,sug:106.5,txt:"Подтягивания: волна 1 не выполнена"}]});g2Save(v);g2Resolve("s1",0,"repeat",0);})()""")
    d=await E("g2Active().recs[0].dec[0]")
    ok('старое «Повторить волну» не откатывает прогресс (3 → 3)',await E("T.ws(3,'pullLean').ptr===3") and d['choice']=='stale',d)
    await E("""(()=>{T.fresh(0);const v=g2Store(),P=v.progs[0];P.st[0].ws.dDecl={w:62.5};
      P.recs.push({uid:"i1",stage:0,kind:"train",variant:"А · грудь и спина",status:"full",setsDone:40,setsPlanned:40,ton:1,durMin:60,ex:[],dec:[{key:"dDecl",type:"inc_confirm",cur:60,sug:64,pct:6.7,txt:"Жим: 10×10 выполнено"}]});
      P.recs.push({uid:"i2",stage:0,kind:"train",variant:"А · грудь и спина",status:"full",setsDone:40,setsPlanned:40,ton:1,durMin:60,ex:[{key:"dDecl",main:true,sets:[{done:true,w:62.5,r:10}]}],dec:[]});
      g2Save(v);g2Summary("i1");})()""")
    ok('старое «Оставить вес» (этап I) не возвращает меньший вес',await E("T.ws(0,'dDecl').w===62.5&&g2Active().recs[0].dec[0].choice==='stale'"))
    ok('в итоге видна пометка «устарело»','устарело' in await E("el('gvtMbox').textContent"))
    await E("el('gvtModal').hidden=true")

    # ---- 5. баннер: от старых к новым и число
    await E("""(()=>{T.fresh(3);const v=g2Store(),P=v.progs[0];['bInc','pullLean','squat','lcurlOut'].forEach(k=>{P.st[3].ws[k]={ptr:2,plan:T.plan(P,3,k,100),scheme:"543",W0:100};});
      P.recs.push({uid:"b1",stage:3,kind:"train",variant:"Грудь и спина · вариант 1",status:"partial",setsDone:1,setsPlanned:2,ton:1,durMin:1,ex:[],dec:[{key:"pullLean",type:"wave_fail",ptr:2,cur:100,next:3,sug:108,txt:"Подтягивания: срыв"}]});
      P.recs.push({uid:"b2",stage:3,kind:"train",variant:"Ноги · вариант 1",status:"partial",setsDone:1,setsPlanned:2,ton:1,durMin:1,ex:[],dec:[{key:"squat",type:"wave_fail",ptr:2,cur:100,next:3,sug:108,txt:"Присед: срыв"}]});
      g2Save(v);g2Render();})()""")
    ok('баннер показывает число занятий с решениями','занятий: 2' in await E("el('gvtBody').textContent"))
    await E("el('g2Pend').click()")
    ok('первым открывается самое старое','Грудь и спина' in await E("el('gvtMbox').textContent"))
    await E("el('gvtModal').hidden=true")

    # ---- 6. вес 6-го появления подтверждается до старта
    await E("""(()=>{T.fresh(3);const v=g2Store(),P=v.progs[0];['bInc','pullLean'].forEach(k=>{const pl=T.plan(P,3,k,100);P.st[3].ws[k]={ptr:6,plan:pl,scheme:"543",W0:100,sug6:pl[5]};});
      g2MainKeysOf(P,3).filter(k=>!P.st[3].ws[k]).forEach(k=>{P.st[3].ws[k]={ptr:7,plan:T.plan(P,3,k,100),scheme:"543",W0:100,conf6:true};});g2Save(v);})()""")
    started=await E("T.open()")
    ok('без подтверждения тренировка не стартует, открыт запрос веса',not started and await E("!el('gvtModal').hidden&&!!el('g2c6_bInc')"))
    await E("el('g2c6_bInc').value='112,5';el('g2c6Go').click();T.begin()")
    ok('после подтверждения вес сохранён и тренировка началась',await E("T.ws(3,'bInc').conf6&&T.ws(3,'bInc').plan[6]===112.5&&!!(current&&current.program.g2)&&current.sets[0][0].w===112.5"))
    await E("T.finish([])")

    # ---- 7. переход на следующий этап закрывает нерешённое
    await E("""(()=>{T.fresh(1);const v=g2Store(),P=v.progs[0];P.st[1].ws.dDecl={w:40};
      P.recs.push({uid:"c1",stage:1,kind:"train",variant:"А",status:"full",setsDone:1,setsPlanned:1,ton:1,durMin:1,ex:[],dec:[{key:"dDecl",type:"inc_confirm",cur:40,sug:42,pct:5,txt:"Жим: верх диапазона"}]});g2Save(v);g2Render();})()""")
    await E("el('g2NextSt').click()")
    ok('предупреждение называет нерешённое',await E("document.body.textContent.includes('Не решено по весу')"))
    await E("el('g2NextSt').click()")
    ok('после перехода решение закрыто «без решения», вес не изменён',await E("(()=>{const P=g2Store().progs[0];return P.stage===2&&P.recs[0].dec[0].choice==='closed'&&P.st[1].ws.dDecl.w===40})()"))

    # ---- 8. этапы I–III не изменились: суперсет из двух, счётчик «N из M»
    await E("""(()=>{T.fresh(0);const v=g2Store(),P=v.progs[0];g2MainKeysOf(P,0).forEach(k=>{P.st[0].ws[k]={w:60};});g2Save(v);})()""")
    await E("T.open()")
    ok('этап I: два суперсета по два упражнения',await E("JSON.stringify(current.program.g2.units)==='[[0,1],[2,3]]'&&current.program.focus.includes('занятие 1 из 18')"),await E("current.program.focus"))
    await E("T.finish([])")
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
