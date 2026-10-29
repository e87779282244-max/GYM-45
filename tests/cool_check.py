# Заминка: раздел в конце дня (бодибилдинг/пауэрлифтинг), подбор под мышцы, предложение после сохранения, «Пропустить», проигрыватель.
# Запуск: python3 tests/cool_check.py index.html [папка_скриншотов]
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);O=sys.argv[2] if len(sys.argv)>2 else None;tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300)
    await pg.evaluate("el('login').style.display='none'")
    mk="(n,ex,sec)=>({name:n,focus:'т',sec:sec,ex:ex.map(x=>[x,3,'10',0])})"
    legs=await pg.evaluate(f"coolPick(({mk})('Ноги',['Приседания со штангой','Румынская тяга','Подъём на носки стоя'],'body'))")
    chest=await pg.evaluate(f"coolPick(({mk})('Грудь',['Жим штанги лёжа','Разводка гантелей лёжа','Французский жим'],'body'))")
    ok('день ног: квадрицепс, задняя поверхность, икры',any(i in legs for i in ['0613','1512']) and any(i in legs for i in ['1511','1585','1576']) and any(i in legs for i in ['1377','1398']),legs)
    ok('день груди: грудь и трицепс, без ног',any(i in chest for i in ['1271','1167']) and any(i in chest for i in ['0643','0817']) and not any(i in chest for i in ['0613','1512','1377']),chest)
    ok('4–6 упражнений, без повторов',all(4<=len(x)<=6 and len(set(x))==len(x) for x in [legs,chest]))
    ok('все анимации заминки есть',await pg.evaluate("Promise.all(Object.keys(CL_X).map(id=>fetch('media/'+id+'.mp4').then(r=>r.ok&&fetch('media/'+id+'.jpg').then(q=>q.ok)))).then(a=>a.every(Boolean))"))
    ok('только бодибилдинг и пауэрлифтинг',await pg.evaluate(f"coolFor({{sec:'body'}})&&coolFor({{sec:'pwr'}})&&coolFor({{g2:{{}}}})&&!coolFor({{sec:'street'}})&&!coolFor({{sec:'cross'}})&&!coolFor({{sec:'sw'}})"))
    # раздел в конце дня
    await pg.evaluate("show('body');authSetWeek(AUTH.find(p=>p.id==='wl'),0);authOpen(AUTH.find(p=>p.id==='wl'));el('bodyDays').querySelectorAll('.disc')[1].click()");await pg.wait_for_timeout(200)
    ok('в дне бодибилдинга раздел «Заминка» после упражнений',await pg.evaluate("!!el('dayCool')&&el('dayList').nextElementSibling===el('dayCool')&&el('dayCool').querySelectorAll('.day-row').length>=4"))
    await pg.evaluate("el('dayCool').querySelector('.day-row').click()");await pg.wait_for_timeout(150)
    ok('нажатие — открывается анимация',await pg.evaluate("!el('player').hidden&&/media\\/\\d{4}\\.mp4/.test(el('pvideo').src)"))
    await pg.evaluate("closeMedia()")
    if O:await pg.screenshot(path=O+'/cool_day.png',full_page=True)
    # тренировка → сохранить → предложение
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(150)
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>s.done=true));finishWorkout()");await pg.wait_for_timeout(600)
    ok('после сохранения предложена заминка',await pg.evaluate("!current&&!el('coolModal').hidden&&!!el('coolGo')&&!!el('coolSkip')"))
    if O:await pg.screenshot(path=O+'/cool_offer.png')
    await pg.evaluate("el('coolSkip').click()")
    ok('«Пропустить заминку» закрывает',await pg.evaluate("el('coolModal').hidden&&el('coolPlay').hidden"))
    h0=await pg.evaluate("safe.get().length")
    # ещё раз — начать
    await pg.evaluate("show('body');authOpen(AUTH.find(p=>p.id==='wl'));el('bodyDays').querySelectorAll('.disc')[1].click()");await pg.wait_for_timeout(150)
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(100)
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>s.done=true));finishWorkout()");await pg.wait_for_timeout(600)
    await pg.evaluate("el('coolGo').click()");await pg.wait_for_timeout(300)
    ok('проигрыватель: анимация, таймер 1:00',await pg.evaluate("!el('coolPlay').hidden&&el('clTime').textContent==='1:00'&&/\\d{4}\\.mp4/.test(el('clVid').src)"))
    if O:await pg.screenshot(path=O+'/cool_play.png')
    n=await pg.evaluate("CL.L.length")
    for i in range(n-1):await pg.evaluate("el('clNext').click()")
    ok('«Следующее» → последнее упражнение «Завершить»',await pg.evaluate(f"CL.i==={n-1}&&el('clNext').textContent==='Завершить'"))
    await pg.evaluate("el('clNext').click()");await pg.wait_for_timeout(100)
    ok('после заминки проигрыватель закрыт, история не изменилась',await pg.evaluate(f"el('coolPlay').hidden&&!CL&&safe.get().length==={h0}+1"))
    await pg.evaluate("coolStart(['0613']);CL.t=31;");await pg.wait_for_timeout(1300)
    ok('смена стороны на 30 с',await pg.evaluate("el('clSide').textContent==='Смени сторону'"))
    await pg.evaluate("el('clSkip').click()")
    ok('«Пропустить заминку» в проигрывателе закрывает',await pg.evaluate("el('coolPlay').hidden&&!CL"))
    # не бодибилдинг: стритлифтинг — без заминки
    await pg.evaluate("startWorkout({name:'Т',focus:'т',sec:'street',ex:[['Подтягивания',3,'5',0]]},false)");await pg.wait_for_timeout(100)
    ok('стритлифтинг — без раздела «Заминка»',await pg.evaluate("!el('dayCool')"))
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(100)
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>s.done=true));finishWorkout()");await pg.wait_for_timeout(600)
    ok('стритлифтинг — без предложения',await pg.evaluate("el('coolModal').hidden"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
