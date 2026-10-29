# Пауэрлифтинг: «Тяжёлая артиллерия» (Conjugate) — 4 дня, ротация вариантов, рекорды по вариантам,
# скоростные волны от 1ПМ, смена подсобки через 3 недели, 6-недельный круг, облако.
# Запуск: python3 tests/cj_check.py index.html [папка_скриншотов]
import asyncio,os,sys,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
HTML=os.path.abspath(sys.argv[1]);SHOT=sys.argv[2] if len(sys.argv)>2 else None
tmp=tempfile.mkdtemp();shutil.copy(HTML,tmp+'/index.html')
if os.path.isdir(os.path.dirname(HTML)+'/media'):os.symlink(os.path.dirname(HTML)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
RUN="startWorkout(cjPlan(cjActive(),cjState(cjActive())),true);el('dayStart').click();current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));finishWorkout()"
PL="(()=>{const P=cjActive(),p=cjPlan(P,cjState(P));return p.ex.map(e=>e[0]+'|'+e[1]+'×'+e[2]+'|'+e[3])})()"
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    await pg.evaluate("document.querySelector('.disc[data-disc=\"Пауэрлифтинг\"]').click()");await pg.wait_for_timeout(100)
    ok('в «Пауэрлифтинге» — «Тяжёлая артиллерия», 5 звёзд',await pg.evaluate("(()=>{const b=[...el('pwrPrograms').querySelectorAll('.disc')].find(b=>b.textContent.includes('Тяжёлая артиллерия'));return b&&b.querySelectorAll('.lvl-dots i.on').length===5})()"))
    await pg.evaluate("[...el('pwrPrograms').querySelectorAll('.disc')].find(b=>b.textContent.includes('Тяжёлая артиллерия')).click()");await pg.wait_for_timeout(100)
    await pg.evaluate("el('cjRm_sq').value='200';el('cjRm_bp').value='140';el('cjRm_dl').value='240';el('cjGo').click()");await pg.wait_for_timeout(100)
    if SHOT:await pg.screenshot(path=SHOT+'/cj.png',full_page=True)
    pl=await pg.evaluate(PL)
    ok('Пн неделя 1: присед узкой стойкой, ориентир 190 (95 %), + 4 подсобки',pl[0]=='Присед узкой стойкой ниже параллели|2×1|190' and len(pl)==5,pl)
    await pg.evaluate(RUN);await pg.wait_for_timeout(150)
    ok('после Пн — экран программы, рекорд варианта записан (192,5)',await pg.evaluate("currentScreen==='cj'&&cjPRs()['Присед узкой стойкой ниже параллели|1'].w===192.5"))
    pl=await pg.evaluate(PL)
    ok('Ср: жим с двух досок, ориентир 147,5',pl[0]=='Жим лёжа с двух досок|2×1|147.5',pl)
    await pg.evaluate(RUN);await pg.wait_for_timeout(150)
    pl=await pg.evaluate(PL)
    ok('Пт: бокс-присед 12×2 на 75 % (150), становая 8×1 на 60 % (145)',pl[0]=='Бокс-присед широкой стойкой ниже параллели|12×2|150' and pl[1]=='Становая тяга — скоростные одиночные|8×1|145',pl)
    await pg.evaluate(RUN);await pg.wait_for_timeout(150)
    pl=await pg.evaluate(PL)
    ok('Сб: скоростной жим 9×3 на 50 % (70)',pl[0]=='Жим лёжа узким хватом — скоростной|9×3|70',pl)
    await pg.evaluate(RUN);await pg.wait_for_timeout(150)
    pl=await pg.evaluate(PL)
    ok('неделя 2: новый вариант — тяга с плинтов (264 = 110 % становой)',await pg.evaluate("cjState(cjActive()).week")==2 and pl[0]=='Тяга с плинтов на уровне колен|2×1|265',pl)
    # прогон до недели 3 пятницы → 85 %, до недели 4 → смена подсобки
    for _ in range(4):await pg.evaluate(RUN);await pg.wait_for_timeout(80)
    await pg.evaluate(RUN+";");await pg.wait_for_timeout(80);await pg.evaluate(RUN);await pg.wait_for_timeout(80)
    st=await pg.evaluate("(()=>{const s=cjState(cjActive());return [s.week,s.next]})()")
    pl=await pg.evaluate(PL)
    ok('неделя 3, Пт: волна 85 % — 10×2 по 170',st==[3,'del'] and pl[0]=='Бокс-присед широкой стойкой ниже параллели|10×2|170',[st,pl[:1]])
    acc1=await pg.evaluate("cjPlan(cjActive(),cjState(cjActive()),'mel').ex.slice(1).map(e=>e[0])")
    await pg.evaluate("(()=>{const v=cjStore(),P=cjActive(v);for(let i=0;i<2;i++)P.recs.push({uid:'z'+i,kind:'x',finishedAt:'2099-01-0'+(i+1)+'T00:00:00Z'});cjSave(v);})()")
    acc2=await pg.evaluate("cjPlan(cjActive(),cjState(cjActive()),'mel').ex.slice(1).map(e=>e[0])")
    ok('неделя 4: новый скоростной вариант и смена подсобки',await pg.evaluate("cjState(cjActive()).week")==4 and acc1!=acc2,[acc1,acc2])
    # круг 2 — другие варианты; рекорд повторного варианта
    await pg.evaluate("(()=>{const v=cjStore(),P=cjActive(v);while(P.recs.length<24)P.recs.push({uid:'y'+P.recs.length,kind:'x',finishedAt:'2099-02-'+String(10+P.recs.length).padStart(2,'0')+'T00:00:00Z'});cjSave(v);})()")
    ok('круг 2, неделя 1: другой набор вариантов',await pg.evaluate("(()=>{const s=cjState(cjActive());return s.cycle===2&&s.week===1&&cjPlan(cjActive(),s,'mel').ex[0][0]==='Становая тяга с плинтов ниже колен'})()"))
    ok('история: тренировки в разделе pwr',await pg.evaluate("safe.get().filter(h=>/Тяжёлая артиллерия/.test(h.name)).length>=10"))
    ok('главная и «Активные программы»',await pg.evaluate("(()=>{const x=mpList().find(x=>x.k==='cj');return x&&weekPlanOf(x)===4&&dashNextName(x).includes('Тяжёлая артиллерия')})()"))
    ok('облако: снимок и слияние',await pg.evaluate("(()=>{const s=cloudSnapshot();return s.cj.progs.length===1&&mergeCj({progs:[],activeId:null},s.cj).progs.length===1})()"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
