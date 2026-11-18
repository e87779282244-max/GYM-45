# Идеи из разбора IZIFit: запас повторов (RIR) влияет на двойную прогрессию, свой шаг веса тренажёра, обхваты слева/справа.
# Запуск: python3 tests/rir_step_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    S="[{w:40,r:12},{w:40,r:12},{w:40,r:12}]"
    r=await E(f"""[prSug(['Разгибание ног в тренажёре',3,'10–12',40],{{}},{{sets:{S}}}).w,
      prSug(['Разгибание ног в тренажёре',3,'10–12',40],{{}},{{sets:{S},rir:'2'}}).w,
      prSug(['Разгибание ног в тренажёре',3,'10–12',40],{{}},{{sets:{S},rir:'0'}}).w,
      prSug(['Разгибание ног в тренажёре',3,'10–12',40],{{}},{{sets:{S},rir:'3'}}).w,
      prSug(['Разгибание ног в тренажёре',3,'10–12',40],{{}},{{sets:{S},rir:'4+'}}).w]""")
    ok('RIR: без отметки и 2 → +5 · 0 → вес тот же · 3 и 4+ → +10',r==[[45]*3,[45]*3,None,[50]*3,[50]*3],r)
    r=await E(f"prSug(['Разгибание ног в тренажёре',3,'10–12',40],{{}},{{sets:{S},rir:'0'}}).why")
    ok('RIR 0 — объяснение «закрепи вес»','закрепи' in r,r)
    r=await E("prSug(['Разгибание ног в тренажёре',3,'10–12',40],{},{sets:[{w:40,r:11},{w:40,r:12},{w:40,r:12}],rir:'4+'}).w")
    ok('не все подходы на верх диапазона — запас не добавляет вес',r is None,r)
    # lastResult отдаёт запас последнего подхода
    r=await E("""(()=>{const h=safe.get();h.push({date:'2026-11-10',name:'Тест',log:{'Жим гантелей лёжа':[{w:20,r:10,done:true},{w:20,r:10,done:true,rir:'3'}]}});localStorage.setItem(KEY,JSON.stringify(h));return lastResult('Жим гантелей лёжа')})()""")
    ok('lastResult: запас последнего подхода',r and r['rir']=='3',r)
    # свой шаг веса
    r=await E("""(()=>{const a=[prInc(40,'Тяга верхнего блока'),wFit(41,'Тяга верхнего блока','up')];wStepSet('Тяга верхнего блока',2.5);
      a.push(prInc(40,'Тяга верхнего блока'),wFit(41,'Тяга верхнего блока','up'),prSug(['Тяга верхнего блока',3,'10–12',40],{},{sets:[{w:40,r:12},{w:40,r:12},{w:40,r:12}]}).w[0]);
      wStepSet('Жим штанги лёжа',5);a.push(wStepOv('Жим штанги лёжа'));wStepSet('Тяга верхнего блока',0);a.push(prInc(40,'Тяга верхнего блока'));return a})()""")
    ok('шаг тренажёра: авто 5 → свой 2,5 (41→42,5, прибавка 2,5) · штанге свой шаг не ставится · сброс → 5',r==[5,45,2.5,42.5,42.5,0,5],r)
    ok('шаг хранится в своём ключе и уходит в облако',await E("(()=>{wStepSet('Бабочка',7);const x=cloudSnapshot().wstep;return x&&x['Бабочка']===7&&localStorage.getItem('gym45_wstep_v1').includes('Бабочка')})()"))
    # обхваты: левая/правая
    await E("show('an');try{AN_UI.tab='body';}catch(e){};anBody()")
    r=await E("""(()=>{['arm','armR','neck'].forEach((k,i)=>el('anM_'+k).value=[40,39,41][i]);el('anW').value='95';el('anBSave').click();const b=anSt().body.find(x=>x.date===localDate());return [b.arm,b.armR,b.neck,b.w]})()""")
    ok('замер: бицепс Л 40 · П 39 · шея 41 сохранены',r==[40,39,41,95],r)
    t=await E("el('anBody').textContent")
    ok('карточка обхватов: левая/правая и разница сторон','Бицепс · правая' in t and 'левая − правая' in t and '+1' in t,t[-400:])
    # старая запись с одним бицепсом читается как левая, без ошибок
    await E("""(()=>{const s=anSt();s.body=[{date:'2026-10-01',w:96,arm:39.5}];anSave(s);anBody()})()""")
    t=await E("el('anBody').textContent")
    ok('старая запись «Бицепс» без правой — показывается как раньше','Бицепс' in t and 'правая' not in t,t[-300:])
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
