# В зале и прогресс: блины, рекорды, заметки, «позже/пропустить», мои программы, рекорды/журнал, итог месяца, фото, облако частями.
# Запуск: python3 tests/gym_tools_check.py index.html [папка_скриншотов]
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools,base64
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);O=sys.argv[2] if len(sys.argv)>2 else None;tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:print('CONSOLE',m.text[:300]) if m.type=='error' else None)
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';coolOffer=function(){}")
    # блины
    r=await pg.evaluate("[plCalc(87.5).t,plCalc(20).t,plCalc(61).t,plIsBar('Жим штанги лёжа'),plIsBar('Жим гантелей лёжа'),plIsBar('Приседания со штангой'),plIsBar('Жим ногами')]")
    ok('87,5 кг: 20 + 10 + 2,5 + 1,25',r[0].startswith('на сторону: 20 + 10 + 2,5 + 1,25'),r[0])
    ok('гриф / не собрать / штанга-гантели',r[1].startswith('только гриф') and 'не хватает' in r[2] and r[3] and not r[4] and r[5] and not r[6],r)
    hist="[{date:addDays(localDate(),-7),name:'A',vol:1,log:{'Жим штанги лёжа':[{w:80,r:8,done:true},{w:80,r:8,done:true}]}}]"
    await pg.evaluate(f"safe.set({hist});startWorkout({{name:'Т',focus:'т',sec:'body',ex:[['Жим штанги лёжа',3,'8',80],['Разведение гантелей лёжа',3,'12',14]]}},false);el('dayStart').click()");await pg.wait_for_timeout(200)
    await pg.evaluate("current.sets[0].forEach(s=>{s.w=87.5;s.r=8});renderWorkout()")
    ok('в карточке штанги — строка блинов',await pg.evaluate("!el('plLine').hidden&&el('plLine').textContent.includes('20 + 10 + 2,5 + 1,25')"))
    # рекорд
    await pg.evaluate("document.querySelectorAll('#exList .chk')[0].click()");await pg.wait_for_timeout(600)
    ok('рекорд веса отмечен 🏆',await pg.evaluate("current.sets[0][0].pr==='вес'"),await pg.evaluate("el('toast').textContent"))
    await pg.evaluate("el('wkRestSkip')&&el('wkRestSkip').click();current.sets[0][1].w=80;current.sets[0][1].r=10;renderWorkout();document.querySelectorAll('#exList .chk')[1].click()");await pg.wait_for_timeout(300)
    ok('рекорд повторов на прежнем весе',await pg.evaluate("current.sets[0][1].pr==='повторы'"))
    await pg.evaluate("el('wkRestSkip')&&el('wkRestSkip').click();current.sets[0][2].w=60;current.sets[0][2].r=8;renderWorkout();document.querySelectorAll('#exList .chk')[2].click()");await pg.wait_for_timeout(300)
    ok('обычный подход — без рекорда',await pg.evaluate("!current.sets[0][2].pr"))
    # заметка
    await pg.evaluate("el('wkRestSkip')&&el('wkRestSkip').click();goEx(0)");await pg.wait_for_timeout(100)
    await pg.evaluate("document.querySelector('.wk-note-btn').click()");await pg.fill('.wk-note-in','Хват шире')
    ok('заметка к упражнению в тренировке',await pg.evaluate("current.notes['Жим штанги лёжа']==='Хват шире'"))
    if O:await pg.screenshot(path=O+'/t_card.png',full_page=True)
    # пропустить второе
    await pg.evaluate("goEx(1)");await pg.wait_for_timeout(100)
    await pg.evaluate("document.querySelector('.wk-skip [data-a=skip]').click()");await pg.evaluate("document.querySelector('.wk-skip [data-a=skip]').click()");await pg.wait_for_timeout(300)
    ok('пропуск → тренировка завершена, окно с заметкой',await pg.evaluate("!el('gvtModal').hidden&&!!el('wkNoteAll')"))
    await pg.fill('#wkNoteAll','Спал 5 часов');await pg.evaluate("el('wkDoneGo').click()");await pg.wait_for_timeout(300)
    h=await pg.evaluate("safe.get().slice(-1)[0]")
    ok('в истории: заметки, пропуск, рекорд',h.get('note')=='Спал 5 часов' and h['notes']['Жим штанги лёжа']=='Хват шире' and h.get('skip')==['Разведение гантелей лёжа'],{k:h.get(k) for k in ['note','notes','skip']})
    ok('пропущенное не попало в «не закрыт план»','Разведение' not in (await pg.evaluate("window.__coachPending||el('coachText').textContent||''")))
    await pg.evaluate("startWorkout({name:'Т',focus:'т',sec:'body',ex:[['Жим штанги лёжа',3,'8',80]]},false);el('dayStart').click()");await pg.wait_for_timeout(150)
    ok('в следующий раз видна прошлая заметка',await pg.evaluate("document.querySelector('.wk-note-prev').textContent.includes('Хват шире')"))
    await pg.evaluate("clearDraft();current=null")
    # позже
    await pg.evaluate("startWorkout({name:'Т2',focus:'т',sec:'body',ex:[['Жим штанги лёжа',1,'8',80],['Тяга штанги в наклоне',1,'8',60],['Подъём штанги на бицепс',1,'10',30]]},false);el('dayStart').click()");await pg.wait_for_timeout(150)
    await pg.evaluate("document.querySelector('.wk-skip [data-a=later]').click()");await pg.wait_for_timeout(100)
    ok('«Сделать позже» → следующее',await pg.evaluate("current.idx===1"))
    await pg.evaluate("current.sets[1][0].w=60;current.sets[1][0].r=8;renderWorkout();document.querySelectorAll('#exList .chk')[0].click()");await pg.wait_for_timeout(200)
    nx=await pg.evaluate("nextUndone(1)")
    ok('отложенное — в конце очереди',nx==2,nx)
    await pg.evaluate("clearDraft();current=null")
    # мои программы
    await pg.evaluate("show('programs');el('myOpen').click()");await pg.wait_for_timeout(150)
    await pg.evaluate("el('myNew').click()");await pg.wait_for_timeout(100)
    await pg.fill('#myName','Мой верх/низ');await pg.fill('.my-ex .my-n','Жим штанги лёжа')
    await pg.evaluate("document.querySelector('[data-x=aex]').click()");await pg.fill('.my-ex[data-xi=\"1\"] .my-n','Подтягивания')
    await pg.evaluate("document.querySelector('.my-ex[data-xi=\"1\"] [data-f=bw]').click()")
    await pg.evaluate("el('myAddDay').click()");await pg.fill('.my-day[data-di=\"1\"] .my-n','Приседания со штангой')
    if O:await pg.screenshot(path=O+'/t_my_ed.png',full_page=True)
    await pg.evaluate("el('mySaveB').click()");await pg.wait_for_timeout(150)
    v=await pg.evaluate("myStore()")
    ok('программа сохранена и активна',len(v['progs'])==1 and v['act']==v['progs'][0]['id'] and len(v['progs'][0]['days'])==2 and v['progs'][0]['days'][0]['ex'][1]['bw']==1,v)
    ok('в «Сегодня»',await pg.evaluate("mpList().some(x=>x.k==='my')"))
    if O:await pg.screenshot(path=O+'/t_my.png',full_page=True)
    await pg.evaluate("document.querySelector('.my-p [data-d=\"0\"]').click()");await pg.wait_for_timeout(150)
    w=await pg.evaluate("dayView.p.ex.map(e=>[e[0],e[1],e[2],e[3]])")
    ok('день программы открывается',w[0][0]=='Жим штанги лёжа' and w[1][3]==0,w)
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(100)
    ok('вес подставлен из истории',await pg.evaluate("current.sets[0][0].w>=80"),await pg.evaluate("current.sets[0].map(s=>s.w)"))
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>{s.done=true;if(!s.r)s.r=8}));finishWorkout()");await pg.wait_for_timeout(200)
    ok('следующий день программы — Б',await pg.evaluate("myNextDay(myList()[0])===1&&safe.get().slice(-1)[0].my.d===0"))
    # прогресс: рекорды, журнал, итог месяца
    await pg.evaluate("AN_UI.tab='pr';show('progress')");await pg.wait_for_timeout(200)
    ok('вкладка «Рекорды»',await pg.evaluate("!el('anPr').hidden&&el('anPr').textContent.includes('Жим штанги лёжа')&&el('anPr').textContent.includes('87,5 кг')"),await pg.evaluate("[el('anPr').hidden,el('anPr').textContent.slice(0,200)]"))
    if O:await pg.screenshot(path=O+'/t_pr.png',full_page=True)
    await pg.evaluate("document.querySelector('#anSub [data-v=log]').click()");await pg.wait_for_timeout(150)
    ok('вкладка «Журнал» с заметками',await pg.evaluate("!el('anLog').hidden&&el('anLog').textContent.includes('Спал 5 часов')&&el('anLog').textContent.includes('Хват шире')"))
    await pg.evaluate("document.querySelector('#anSub [data-v=load]').click()");await pg.wait_for_timeout(150)
    await pg.evaluate("el('mcGo').click()");await pg.wait_for_timeout(300)
    ok('итог месяца — картинка',await pg.evaluate("!el('coolModal').hidden&&document.querySelector('.mc-img').src.startsWith('data:image/png')"))
    if O:
      d=await pg.evaluate("document.querySelector('.mc-img').src");open(O+'/t_month.png','wb').write(base64.b64decode(d.split(',')[1]))
    await pg.evaluate("el('mcX').click()")
    # фото (без Claude — на устройстве)
    await pg.evaluate("document.querySelector('#anTabs [data-v=body]').click()");await pg.wait_for_timeout(200)
    png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAIAAAADCAIAAAA2iEnWAAAAFUlEQVR4nGP4z8DAwMDAxMDAwMAAABUAAf4kG6sAAAAASUVORK5CYII=')
    open(tmp+'/p.png','wb').write(png)
    await pg.set_input_files('#phFile',tmp+'/p.png');await pg.wait_for_timeout(800)
    await pg.evaluate("el('phDate').value='2026-11-30'");await pg.set_input_files('#phFile',tmp+'/p.png');await pg.wait_for_timeout(800)
    ok('два фото — сравнение рядом',await pg.evaluate("phList().length===2&&document.querySelectorAll('#phCmp figure img').length===2"))
    ok('фото в облачном снимке (только список)',await pg.evaluate("cloudSnapshot().photos.length===2&&!JSON.stringify(cloudSnapshot().photos).includes('data:')"))
    if O:await pg.screenshot(path=O+'/t_photo.png',full_page=True)
    # облако по частям
    r=await pg.evaluate("""(async()=>{const M={};const db={doc:p=>({get:async()=>({exists:p in M,data:()=>M[p]}),set:async d=>{M[p]=JSON.parse(JSON.stringify(d))},delete:async()=>{delete M[p]}})};
      const S=claudeStore(db,'u');const big={history:Array.from({length:3000},(_,i)=>({date:'2026-10-01',name:'Тренировка '+i,log:{'Жим':[{w:80,r:8}]}}))};
      await S.doc().set(big);const n=M['data/users/u/appdata'].__ch.n;const g=await S.doc().get();const ok1=g.data().history.length===3000;
      await S.doc().set({history:[]});const left=Object.keys(M).filter(k=>k.includes('_c')).length;const g2=await S.doc().get();return [n,ok1,left,g2.data().history.length];})()""")
    ok('облако Claude: большой снимок пишется частями и читается',r[0]>1 and r[1] and r[2]==0 and r[3]==0,r)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
