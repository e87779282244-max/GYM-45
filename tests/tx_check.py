# Пауэрлифтинг: «Техасский рейнджер» (Texas Method) — старт, неделя объём/лёгкий/рекорд, чередование жимов,
# прогрессия рекорда, сброс −10 % после двух промахов, 4 дня, лёгкий объёмный день, история и облако.
# Запуск: python3 tests/tx_check.py index.html [папка_скриншотов]
import asyncio,os,sys,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
HTML=os.path.abspath(sys.argv[1]);SHOT=sys.argv[2] if len(sys.argv)>2 else None
tmp=tempfile.mkdtemp();shutil.copy(HTML,tmp+'/index.html')
if os.path.isdir(os.path.dirname(HTML)+'/media'):os.symlink(os.path.dirname(HTML)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
DONE="current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));finishWorkout()"
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';localStorage.setItem(KEY,JSON.stringify([{date:'2026-01-01',name:'Старая',vol:1,log:{}}]))")
    await pg.evaluate("document.querySelector('.disc[data-disc=\"Пауэрлифтинг\"]').click()");await pg.wait_for_timeout(100)
    ok('в «Пауэрлифтинге» есть «Техасский рейнджер»',await pg.evaluate("[...el('pwrPrograms').querySelectorAll('.disc')].some(b=>b.textContent.includes('Техасский рейнджер'))"))
    await pg.evaluate("[...el('pwrPrograms').querySelectorAll('.disc')].find(b=>b.textContent.includes('Техасский рейнджер')).click()");await pg.wait_for_timeout(100)
    ok('экран программы с формой старта',await pg.evaluate("currentScreen==='tx'&&!!el('txGo')"))
    await pg.evaluate("el('txT_sq').value='100';el('txT_bp').value='80';el('txT_pr').value='50';el('txT_dl').value='120';el('txT_pc').value='60';el('txGo').click()");await pg.wait_for_timeout(100)
    if SHOT:await pg.screenshot(path=SHOT+'/tx.png',full_page=True)
    ok('программа активна, неделя 1, следующая — Пн · объём',await pg.evaluate("(()=>{const P=txActive(),s=txState(P);return s.week===1&&s.next==='vd'})()"))
    pl=await pg.evaluate("(()=>{const P=txActive(),p=txPlan(P,txState(P));return p.ex.map(e=>e[0]+'|'+e[1]+'|'+e[2]+'|'+e[3])})()")
    ok('Пн: присед 5×5 90 кг, жим лёжа 5×5 72,5, становая 1×5 120',pl[:3]==['Приседания со штангой|5|5|90','Жим штанги лёжа|5|5|72.5','Становая тяга|1|5|120'],pl)
    await pg.evaluate("el('txNext').querySelector('.disc').click()");await pg.wait_for_timeout(100)
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(100)
    ok('тренировка: разминочные подходы перед рабочими',await pg.evaluate("current.sets[0].filter(s=>s.warm).length===4&&current.sets[0].filter(s=>!s.warm).length===5"))
    await pg.evaluate(DONE);await pg.wait_for_timeout(150)
    ok('после Пн — экран программы с итогом, становая +5 дальше',await pg.evaluate("currentScreen==='tx'&&el('txBody').textContent.includes('Итог')&&txState(txActive()).t.dl===125"))
    pl=await pg.evaluate("(()=>{const P=txActive(),p=txPlan(P,txState(P));return p.ex.map(e=>e[0]+'|'+e[1]+'|'+e[2]+'|'+e[3])})()")
    ok('Ср: присед 2×5 на 80 % объёма (72,5), жим стоя 3×5',pl[0]=='Приседания со штангой|2|5|72.5' and pl[1].startswith('Жим штанги стоя|3|5'),pl)
    await pg.evaluate("startWorkout(txPlan(txActive(),txState(txActive())),true);el('dayStart').click();"+DONE);await pg.wait_for_timeout(150)
    pl=await pg.evaluate("(()=>{const P=txActive(),p=txPlan(P,txState(P));return p.ex.map(e=>e[0]+'|'+e[1]+'|'+e[2]+'|'+e[3])})()")
    ok('Пт: рекорд присед 1×5 100, жим лёжа 1×5 80, взятие 5×3 60',pl==['Приседания со штангой|1|5|100','Жим штанги лёжа|1|5|80','Силовое взятие на грудь|5|3|60'],pl)
    # рекорд в приседе, промах в жиме
    await pg.evaluate("startWorkout(txPlan(txActive(),txState(txActive())),true);el('dayStart').click();current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));current.sets[1].filter(s=>!s.warm)[0].r=3;finishWorkout()");await pg.wait_for_timeout(150)
    st=await pg.evaluate("(()=>{const s=txState(txActive());return [s.week,s.t.sq,s.t.bp,s.t.pc,s.main]})()")
    ok('неделя 2: присед 105, жим лёжа остался 80, взятие 62,5, главный жим — стоя',st==[2,105,80,62.5,'pr'],st)
    pl=await pg.evaluate("(()=>{const P=txActive(),p=txPlan(P,txState(P));return p.ex.map(e=>e[0]+'|'+e[3])})()")
    ok('неделя 2, Пн: главный жим — жим стоя 5×5 (45)',pl[1]=='Жим штанги стоя|45',pl)
    # промах в жиме лёжа ещё раз → сброс −10 %
    await pg.evaluate("(()=>{const v=txStore(),P=txActive(v);for(let i=0;i<2;i++){P.recs.push({uid:'x'+i,kind:'id',week:3,finishedAt:'2099-0'+(i+1)+'-01T00:00:00Z',lifts:{bp:{w:80,prog:true,reps:[2],need:[5]}}});}txSave(v);})()")
    ok('два промаха подряд → жим лёжа −10 % (72,5)',await pg.evaluate("txState(txActive()).t.bp")==72.5)
    ok('в истории — тренировки с разделом pwr, старая запись цела',await pg.evaluate("(()=>{const h=safe.get();return h[0].name==='Старая'&&h.length===4&&h.slice(1).every(x=>x.sec==='pwr'||anSecOf)})()"))
    ok('в «Активных программах» и на главной',await pg.evaluate("mpList().some(x=>x.k==='tx')&&weekPlanOf(mpList().find(x=>x.k==='tx'))===3&&dashNextName(mpList().find(x=>x.k==='tx')).includes('Техасский рейнджер')"))
    ok('облачный снимок и слияние',await pg.evaluate("(()=>{const s=cloudSnapshot();const m=mergeTx({progs:[],activeId:null},s.tx);return s.tx.progs.length===1&&m.progs.length===1})()"))
    # 4 дня и лёгкий объём
    await pg.evaluate("txFormOpen=true;renderTx();el('txT_sq').value='100';el('txT_bp').value='80';el('txT_pr').value='50';el('txT_dl').value='120';el('txT_pc').value='60';el('txDays').value='4';el('txMode').value='easy';el('txPc').value='pause';el('txGo').click();el('txGo')&&el('txGo').click()");await pg.wait_for_timeout(100)
    pl=await pg.evaluate("(()=>{const P=txActive(),out=[];['d1','d2','d3','d4'].forEach(k=>out.push(txPlan(P,txState(P),k).ex.map(e=>e[0]+' '+e[1]+'×'+e[2]).join(', ')));return out})()")
    ok('4 дня: день 1 жимы, день 2 присед + становая с паузой, день 4 рекорд приседа и становая',pl[0].startswith('Жим штанги лёжа 5×5') and 'Становая тяга с паузой у пола 5×3' in pl[1] and pl[3].startswith('Приседания со штангой 1×5') and 'Становая тяга 1×5' in pl[3],pl)
    await pg.evaluate("(()=>{const v=txStore();txActive(v).cfg.days=3;txSave(v);})()")
    pl=await pg.evaluate("(()=>{const P=txActive();return txPlan(P,txState(P),'vd').ex.map(e=>e[0]+' '+e[1]+'×'+e[2]+' '+e[3]).join(', ')})()")
    ok('лёгкий объём: присед 12×2 на 85 %, жим 8×3, становая 15×1',pl.startswith('Приседания со штангой 12×2 85') and 'Становая тяга 15×1' in pl,pl)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
