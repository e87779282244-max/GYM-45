# Шаг веса по снаряду во всех программах + подсказка стартовых весов этапа GVT 2.0.
# Штанга — собираемый из грифа и блинов калькулятора вес; гантели +2; доп. вес +2,5; тренажёры +5.
# Подсказка этапа: лучший результат упражнения за программу (или 1ПМ из «Рабочих весов»), вниз, без автосохранения.
# Запуск: python3 tests/weight_step_check.py index.html
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
    E=pg.evaluate

    # ---- штанга по блинам (гриф 20, блины 20…1,25)
    r=await E("[wBar(63,'up'),wBar(63,'down'),wBar(61.25,'near'),wBar(61.3,'near'),wBar(15,'down'),wBar(62.5,'up')]")
    ok('штанга: 63 → вверх 65 / вниз 62,5; 61,25 → 60 (равенство — вниз); меньше грифа → 20',r==[65,62.5,60,62.5,20,62.5],r)
    r=await E("(()=>{localStorage.setItem('gym45_plates_v1',JSON.stringify({bar:20,plates:[20,15,10,5,2.5,1.25,0.5]}));const x=[wBar(61.3,'near'),wBar(63,'down')];localStorage.removeItem('gym45_plates_v1');return x})()")
    ok('с блином 0,5 кг — точнее: 61,3 → 61 (по 0,5 на сторону); 63 вниз → 62,5 (маленьких блинов не больше двух одного вида)',r==[61,62.5],r)
    r=await E("[wSnap(13,'db','up'),wSnap(13,'db','down'),wSnap(11.3,'bw','near'),wSnap(42,'mach','up'),wSnap(42,'mach','down')]")
    ok('гантели 2 · доп. вес 2,5 · тренажёр 5',r==[14,12,12.5,45,40],r)
    r=await E("[wKind('Жим штанги лёжа'),wKind('Жим гантелей лёжа'),wKind('Подтягивания с весом'),wKind('Сгибание ног лёжа в тренажёре'),wKind('Тяга верхнего блока')]")
    ok('тип снаряда по названию',r==['bar','db','bw','mach','mach'],r)

    # ---- обычные программы: прибавка по снаряду
    r=await E("""[prSug(['Жим штанги лёжа',3,'8–10',60],{},{sets:[{w:60,r:10},{w:60,r:10},{w:60,r:10}]}).w,
      prSug(['Разгибание ног в тренажёре',3,'10–12',40],{},{sets:[{w:40,r:12},{w:40,r:12},{w:40,r:12}]}).w,
      prSug(['Жим гантелей лёжа',3,'8–10',20],{},{sets:[{w:20,r:10},{w:20,r:10},{w:20,r:10}]}).w]""")
    ok('обычная программа: штанга +2,5 · тренажёр +5 · гантели +2',r==[[62.5]*3,[45]*3,[22]*3],r)

    # ---- ТХ: жимы назначаются собираемым весом
    r=await E("""(()=>{const P={id:"t",cfg:{days:3,mode:"std",t:{sq:100,bp:61.25,pr:41.25,dl:120,pc:60},pc:"pc"},recs:[]};const st=txState(P);
      const pl=txPlan(P,st,st.next);const ws=[];pl.preset.forEach((ss,i)=>ss.forEach(s=>{if(s.w>0)ws.push(s.w);}));return ws.filter(w=>Math.abs(((w-20)/2)/1.25-Math.round(((w-20)/2)/1.25))>1e-6)})()""")
    ok('ТХ: все веса на штанге собираются из блинов',r==[],r)

    # ---- GVT 1: проценты → шаг снаряда
    r=await E("""(()=>{return [gvtRoundEx(61.6,'down',GVT_EX.B1),gvtRoundEx(61.6,'up',GVT_EX.B1),gvtRoundEx(41.2,'down',GVT_EX.B2),gvtRoundEx(23.1,'up',GVT_EX.A1)]})()""")
    ok('GVT 1: присед 61,6 → 60 / 62,5 · тренажёр 41,2 → 40 · гантели 23,1 → 24',r==[60,62.5,40,24],r)

    # ---- GVT 2.0: шаг программы и прибавка
    r=await E("""(()=>{const P=g2New({bw:90});return [P.stepM,g2DefStep(P,'bench'),g2DefStep(P,'lcurl'),g2DefStep(P,'dDecl'),g2DefStep(P,'dips'),g2FromLoad(P,'bench',63),g2FromLoad(P,'lcurl',42)]})()""")
    ok('GVT 2.0: тренажёр 5 · штанга по блинам · гантели 2 · доп. вес 2,5; 63 → 65, 42 → 45',r==[5,0,5,2,2.5,65,45],r)

    # ---- подсказка стартовых весов: этап I → этап II
    await E("""(()=>{localStorage.removeItem(G2K);localStorage.setItem(RMK,JSON.stringify({"Жим лёжа":100}));const v=g2Store();const P=g2New({stage:0,bw:90});P.st[0].setup=true;
      const sets=(w,n,r)=>Array.from({length:n},()=>({w:w,r:r,done:true}));
      P.recs.push({uid:"a",kind:"train",stage:0,date:"2026-10-20",ex:[{key:"dDecl",main:true,sets:sets(24,10,10)},{key:"pull",main:true,sets:sets(5,10,10)},{key:"squat",main:true,sets:sets(80,10,10)},{key:"lcurl",main:true,sets:sets(40,10,10)}],dec:[]});
      P.recs.push({uid:"b",kind:"train",stage:0,date:"2026-10-24",ex:[{key:"squat",main:true,sets:sets(82.5,10,8)}],dec:[]});
      P.st[0].status="done";P.stage=1;P.st[1].status="active";v.progs.push(P);v.activeId=P.id;g2Save(v);show("gvt");g2Render();})()""")
    r=await E("""(()=>{const g=k=>{const i=el('g2w_'+k);return i?i.value:null};return {dDecl:g('dDecl'),pull:g('pull'),squat:g('squat'),lcurl:g('lcurl'),dips:g('dips'),hammer:g('hammer'),txt:el('gvtBody').textContent}})()""")
    # жим гантелей 24×10 → 1ПМ 32 → под 8 повт. 25,26 → вниз по 2 → 24; присед лучший 80×10=106,67 vs 82,5×8=104,5 → 106,67/1,2667=84,2 → 82,5;
    # подтягивания (90+5)×10/3+… = 126,67 → /1,2667 = 100 → доп. 10; сгибание ног 40×10 → 53,33 → 42,1 → тренажёр вниз → 40
    ok('этап II: жим гантелей 24 · присед 82,5 · подтягивания доп. 10 · сгибание ног 40',[r['dDecl'],r['squat'],r['pull'],r['lcurl']]==['24','82.5','10','40'],r)
    ok('без истории — пусто (брусья, молотки)',r['dips']=='' and r['hammer']=='',[r['dips'],r['hammer']])
    ok('показан источник: этап, вес × повторы, дата','Из этапа I: 80 кг × 10 · 20.10' in r['txt'],r['txt'][:400])
    ok('ничего не сохранено до кнопки',await E("!g2Active().st[1].setup&&!g2Active().st[1].ws.squat"))
    await E("el('g2w_dips').value='0';el('g2w_hammer').value='12';el('g2SetGo').click()")
    ok('после «Сохранить» веса записаны',await E("(()=>{const w=g2Active().st[1].ws;return g2Active().st[1].setup&&w.squat.w===82.5&&w.dDecl.w===24&&w.pull.w===10})()"))
    # 1ПМ из «Рабочих весов», когда истории нет: этап V, жим лёжа (bench) 100 → 10ПМ 75
    r=await E("""(()=>{const v=g2Store(),P=v.progs[0];P.st[1].status="done";P.st[2].status="skip";P.st[3].status="skip";P.stage=4;P.st[4].status="active";g2Save(v);g2Render();
      return {w:el('g2w_bench')&&el('g2w_bench').value,txt:el('gvtBody').textContent.includes('Из 1ПМ «Жим лёжа»: 100 кг')}})()""")
    ok('нет истории — из 1ПМ «Рабочих весов»: жим 100 → 75',r['w']=='75' and r['txt'],r)
    # без массы тела — подсказки для подтягиваний нет, есть напоминание
    r=await E("""(()=>{const v=g2Store(),P=v.progs[0];P.bw=0;g2Save(v);const s=g2Suggest(P,4,'pull');return s&&s.w===null&&/массу тела/.test(s.txt)})()""")
    ok('подтягивания без массы тела — напоминание вместо веса',r)
    # повторная настройка: введённое значение не перезаписывается
    r=await E("""(()=>{const v=g2Store(),P=v.progs[0];P.st[4].ws.squat={ptr:1,plan:{1:70},W0:70};g2Save(v);g2Render();return el('g2w_squat').value})()""")
    ok('уже введённый вес не перезаписывается',r=='70',r)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
