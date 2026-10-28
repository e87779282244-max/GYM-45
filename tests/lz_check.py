# Стритлифтинг: Level Zero — выход силой + брусья/турник с весом, прогрессия по худшему подходу, разгрузка с проходкой.
# Запуск: python3 tests/lz_check.py index.html [папка_скриншотов]
import asyncio,os,sys,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
HTML=os.path.abspath(sys.argv[1]);SHOT=sys.argv[2] if len(sys.argv)>2 else None
tmp=tempfile.mkdtemp();shutil.copy(HTML,tmp+'/index.html')
if os.path.isdir(os.path.dirname(HTML)+'/media'):os.symlink(os.path.dirname(HTML)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
# выполнить следующую тренировку: reps — {lift:[повторы]}, mu — число выходов, test — {lift:вес}
DO="""((reps,mu,test)=>{const P=lzActive(),st=lzState(P);startWorkout(lzPlan(P,st),true);el('dayStart').click();
  const rows=current.program.lz.rows;rows.forEach((R,i)=>{const ws=current.sets[i].filter(s=>!s.warm);current.sets[i].filter(s=>s.warm).forEach(s=>s.done=true);
    if(R.mu)ws.forEach((s,j)=>s.done=j<mu);
    else if(R.test){ws.forEach(s=>s.done=false);const t=test[R.lift];if(t){ws[0].w=t;ws[0].done=true;}}
    else if(R.lift){const rr=reps[R.lift]||[];ws.forEach((s,j)=>{s.r=rr[j]!=null?rr[j]:s.r;s.done=rr[j]!==0;});}});
  finishWorkout();return current==null;})"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    await pg.evaluate("document.querySelector('.disc[data-disc=\"Стритлифтинг\"]').click()");await pg.wait_for_timeout(100)
    ok('Level Zero в «Стритлифтинге»',await pg.evaluate("[...el('streetDays').querySelectorAll('.disc span span')].some(s=>s.textContent==='Рождённый ползать')"))
    await pg.evaluate("[...el('streetDays').querySelectorAll('.disc')].find(b=>b.textContent.includes('Рождённый ползать')).click()");await pg.wait_for_timeout(100)
    await pg.fill('#lzRm_pull','20');await pg.fill('#lzRm_dip','30')
    ok('старт 40% 1ПМ с шагом 1,25',await pg.evaluate("el('lzSt_pull').textContent==='+7,5 кг'&&el('lzSt_dip').textContent==='+12,5 кг'"),await pg.evaluate("el('lzSt_pull').textContent+' '+el('lzSt_dip').textContent"))
    if SHOT:await pg.screenshot(path=SHOT+'/lz-form.png',full_page=True)
    await pg.click('#lzGo');await pg.wait_for_timeout(100)
    pl=await pg.evaluate("(()=>{const P=lzActive(),p=lzPlan(P,lzState(P));return {n:p.name,ex:p.ex.map(e=>e[0]),dip:p.preset[1].map(s=>[s.w,s.r,!!s.warm]),mu:p.preset[0].length,rest:p.ex[0][6]}})()")
    ok('Пн: выход силой 10×1 (отдых 2 мин) + брусья + турник',pl['ex']==['Выход силой','Отжимания на брусьях с весом','Подтягивания с весом'] and pl['mu']==10 and pl['rest']==120,pl['ex'])
    ok('брусья: разминка 50/65/80% + 3×8 по 12,5',pl['dip']==[[6.25,6,True],[8.75,5,True],[10,3,True],[12.5,8,False],[12.5,8,False],[12.5,8,False]],pl['dip'])
    if SHOT:await pg.screenshot(path=SHOT+'/lz-main.png',full_page=True)
    await pg.evaluate(DO+"({dip:[8,8,8],pull:[8,8,7]},9,{})")
    ok('после тренировки — экран Level Zero с итогом',await pg.evaluate("currentScreen==='lz'&&el('lzBody').textContent.includes('Итог')&&el('lzBody').textContent.includes('9/10')"))
    st=await pg.evaluate("(()=>{const s=lzState(lzActive());return {d:s.lifts.dip.W,p:s.lifts.pull.W,next:s.next,Ld:s.lifts.dip.L}})()")
    ok('8/8/8 → +2,5; худший 7 → +1,25; дальше Ср',st['d']==15 and st['p']==8.75 and st['next']=='wed',st)
    wed=await pg.evaluate("(()=>{const P=lzActive(),p=lzPlan(P,lzState(P));return p.preset.slice(1).map(x=>x.filter(s=>!s.warm).map(s=>s.w))})()")
    ok('Ср: 2×8 с весом 60% от Пн (7,5 / 5)',wed==[[7.5,7.5],[5,5]],wed)
    await pg.evaluate(DO+"({dip:[8,8],pull:[8,8]},10,{})")
    ok('после Ср лёгкий вес +1,25',await pg.evaluate("(()=>{const s=lzState(lzActive());return s.lifts.dip.L===8.75&&s.next==='fri'})()"))
    await pg.evaluate(DO+"({dip:[8,8,5],pull:[6,6,6]},10,{})")
    st=await pg.evaluate("(()=>{const s=lzState(lzActive());return {d:s.lifts.dip.W,p:s.lifts.pull.W,w:s.week,next:s.next}})()")
    ok('Пт: худший 5 → вес тот же; 6 → +0,5; неделя 2',st=={'d':15,'p':9.25,'w':2,'next':'mon'},st)
    ok('в истории — раздел стритлифтинг',await pg.evaluate("safe.get().slice(-1)[0].sec==='street'&&safe.get().length===3"))
    # 2 недели без прибавки → разгрузка
    for r in ["{dip:[6,6,6],pull:[5,5,5]}","{dip:[8,8],pull:[8,8]}","{dip:[5,5,5],pull:[6,6,5]}","{dip:[6,5,5],pull:[5,5,5]}","{dip:[8,8],pull:[8,8]}","{dip:[6,6,6],pull:[6,6,6]}"]:
      await pg.evaluate(DO+"("+r+",10,{})")
    st=await pg.evaluate("(()=>{const s=lzState(lzActive());return {dl:!!s.deload,next:s.next,w:s.week}})()")
    ok('2 недели с прибавкой ≤0,5 кг → разгрузочная неделя',st=={'dl':True,'next':'dmon','w':4},st)
    dm=await pg.evaluate("(()=>{const P=lzActive(),s=lzState(P),p=lzPlan(P,s);return [p.preset[1].filter(x=>!x.warm).map(x=>x.w),s.lifts.dip.W]})()")
    ok('разгрузка Пн: 2×8 на 70% прошлой Пт (15,5 → 11,25)',dm[0]==[11.25,11.25],dm)
    await pg.evaluate(DO+"({dip:[8,8],pull:[8,8]},10,{})");await pg.evaluate(DO+"({dip:[8,8],pull:[8,8]},10,{})")
    tp=await pg.evaluate("(()=>{const P=lzActive(),p=lzPlan(P,lzState(P));return [p.name,p.ex.map(e=>e[0])]})()")
    ok('Пт разгрузки: проходка, затем выходы, приседания по желанию',tp[1]==['Отжимания на брусьях с весом','Подтягивания с весом','Выход силой','Приседания со штангой'],tp)
    await pg.evaluate(DO+"({},10,{dip:40,pull:27.5})")
    st=await pg.evaluate("(()=>{const s=lzState(lzActive());return {d:s.lifts.dip.W,dl:s.lifts.dip.L,rm:s.lifts.dip.rm,p:s.lifts.pull.W,dlz:!!s.deload,next:s.next,reg:rmReg()['Отжимания на брусьях с весом']}})()")
    ok('проходка: новый 1ПМ 40 → рабочий 40% (16,25), лёгкий 10, в «Рабочие веса»',st=={'d':16.25,'dl':10,'rm':40,'p':11.25,'dlz':False,'next':'mon','reg':40},st)
    # новичок: повторы без веса
    await pg.evaluate("lzFormOpen=true;renderLz()");await pg.fill('#lzRm_pull','');await pg.fill('#lzRp_pull','13');await pg.fill('#lzRm_dip','');await pg.fill('#lzRp_dip','24')
    await pg.click('#lzGo');await pg.click('#lzGo');await pg.wait_for_timeout(100)
    bp=await pg.evaluate("(()=>{const P=lzActive(),p=lzPlan(P,lzState(P));return [p.ex.map(e=>[e[0],e[2],e[3]]),lzStore().progs.filter(x=>x.closedAt).length]})()")
    ok('новичок: без веса, 3×13 и 3×24, прошлая программа в архиве',bp[0][1]==['Отжимания на брусьях','24',0] and bp[0][2]==['Подтягивания','13',0] and bp[1]==1,bp)
    await pg.evaluate(DO+"({dip:[25,25,25],pull:[13,13,13]},6,{})")
    st=await pg.evaluate("(()=>{const s=lzState(lzActive());return [s.lifts.dip.mode,s.lifts.dip.W,s.lifts.pull.mode,s.lifts.pull.R]})()")
    ok('25 на брусьях → переход на вес (+2,5 кг × 8); турник 13 → цель 14',st==['kg',2.5,'reps',14],st)
    wl=await pg.evaluate("(()=>{const P=lzActive(),p=lzPlan(P,lzState(P));return p.ex.map(e=>[e[0],e[2]])})()")
    ok('Ср новичка: ~60% повторов',wl[2]==['Подтягивания','8'],wl)
    ok('«Активные программы»: Level Zero',await pg.evaluate("mpList().some(x=>x.k==='lz')"))
    ok('облако: снимок и слияние',await pg.evaluate("(()=>{const s=cloudSnapshot();const m=mergeLz(lzStore(),{progs:[{id:'x',createdAt:'2020',recs:[]}],activeId:null});return s.lz.progs.length===2&&m.progs.length===3&&m.activeId===lzStore().activeId})()"))
    await pg.evaluate("show('lz')");await pg.wait_for_timeout(100)
    ok('без горизонтальной прокрутки',await pg.evaluate("document.documentElement.scrollWidth<=window.innerWidth"))
    if SHOT:await pg.screenshot(path=SHOT+'/lz-beginner.png',full_page=True)
    ok('без ошибок JS',not errs,errs)
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
