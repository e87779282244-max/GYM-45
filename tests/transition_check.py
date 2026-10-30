# Переход между программами бодибилдинга: стартовый вес от лучшего результата (−10 % / −18 % после перерыва), GVT не образец,
# лёгкая неделя после программы без разгрузки (по желанию).
# Запуск: python3 tests/transition_check.py index.html
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
    rec="(d,nm,w,r,au)=>({date:addDays(localDate(),-d),name:nm,vol:1,log:{'Жим штанги лёжа':[1,2,3].map(()=>({w:w,r:r,done:true}))},au:au?{id:au,w:0}:undefined})"
    prog="{name:'Тест',focus:'т',au:{id:'cbum',w:0},sec:'body',ex:[['Жим штанги лёжа',3,'12–15',60,undefined,'12–15 повт.']]}"
    async def start(h):
      await pg.evaluate(f"(()=>{{const R={rec};safe.set({h});current=null;startWorkout({prog},false);el('dayStart').click();}})()");await pg.wait_for_timeout(100)
      return await pg.evaluate("[current.sets[0].map(s=>s.w).join(),current.sets[0].map(s=>s.r).join(),(current.why||{})[0]||'']")
    r=await start("[R(3,'Последний патрон',100,6,'pcfb')]")
    ok('новая программа: 100×6 → под 12–15 с −10 % = 70 кг × 12',r[0]=='70,70,70' and r[1]=='12,12,12' and '−10 %' in r[2],r)
    r=await start("[R(20,'Последний патрон',100,6,'pcfb')]")
    ok('перерыв 20 дней → −18 %: 65 кг',r[0]=='65,65,65' and '−18 %' in r[2],r)
    r=await start("[R(5,'Последний патрон',100,6,'pcfb'),R(2,'GVT · I · A',60,10,null)]")
    ok('GVT 60×10 не берётся как образец',r[0]=='70,70,70',r)
    r=await start("[R(5,'Последний патрон',100,6,'pcfb'),R(2,'Сдохни',70,12,'cbum')]")
    ok('упражнение уже было в этой программе — обычная прогрессия',r[0]=='70,70,70' and 'добери' in r[2],r)
    r=await start("[R(5,'Последний патрон',100,6,'pcfb'),R(2,'Сдохни',70,15,'cbum')]")
    ok('в программе: верх диапазона → +2,5 кг',r[0]=='72.5,72.5,72.5',r)
    ok('разгрузка распознаётся: «Мясорубка» есть, «Сдохни, но красиво» нет',await pg.evaluate("lwHasDeload(lwFrom('jc'))&&lwHasDeload(lwFrom('wl'))&&lwHasDeload(lwFrom('fbn'))&&!lwHasDeload(lwFrom('cbum'))"))
    # программа без разгрузки пройдена → предложение лёгкой недели после окна заминки
    await pg.evaluate("""(()=>{current=null;const P=lwFrom('cbum');const h=[];for(let i=0;i<P.total-1;i++)h.push({date:'2026-09-01',name:'x',vol:1,log:{'Жим штанги лёжа':[{w:100,r:10,done:true}]},au:{id:'cbum',w:0}});safe.set(h);
      const v=auSt();if(v.act)delete v.act.cbum;auSave(v);auPlanStart(P,auPlanNext(P));el('dayStart').click();current.sets.forEach(se=>se.forEach(s=>{s.done=true;if(!s.r)s.r=10;}));finishWorkout();})()""");await pg.wait_for_timeout(700)
    ok('сначала окно заминки',await pg.evaluate("!el('coolModal').hidden&&!!el('coolSkip')"))
    await pg.evaluate("el('coolSkip').click()");await pg.wait_for_timeout(1300)
    ok('затем — предложение лёгкой недели',await pg.evaluate("!el('coolModal').hidden&&!!el('lwYes')&&el('coolModal').textContent.includes('лёгкую неделю')"),await pg.evaluate("el('coolModal').textContent.slice(0,200)"))
    await pg.evaluate("el('lwYes').click()");await pg.wait_for_timeout(200)
    st=await pg.evaluate("(()=>{const a=lwStore().act,P=lwFrom('cbum'),d=lwDays(P).days[0];return {a:!!a,n:a&&a.n,scr:currentScreen,ex:dayView.p.ex.map(e=>[e[0],e[1],e[3]]),orig:d.ex.map(e=>[e[0],e[1]]),dash:mpList().some(x=>x.k==='lw')}})()")
    ok('лёгкая неделя активна, есть в «Сегодня», открыт день',st['a'] and st['dash'] and st['scr']=='day',st)
    ok('подходов на треть меньше',all(x[1]==max(1,round(o[1]*2/3)) for x,o in zip(st['ex'],st['orig'])),st['ex'][:3])
    bench=[x for x in st['ex'] if x[0]=='Жим штанги лёжа']
    ok('вес −15 % от последнего (100 → 85)',not bench or bench[0][2]==85,bench)
    # пройти все тренировки лёгкой недели
    n=st['n']
    for k in range(n):
      await pg.evaluate("(()=>{coolOffer=function(){};if(!current||!current.program.lw){lwGo();el('dayStart').click();}current.sets.forEach(se=>se.forEach(s=>{s.done=true;if(!s.r)s.r=8;}));finishWorkout();})()");await pg.wait_for_timeout(150)
    ok('лёгкая неделя завершена и ушла из «Сегодня»',await pg.evaluate("!lwStore().act&&lwStore().hist.length===1&&!mpList().some(x=>x.k==='lw')"))
    ok('записи лёгкой недели помечены и не образец',await pg.evaluate("safe.get().slice(-1)[0].lw===1&&lastResult('Жим штанги лёжа')&&lastResult('Жим штанги лёжа').sets[0].w===100"))
    ok('лёгкая неделя в облачном снимке',await pg.evaluate("!!cloudSnapshot().lw&&cloudSnapshot().lw.hist.length===1"))
    # программа с разгрузкой — без предложения
    await pg.evaluate("""(()=>{coolOffer=function(){};el('coolModal').hidden=true;const P=lwFrom('dc');const h=[];for(let i=0;i<P.total-1;i++)h.push({date:'2026-09-01',name:'x',vol:1,log:{},au:{id:'dc',w:0}});safe.set(h);
      auPlanStart(P,auPlanNext(P));el('dayStart').click();current.sets.forEach(se=>se.forEach(s=>{s.done=true;if(!s.r)s.r=8;}));finishWorkout();})()""");await pg.wait_for_timeout(1800)
    ok('после программы с разгрузкой — не предлагается',await pg.evaluate("el('coolModal').hidden"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
