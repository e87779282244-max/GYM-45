# Единый движок программ + прогрессия весов.
# Запуск: python3 tests/engine_check.py index.html [папка_скриншотов]
import asyncio,os,sys,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
HTML=os.path.abspath(sys.argv[1]);SHOT=sys.argv[2] if len(sys.argv)>2 else None
tmp=tempfile.mkdtemp();shutil.copy(HTML,tmp+'/index.html')
if os.path.isdir(os.path.dirname(HTML)+'/media'):os.symlink(os.path.dirname(HTML)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
# записать k тренировок программы id (как будто сделаны)
FAKE="""((id,k,day)=>{const h=safe.get();for(let i=0;i<k;i++)h.push({date:day||localDate(),name:'x',vol:1,au:{id:id,w:0},log:{}});localStorage.setItem(KEY,JSON.stringify(h));})"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    # --- все программы на движке ---
    n=await pg.evaluate("auAll().filter(p=>p.plan).length")
    ok('на движке все программы с неделями (≥28)',n>=28,n)
    tot=await pg.evaluate("Object.fromEntries(['y3t','bts','jc','dc','bg','fst7','hiit','wl','jpcm','cbum','bp180b','bp180a','pcfb','ta','pl5','fbn','phil'].map(id=>[id,auTotal(auAll().find(p=>p.id===id))]))")
    ok('длина программ совпадает с описанием',tot=={'y3t':60,'bts':60,'jc':72,'dc':22,'bg':24,'fst7':44,'hiit':36,'wl':32,'jpcm':54,'cbum':48,'bp180b':108,'bp180a':204,'pcfb':24,'ta':163,'pl5':21,'fbn':24,'phil':24},tot)
    # --- Y3T: 1A → 1B → 2 → 3 по кругу ---
    await pg.evaluate("authOpen(AUTH.find(p=>p.id==='y3t'))");await pg.wait_for_timeout(100)
    ok('до старта: «Начать программу · 60 тренировок»',await pg.evaluate("document.querySelector('.au-start').textContent.includes('60 тренировок')&&!document.querySelector('.au-cont')"))
    await pg.evaluate("document.querySelector('.au-start').click()");await pg.wait_for_timeout(100)
    Y="(()=>{const p=AUTH.find(q=>q.id==='y3t'),n=auPlanNext(p);return [n.w,n.d]})()"
    ok('следующая: Неделя 1A, день 1',await pg.evaluate(Y)==[0,0])
    await pg.evaluate(FAKE+"('y3t',5)");ok('после 5: Неделя 1B',await pg.evaluate(Y)==[1,0])
    await pg.evaluate(FAKE+"('y3t',15)");ok('после 20: снова 1A (второй круг)',await pg.evaluate(Y)==[0,0])
    await pg.evaluate(FAKE+"('y3t',40)");ok('после 60: программа пройдена',await pg.evaluate("auPlanNext(AUTH.find(q=>q.id==='y3t'))===null&&auDone(AUTH.find(q=>q.id==='y3t'))"))
    # --- DC: 18 занятий блица, потом разгрузка ---
    await pg.evaluate("localStorage.setItem(KEY,'[]');const v=auSt();v.act={dc:{start:localDate(),base:0}};auSave(v)")
    await pg.evaluate(FAKE+"('dc',17)");d1=await pg.evaluate("(()=>{const n=auPlanNext(AUTH.find(p=>p.id==='dc'));return [n.w,n.d]})()")
    await pg.evaluate(FAKE+"('dc',1)");d2=await pg.evaluate("(()=>{const n=auPlanNext(AUTH.find(p=>p.id==='dc'));return [n.w,n.d]})()")
    ok('DC: 18-я — B3 блица, 19-я — разгрузка',d1==[0,5] and d2==[1,0],(d1,d2))
    # --- вариант на выбор (Картер): следующая — из выбранной вкладки ---
    await pg.evaluate("const v=auSt();v.act={pcfb:{start:localDate(),base:0}};auSave(v);authSetWeek(AUTH.find(p=>p.id==='pcfb'),2)")
    ok('Картер: вариант 3 выбран — следующая из него',await pg.evaluate("auPlanNext(AUTH.find(p=>p.id==='pcfb')).w===2"))
    # --- продолжение уже начатой программы ---
    await pg.evaluate("localStorage.setItem(KEY,'[]');const v=auSt();v.act={};auSave(v)");await pg.evaluate(FAKE+"('bts',7)")
    await pg.evaluate("authOpen(AUTH.find(p=>p.id==='bts'))");await pg.wait_for_timeout(100)
    ok('уже сделано 7 → кнопка «Продолжить»',await pg.evaluate("!!document.querySelector('.au-cont')&&document.querySelector('.au-cont').textContent.includes('7')"))
    await pg.evaluate("document.querySelector('.au-cont').click()");await pg.wait_for_timeout(100)
    ok('продолжение: позиция 7 → вкладка «Недели 2–5»',await pg.evaluate("(()=>{const p=AUTH.find(q=>q.id==='bts');return auPos(p)===7&&auPlanNext(p).w===1&&document.querySelector('.au-prog').textContent.includes('7 / 60')})()"))
    if SHOT:await pg.screenshot(path=SHOT+'/engine-bts.png',full_page=True)
    ok('дата: 5 дней в неделю → завтра после сегодняшней',await pg.evaluate("(()=>{const d=new Date();d.setDate(d.getDate()+1);return auPlanDate(AUTH.find(q=>q.id==='bts'))===localDate(d)})()"))
    ok('в «Активных программах» с номером тренировки',await pg.evaluate("mpList().some(x=>x.k==='au:bts'&&x.s.includes('тренировка 8 из 60'))"))
    # --- бесконечная ротация (BAZA) ---
    await pg.evaluate("localStorage.setItem(KEY,'[]');const v=auSt();v.act={};auSave(v);renderBody();show('body')");await pg.wait_for_timeout(80)
    await pg.evaluate("[...el('bodyProgs').querySelectorAll('.disc')].find(b=>b.textContent.includes('BAZA')).click()");await pg.wait_for_timeout(100)
    await pg.evaluate("document.querySelector('.au-start').click()");await pg.wait_for_timeout(80)
    await pg.evaluate(FAKE+"('baza',4)")
    ok('BAZA по кругу: после 4 — день 2 (Тяга), без конца',await pg.evaluate("(()=>{const n=auPlanNext(BODY[0]);return n.d===1&&auTotal(BODY[0])===null&&!auDone(BODY[0])})()"))
    # --- пауэрлифтинг: Руки титана и 5×5 одной программой ---
    await pg.evaluate("renderPwrPrograms()")
    ok('«Руки титана» и «5×5 · Сила» — программы с прогрессом',await pg.evaluate("['Руки титана','5×5 · Сила'].every(t=>[...el('pwrPrograms').querySelectorAll('.disc')].some(b=>b.textContent.includes(t)))"))
    await pg.evaluate("const r=rmReg();r['Приседания со штангой']=140;rmRegSet(r);authOpen(P5_PROG)");await pg.wait_for_timeout(80)
    await pg.evaluate("document.querySelector('.au-start').click()");await pg.wait_for_timeout(80)
    await pg.evaluate("document.querySelector('.au-go').click()");await pg.wait_for_timeout(100);await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(100)
    ok('5×5: вес от 1ПМ по плану программы, без «первый раз»',await pg.evaluate("current.sets[0][0].w===plW('Приседания со штангой',72.5)&&!(current.why&&current.why[0])"),await pg.evaluate("current.sets[0][0].w"))
    await pg.evaluate("current=null;clearDraft()")
    # --- прогрессия весов ---
    E="['Жим лёжа',3,8,80,null,'6–10 повт. до отказа',120]"
    s1=await pg.evaluate("(()=>{localStorage.setItem(KEY,'[]');const r=rmReg();delete r['Жим лёжа'];rmRegSet(r);return prSug("+E+",{},null)})()")
    ok('первый раз без 1ПМ: поле пустое, ориентир в подсказке',s1['first']==1 and s1['w']==[0,0,0] and '80' in s1['why'],s1)
    s2=await pg.evaluate("(()=>{const r=rmReg();r['Жим лёжа']=100;rmRegSet(r);return prSug("+E+",{},null)})()")
    ok('первый раз с 1ПМ 100: 75 кг (90% расчёта на 6 повт.)',s2['w']==[75,75,75],s2)
    s3=await pg.evaluate("prSug("+E+",{},{sets:[{w:80,r:10},{w:80,r:10},{w:80,r:11}]})")
    ok('все подходы по 10 (верх диапазона) → +2,5 кг и снова 6',s3.get('up')==1 and s3['w']==[82.5,82.5,82.5] and s3['r']==[6,6,6],s3)
    s4=await pg.evaluate("prSug("+E+",{},{sets:[{w:80,r:10},{w:80,r:8},{w:80,r:7}]})")
    ok('не все добрали → вес тот же, объяснение',s4['w'] is None and 'добери до 10' in s4['why'],s4['why'])
    s5=await pg.evaluate("prSug(['Подъём гантелей',3,'10–12',12],{},{sets:[{w:12,r:12},{w:12,r:12},{w:12,r:13}]})")
    ok('гантели → +2 кг',s5['w']==[14,14,14],s5)
    ok('свой вес не трогается',await pg.evaluate("prSug(['Подтягивания',3,10,0],{},{sets:[{w:0,r:10}]})===null"))
    # на экране тренировки — строка «почему такой вес»
    await pg.evaluate("localStorage.setItem(KEY,JSON.stringify([{date:'2026-10-01',name:'t',vol:1,log:{'Жим лёжа':[{w:80,r:10,done:true},{w:80,r:10,done:true},{w:80,r:10,done:true}]}}]))")
    await pg.evaluate("startWorkout({name:'Тест',focus:'тест',ex:["+E+"]},false);el('dayStart').click()");await pg.wait_for_timeout(120)
    ok('тренировка: 82,5 кг × 6 и строка «↑ +2,5 кг»',await pg.evaluate("current.sets[0][0].w===82.5&&current.sets[0][0].r===6&&el('exList').querySelector('.pr-why.up').textContent.includes('+2,5 кг')"))
    if SHOT:await pg.screenshot(path=SHOT+'/engine-why.png')
    pl=await pg.evaluate("(()=>{const p={name:'x',ex:["+E+"]};dayView={p:p,computed:false};return planOf(p.ex[0],p)})()")
    ok('обзор дня: 82,5 кг ↑ × 6',('82,5' in pl['w']) and pl['reps']==6,pl)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
