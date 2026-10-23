# Авторские программы бодибилдинга: порядок, недели, дни, запуск тренировки, подсказки, отдых, анимации.
# Запуск: python3 tests/authored_check.py index.html [папка_скриншотов]
import asyncio,json,os,sys,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
HTML=os.path.abspath(sys.argv[1]);SHOT=sys.argv[2] if len(sys.argv)>2 else None
tmp=tempfile.mkdtemp();shutil.copy(HTML,tmp+'/index.html')
if os.path.isdir(os.path.dirname(HTML)+'/media'):os.symlink(os.path.dirname(HTML)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';show('body')");await pg.wait_for_timeout(200)
    order=await pg.evaluate("[...el('bodyProgs').children].map(x=>x.classList.contains('bb-lbl')?'#'+x.firstChild.textContent:x.querySelector('span span').textContent)")
    exp=['German Volume Training','#Авторские программы','Y3T · Нил Хилл','Fortitude Training · Скотт Стивенсон','FST-7 · Хэни Рэмбод','DC Training · Данте Трудель','Creeping Death II · Джон Медоуз','Blood & Guts · Дориан Ятс','#Базовые программы']
    ok('порядок: GVT → 6 авторских по сложности → базовые',order[:9]==exp and len(order)==14,order[:9])
    ok('индикатор сложности 1…6',await pg.evaluate("[...el('bodyProgs').querySelectorAll('.lvl-dots')].map(d=>d.querySelectorAll('i.on').length).join()==='1,2,3,4,5,6'"))
    if SHOT:await pg.evaluate("el('bodyProgs').scrollIntoView()");await pg.screenshot(path=SHOT+'/au-list.png')
    info=json.loads(await pg.evaluate("JSON.stringify(AUTH.map(p=>({id:p.id,w:p.weeks.length,d:p.weeks.map(w=>w.days.length)})))"))
    ok('недели и дни: Y3T 3×4, Fortitude 2×4, FST-7 6×5, DC 6+2, CD2 3×5, B&G 2×4',[ (x['w'],x['d']) for x in info]==[(3,[4,4,4]),(2,[4,4]),(6,[5]*6),(2,[6,2]),(3,[5,5,5]),(2,[4,4])],info)
    # каждый день каждой программы открывается и стартует
    bad=[]
    for pi,x in enumerate(info):
      for wi,nd in enumerate(x['d']):
        for di in range(nd):
          r=await pg.evaluate(f"""(()=>{{const p=AUTH[{pi}];authSetWeek(p,{wi});authOpen(p);const bt=el('bodyDays').querySelectorAll('.disc')[{di}];bt.click();
            if(currentScreen!=='day')return 'no day';current=null;el('dayStart').click();if(currentScreen!=='workout'||!current)return 'no workout';
            const n=current.program.ex.length,ok=current.sets.every((s,i)=>s.length===current.program.ex[i][1]||s.length===rScaleSets(current.program.ex[i][1]));clearDraft();current=null;return ok?'':'sets'}})()""")
          if r:bad.append((x['id'],wi,di,r))
    ok('все 81 тренировка запускается, подходы совпадают с программой',not bad,bad[:5])
    await pg.evaluate("authSetWeek(AUTH[2],3);authOpen(AUTH[2])");await pg.wait_for_timeout(60)
    ok('выбранная неделя запоминается',await pg.evaluate("authWeek(AUTH[2])===3&&el('auWk').querySelectorAll('.on')[0].dataset.v==='3'"))
    if SHOT:await pg.screenshot(path=SHOT+'/au-prog.png')
    # FST-7: подсказка, отдых финиша, отдельная память веса, анимация по базовому названию
    await pg.evaluate("el('bodyDays').querySelectorAll('.disc')[3].click()");await pg.wait_for_timeout(60)
    ok('обзор дня: подсказки к упражнениям',await pg.evaluate("el('dayList').innerText.includes('отдых 30–45 с')"))
    if SHOT:await pg.screenshot(path=SHOT+'/au-day.png')
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(80)
    await pg.evaluate("current.idx=3;renderWorkout()");await pg.wait_for_timeout(60)
    ok('тренировка: подсказка под упражнением',await pg.evaluate("!!el('exList').querySelector('.ex-note')&&el('exList').querySelector('.ex-note').innerText.includes('7 подх.')"))
    ok('отдых на финише FST-7 — 40 с, в базе — 150 с',await pg.evaluate("(()=>{const a=restDefault();current.idx=0;const b=restDefault();current.idx=3;return a===40&&b===150})()"))
    ok('анимация финиша по базовому упражнению',await pg.evaluate("!!MEDIA['Разведение гантелей в стороны · FST-7']"))
    if SHOT:await pg.screenshot(path=SHOT+'/au-workout.png')
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));finishWorkout()");await pg.wait_for_timeout(150)
    last=json.loads(await pg.evaluate("JSON.stringify(safe.get().slice(-1)[0])"))
    ok('завершение: запись в историю, раздел «бодибилдинг»',last.get('sec')=='body' and 'Разведение гантелей в стороны · FST-7' in last.get('log',{}),last.get('name'))
    ok('память весов: финиш FST-7 не путается с базовым упражнением',await pg.evaluate("lastResult('Разведение гантелей в стороны')===null&&!!lastResult('Разведение гантелей в стороны · FST-7')"))
    ok('без горизонтальной прокрутки',await pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f'\n{sum(R)}/{len(R)} PASS');sys.exit(0 if all(R) else 1)
asyncio.run(m())
