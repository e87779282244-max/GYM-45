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
    order=await pg.evaluate("[...el('bodyProgs').children].map(x=>x.classList.contains('bb-lbl')?'#'+x.firstChild.textContent:x.classList.contains('au-by')?'@'+x.textContent:x.querySelector('span span').textContent)")
    exp=['German Volume Training','#С чего начать','Фулбади для новичков','#Авторские программы','@Пол Картер · 2 программы','Фулбади 3 дня','Верх / низ с ротацией','@Джон Медоуз','Warlock','@Крис Бамстед','Push / Pull / Legs','@Нил Хилл','Y3T','@Джефф Ниппард','Bodybuilding Transformation System','@Джордан Питерс','Completely Massive','@Джей Катлер','Mass-Ter Plan','@Джим Стоппани',"HIIT 100's",'@Скотт Стивенсон','Fortitude Training','@Хэни Рэмбод','FST-7: Big and Ripped','@Данте Трудель','DC Training','@Майк Ментцер','Heavy Duty','@Дориан Ятс','Blood & Guts','#Базовые программы']
    await pg.evaluate("[...el('bodyProgs').querySelectorAll('.disc')].find(b=>b.textContent.includes('Фулбади для новичков')).click()");await pg.wait_for_timeout(150)
    ok('новичок → кнопка «Следующий шаг: Картер»',await pg.evaluate("!!el('bodyDays').querySelector('.next-step')&&el('bodyDays').querySelector('.next-step').textContent.includes('Пол Картер')"))
    if SHOT:await pg.screenshot(path=SHOT+'/next_step.png',full_page=True)
    await pg.evaluate("el('bodyDays').querySelector('.next-step').click()");await pg.wait_for_timeout(150)
    ok('переход открывает фулбади Картера',await pg.evaluate("el('bodyName').textContent.includes('Фулбади 3 дня')&&!!el('auWk')"))
    ok('порядок: GVT → авторские блоками по авторам (внутри — по сложности) → базовые',order[:len(exp)]==exp,order[:len(exp)])
    ok('сложность 1…5 у каждой программы',await pg.evaluate("[...el('bodyProgs').querySelectorAll('.lvl-dots')].every(d=>d.querySelectorAll('i').length===5)&&AUTH.every(p=>p.lvl>=1&&p.lvl<=5)"))
    ok('внутри блока автора сложность не убывает',await pg.evaluate("AUTH.every((p,i)=>i===0||AUTH[i-1].by!==p.by||AUTH[i-1].lvl<=p.lvl)"))
    if SHOT:await pg.evaluate("el('bodyProgs').scrollIntoView()");await pg.screenshot(path=SHOT+'/au-list.png')
    info=json.loads(await pg.evaluate("JSON.stringify(AUTH.map(p=>({id:p.id,w:p.weeks.length,d:p.weeks.map(w=>w.days.length)})))"))
    want={'pcfb':(5,[3]*5),'pcul':(4,[6]*4),'wl':(3,[4,4,4]),'cbum':(1,[6]),'y3t':(4,[5,5,5,5]),'bts':(6,[5]*6),'jpcm':(2,[5,4]),'jc':(6,[6]*6),'ft':(8,[8]*6+[2,2]),'hiit':(6,[6]*6),'fst7':(8,[5]*4+[6]*4),'dc':(2,[6,2]),'hd':(2,[3,3]),'bg':(2,[4,4])}
    ok('недели и дни всех 14 программ',{x['id']:(x['w'],x['d']) for x in info}==want,[x['id'] for x in info])
    # каждый день каждой программы открывается и стартует
    bad=[]
    for pi,x in enumerate(info):
      for wi,nd in enumerate(x['d']):
        for di in range(nd):
          r=await pg.evaluate(f"""(()=>{{const p=AUTH[{pi}];authSetWeek(p,{wi});authOpen(p);const bt=el('bodyDays').querySelectorAll('.disc')[{di}];bt.click();
            if(currentScreen!=='day')return 'no day';current=null;el('dayStart').click();if(currentScreen!=='workout'||!current)return 'no workout';
            const n=current.program.ex.length,ok=current.sets.every((s,i)=>s.length===current.program.ex[i][1]||s.length===rScaleSets(current.program.ex[i][1]));clearDraft();current=null;return ok?'':'sets'}})()""")
          if r:bad.append((x['id'],wi,di,r))
    ok(f'все {sum(sum(x["d"]) for x in info)} тренировок запускаются, подходы совпадают с программой',not bad,bad[:5])
    await pg.evaluate("authSetWeek(AUTH.find(p=>p.id==='fst7'),3);authOpen(AUTH.find(p=>p.id==='fst7'))");await pg.wait_for_timeout(60)
    ok('выбранная неделя запоминается',await pg.evaluate("authWeek(AUTH.find(p=>p.id==='fst7'))===3&&el('auWk').querySelectorAll('.on')[0].dataset.v==='3'"))
    if SHOT:await pg.screenshot(path=SHOT+'/au-prog.png')
    # FST-7: подсказка, отдых финиша, отдельная память веса, анимация по базовому названию
    await pg.evaluate("el('bodyDays').querySelectorAll('.disc')[3].click()");await pg.wait_for_timeout(60)
    ok('обзор дня: подсказки к упражнениям',await pg.evaluate("el('dayList').innerText.includes('отдых 30–45 с')"))
    if SHOT:await pg.screenshot(path=SHOT+'/au-day.png')
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(80)
    await pg.evaluate("current.idx=3;renderWorkout()");await pg.wait_for_timeout(60)
    ok('тренировка: подсказка под упражнением',await pg.evaluate("!!el('exList').querySelector('.ex-note')&&el('exList').querySelector('.ex-note').innerText.includes('7 подх.')"))
    ok('отдых на финише FST-7 — 40 с, в базе — 120 с',await pg.evaluate("(()=>{const a=restDefault();current.idx=0;const b=restDefault();current.idx=3;return a===40&&b===120})()"))
    ok('анимация FST-7 по базовому упражнению',await pg.evaluate("!!MEDIA['Шраги в Смите · FST-7']||!!MEDIA['Разведение гантелей в стороны · FST-7']"))
    if SHOT:await pg.screenshot(path=SHOT+'/au-workout.png')
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));finishWorkout()");await pg.wait_for_timeout(150)
    last=json.loads(await pg.evaluate("JSON.stringify(safe.get().slice(-1)[0])"))
    ok('завершение: запись в историю, раздел «бодибилдинг»',last.get('sec')=='body' and 'Махи в стороны в тренажёре · FST-7' in last.get('log',{}),last.get('name'))
    ok('память весов: финиш FST-7 не путается с базовым упражнением',await pg.evaluate("lastResult('Махи в стороны в тренажёре')===null&&!!lastResult('Махи в стороны в тренажёре · FST-7')"))
    adup=await pg.evaluate("AUTH.flatMap(p=>p.weeks.flatMap(w=>w.days.filter(d=>new Set(d.ex.map(e=>e[0])).size!==d.ex.length).map(d=>p.id+': '+d.name)))")
    ok('во всех программах в одном дне нет повторяющихся названий',not adup,adup[:3])
    # Warlock: структура по программе
    wl=json.loads(await pg.evaluate("JSON.stringify(AUTH.find(p=>p.id==='wl').weeks.map(w=>w.days.map(d=>({n:d.name,ex:d.ex.map(e=>[e[0],e[1],e[2],e[6]])}))))"))
    ok('Warlock: 2 блока по 4 тренировки + разгрузка, верх/низ/верх/низ',[len(w) for w in wl]==[4,4,4] and all(['Верх' in w[0]['n'],'Низ' in w[1]['n'],'Верх' in w[2]['n'],'Низ' in w[3]['n']]==[True]*4 for w in wl))
    ok('Warlock: блоки с разными упражнениями, 10/6/10/6 упражнений',[len(d['ex']) for d in wl[0]]==[10,6,10,6] and wl[0][0]['ex'][0][0]!=wl[1][0]['ex'][0][0])
    ok('Warlock: отдых — база 3 мин, изоляция 1 мин',wl[0][0]['ex'][0][3]==180 and wl[0][0]['ex'][6][3]==60)
    dl=sum(e[1] for d in wl[2] for e in d['ex']);b2=sum(e[1] for d in wl[1] for e in d['ex'])
    ok('Warlock: разгрузка ≈ −20 % подходов',0.75*b2<=dl<=0.85*b2,(dl,b2))
    wdup=[d['n'] for w in wl for d in w if len({e[0] for e in d['ex']})!=len(d['ex'])]
    ok('Warlock: в дне нет повторяющихся упражнений',not wdup,wdup)
    # Fortitude: структура по книге
    ft=json.loads(await pg.evaluate("JSON.stringify(AUTH.find(p=>p.id==='ft').weeks.map(w=>({n:w.name,d:w.days.map(d=>({n:d.name,ex:d.ex.map(e=>[e[0],e[1],e[2],e[6]])}))})))"))
    dup=[(w['n'],d['n']) for w in ft for d in w['d'] if len({e[0] for e in d['ex']})!=len(d['ex'])]
    ok('Fortitude: в дне нет повторяющихся упражнений (журнал не склеивается)',not dup,dup[:3])
    mr=[e for w in ft for d in w['d'] for e in d['ex'] if e[0].endswith(' · раунд')]
    ok('Fortitude: мышечный раунд — 6×4, отдых 10 с',mr and all(e[1]==6 and e[2]==4 and e[3]==10 for e in mr),len(mr))
    fb=ft[0]['d']
    ok('Fortitude: день 3 — раунды низа, день 4 — верха; дни 1–2 в группах A/B/C',fb[6]['n'].startswith('День 3') and 'Жим ногами · раунд' in [e[0] for e in fb[6]['ex']] and 'Тяга верхнего блока · раунд' in [e[0] for e in fb[7]['ex']] and [d['n'][:10] for d in fb[:6]]==['День 1 · A','День 1 · B','День 1 · C','День 2 · A','День 2 · B','День 2 · C'])
    sets=lambda w,i:sum(e[1] for e in ft[w]['d'][i]['ex'])
    ok('Fortitude: объём растёт Tier I → II → III',sets(0,0)<sets(1,0)<sets(2,0) and sets(0,7)<sets(1,7)<sets(2,7),[sets(i,0) for i in range(3)])
    ok('Fortitude: разгрузка — только мышечные раунды (дни 3 и 4)',all('раунды' in d['n'] for d in ft[6]['d']+ft[7]['d']))
    if SHOT:
      await pg.evaluate("authSetWeek(AUTH.find(p=>p.id==='ft'),0);authOpen(AUTH.find(p=>p.id==='ft'))");await pg.wait_for_timeout(80);await pg.screenshot(path=SHOT+'/ft-prog.png')
      await pg.evaluate("el('bodyDays').querySelectorAll('.disc')[6].click()");await pg.wait_for_timeout(80);await pg.screenshot(path=SHOT+'/ft-day3.png')
    ok('без горизонтальной прокрутки',await pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f'\n{sum(R)}/{len(R)} PASS');sys.exit(0 if all(R) else 1)
asyncio.run(m())
