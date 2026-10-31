# Синхронизация циклических программ между устройствами: слияние по частям (метки времени), счётчики не уменьшаются,
# решения по весу не возвращаются, старые данные без меток сливаются как раньше; облако Claude подтягивается при возвращении.
# Запуск: python3 tests/sync_merge_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools,json
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
HELP="""(()=>{let tick=0;const RD=Date,realNow=RD.now.bind(RD);
 /* часы идут вперёд между «устройствами»: и Date.now(), и new Date() */
 window.Date=class extends RD{constructor(...a){super(...(a.length?a:[realNow()+tick]));} static now(){return realNow()+tick;}};
 window.T={
 later(){tick+=60000;},
 snap(){return JSON.parse(localStorage.getItem(G2K));},
 load(x){localStorage.setItem(G2K,JSON.stringify(x));},
 fresh(){localStorage.removeItem(G2K);const v=g2Store();const P=g2New({stage:0,step:2.5});P.st[0].setup=true;g2MainKeysOf(P,0).forEach(k=>P.st[0].ws[k]={w:60});v.progs.push(P);v.activeId=P.id;g2Save(v);},
 train(){T.later();const v=g2Store(),P=g2Active(v),sl=g2NextSlot(P),w=g2Build(P,sl);
   current={program:w,startedAt:new Date(Date.now()).toISOString(),sets:w.preset.map(ss=>ss.map(s=>({...s,done:true,r:s.pr})))};const r=g2Record();current=null;return r;},
 setRest(n){T.later();g2Render();const b=el("gvtBody").querySelector('[data-rest="'+n+'"]');b.click();},
};})()"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    await pg.evaluate(HELP);E=pg.evaluate

    # ---- 6. облако Claude: подтягивание при возвращении (не чаще раза в 30 с) и отправка при уходе
    r=await E("""(async()=>{T.fresh();const P=g2Store();const cloudV=JSON.parse(JSON.stringify(P));cloudV.progs[0].recs.push({uid:"cloud-1",stage:0,kind:"train",finishedAt:"2099-01-01",updatedAt:"2099-01-01",ex:[],dec:[]});
      let sets=0,gets=0;const doc={get:async()=>{gets++;return {exists:true,data:()=>({gvt2:cloudV})};},set:async()=>{sets++;}};
      CLOUD={db:{doc:()=>doc},user:{}};cloudReady=true;
      let vis="visible";Object.defineProperty(document,"visibilityState",{configurable:true,get:()=>vis});
      document.dispatchEvent(new Event("visibilitychange"));await new Promise(r=>setTimeout(r,200));const early=gets;
      T.later();document.dispatchEvent(new Event("visibilitychange"));await new Promise(r=>setTimeout(r,300));
      const pulled=g2Store().progs[0].recs.some(r=>r.uid==="cloud-1");
      cloudPush();const s0=sets;vis="hidden";document.dispatchEvent(new Event("visibilitychange"));await new Promise(r=>setTimeout(r,100));
      CLOUD=null;cloudReady=false;return {early:early,gets:gets,pulled:pulled,flushed:sets>s0}})()""")
    ok('сразу после открытия повторной загрузки нет (30 с)',r['early']==0,r)
    ok('возвращение в приложение подтянуло запись с другого устройства',r['gets']==1 and r['pulled'],r)
    ok('уход из приложения сразу отправляет несохранённое',r['flushed'],r)
    # ---- 1. A открыт со «вчера», B тренируется 3 раза и подтверждает прибавку; A меняет дни отдыха
    await E("T.fresh();for(let i=0;i<4;i++)T.train();window.XA0=T.snap();")
    await E("""(()=>{for(let i=0;i<3;i++)T.train();const P=g2Active(),r=P.recs.slice(-1)[0],i=r.dec.findIndex(d=>!d.done&&d.type==='inc_confirm');
      if(i>=0){T.later();g2Resolve(r.uid,i,'yes',0);}window.XB=T.snap();})()""")
    bst=await E("(()=>{const P=XB.progs[0];return {n:P.recs.length,pos:P.st[0].pos,ws:P.st[0].ws}})()")
    await E("T.load(XA0);T.setRest(2);window.XA=T.snap();")
    for name,expr in (('A ← облако B',"mergeG2(XA,XB)"),('B ← облако A',"mergeG2(XB,XA)")):
      r=await E(f"(()=>{{const P={expr}.progs[0];return {{n:P.recs.length,pos:P.st[0].pos,ws:P.st[0].ws,rest:P.rest}}}})()")
      ok(f'{name}: 7 занятий, счётчик 7 (не откатился на 4)',r['n']==7 and r['pos']==7,r['pos'])
      ok(f'{name}: веса и прибавки с B',json.dumps(r['ws'],sort_keys=True)==json.dumps(bst['ws'],sort_keys=True),r['ws'])
      ok(f'{name}: дни отдыха = 2 (настройка с A)',r['rest']==2,r['rest'])
    ok('прибавка на B действительно была (проверка сценария)',any(v['w']!=60 for v in bst['ws'].values()),bst['ws'])

    # ---- 2. решение принято на A, а на B (позже менял шаг) оно ещё висит
    await E("""(()=>{T.fresh();T.train();const P=g2Active();const r=P.recs[0];window.Xbase=T.snap();
      const i=r.dec.findIndex(d=>d.type==='inc_confirm');window.Xdi=i;window.Xduid=r.uid;})()""")
    has=await E("Xdi>=0")
    if has:
      await E("T.load(Xbase);T.later();g2Resolve(Xduid,Xdi,'yes',0);window.XA=T.snap();")
      await E("T.load(Xbase);T.later();(()=>{const v=g2Store();v.progs[0].step=2;v.progs[0].updatedAt=new Date(Date.now()).toISOString();g2Save(v);})();window.XB=T.snap();")
      r=await E("""(()=>{const out=[];[mergeG2(XA,XB),mergeG2(XB,XA)].forEach(M=>{const P=M.progs[0],d=P.recs[0].dec[Xdi],k=d.key;out.push({done:d.done,w:P.st[0].ws[k].w,sug:d.sug,step:P.step});});return out;})()""")
      ok('принятое на A решение не возвращается на B (оба направления)',all(x['done'] and x['w']==x['sug'] for x in r),r)
      ok('настройка шага с B сохраняется',all(x['step']==2 for x in r),r)
    else: ok('в сценарии есть решение по весу',False)

    # ---- 3. параллельные тренировки на двух устройствах
    await E("T.fresh();T.train();T.train();window.Xbase=T.snap();T.train();window.XA=T.snap();T.load(Xbase);T.train();window.XB=T.snap();")
    r=await E("(()=>{const P=mergeG2(XA,XB).progs[0],Q=mergeG2(XB,XA).progs[0];return [P.recs.length,P.st[0].pos,Q.recs.length,Q.st[0].pos]})()")
    ok('параллельно: все 4 записи сохранены, счётчик не уменьшился',r[0]==4 and r[2]==4 and r[1]>=3 and r[3]>=3,r)

    # ---- 4. старые данные без меток — как раньше (целиком из более новой копии), ничего не теряется
    r=await E("""(()=>{const a=JSON.parse(JSON.stringify(XA)),b=JSON.parse(JSON.stringify(XB));[a,b].forEach(v=>v.progs.forEach(p=>delete p._t));
      a.progs[0].updatedAt="2030-01-01T00:00:00.000Z";const P=mergeG2(a,b).progs[0];return {n:P.recs.length,pos:P.st[0].pos,apos:a.progs[0].st[0].pos,t:!!P._t}})()""")
    ok('без меток: записи объединены, состояние — из более новой копии',r['n']==4 and r['pos']==r['apos'] and not r['t'],r)

    # ---- 5. GVT 1 и 5/3/1: та же схема (метки ставятся при сохранении, части сливаются)
    r=await E("""(()=>{const now=()=>new Date(Date.now()).toISOString();
      const c={id:"c1",createdAt:now(),updatedAt:now(),target:{A:70,B:70,C:70},recs:[],note:"x"};localStorage.setItem(GVTK,JSON.stringify({cycles:[c],activeId:"c1"}));
      const base=gvtStore();
      T.later();let v=JSON.parse(JSON.stringify(base));v.cycles[0].target.A=60;v.cycles[0].recs.push({uid:"r1",updatedAt:now(),finishedAt:now()});v.cycles[0].updatedAt=now();gvtSave(v);const Bv=gvtStore();
      localStorage.setItem(GVTK,JSON.stringify(base));T.later();v=gvtStore();v.cycles[0].note="y";v.cycles[0].updatedAt=now();gvtSave(v);const Av=gvtStore();
      const M=mergeGvt(Av,Bv).cycles[0],N=mergeGvt(Bv,Av).cycles[0];
      return {a:[M.target.A,M.note,M.recs.length],b:[N.target.A,N.note,N.recs.length],stamped:!!(Bv.cycles[0]._t&&Bv.cycles[0]._t["target.A"])}})()""")
    ok('GVT 1: процент дня с B и настройка с A, записи объединены',r['a']==[60,'y',1] and r['b']==[60,'y',1] and r['stamped'],r)
    r=await E("""(()=>{localStorage.setItem(W5K,JSON.stringify({cycles:[{id:"w1",createdAt:"x",updatedAt:"x",tm:{bench:100},recs:[]}],activeId:"w1"}));
      const v=w5Store();v.cycles[0].tm.bench=105;w5Save(v);return !!(w5Store().cycles[0]._t||{})["tm.bench"]})()""")
    ok('5/3/1: изменение тренировочного максимума получает метку',r)

    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
