# Пауэрлифтинг: 5/3/1 Джима Вендлера — классика, цикл, прогрессия ТМ, соревновательные этапы.
# Запуск: python3 tests/w531_check.py index.html [папка_скриншотов]
import asyncio,os,sys,shutil,tempfile,http.server,threading,functools,datetime
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
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    # старая история и GVT не трогаются
    await pg.evaluate("localStorage.setItem(KEY,JSON.stringify([{date:'2026-10-01',name:'Старая',vol:1000,log:{'Жим лёжа':[{w:80,r:5,done:true}]}}]))")
    await pg.evaluate("document.querySelector('.disc[data-disc=\"Пауэрлифтинг\"]').click()");await pg.wait_for_timeout(100)
    first=await pg.evaluate("el('pwrPrograms').querySelector('.disc span span').textContent")
    ok('5/3/1 — первая в «Пауэрлифтинге»',first=='5/3/1',first)
    await pg.evaluate("el('pwrPrograms').querySelector('.disc').click()");await pg.wait_for_timeout(100)
    ok('экран открыт, форма старта',await pg.evaluate("!el('scr-w531').hidden&&!!el('w5Go')"))
    for k,v in {'press':60,'dead':160,'bench':100,'squat':140}.items():
      await pg.fill(f'#w5In_{k}',str(v))
    ok('ТМ = 90% с округлением 2,5',await pg.evaluate("el('w5Tm_press').textContent==='55 кг'&&el('w5Tm_dead').textContent==='145 кг'"),await pg.evaluate("el('w5Tm_press').textContent+' / '+el('w5Tm_dead').textContent"))
    if SHOT:await pg.screenshot(path=SHOT+'/w531-form.png',full_page=True)
    await pg.click('#w5Go');await pg.wait_for_timeout(150)
    ok('16 занятий, 4 недели',await pg.evaluate("el('w5Sess').querySelectorAll('.disc').length===16&&w5Weeks(w5Active())===4"))
    if SHOT:await pg.screenshot(path=SHOT+'/w531-cycle.png',full_page=True)
    # занятие 1 — жим стоя, неделя 1, вариант 1: 65/75/85 от ТМ 55 + разминка + BBB
    P=await pg.evaluate("(()=>{const p=w5Build(w5Active(),0);return {n:p.name,ex:p.ex.map(e=>e[0]),w:p.preset[0].map(s=>[s.w,s.r,!!s.warm,s.amrap||''])}})()")
    ok('жим стоя 1-я неделя: 35×5, 42.5×5, 47.5×5+',[x[:2] for x in P['w'] if not x[2]]==[[35,5],[42.5,5],[47.5,5]] and P['w'][-1][3]=='full',P['w'])
    ok('разминка 40/50/60% (22.5/27.5/32.5)',[x[0] for x in P['w'] if x[2]]==[22.5,27.5,32.5])
    ok('BBB: жим стоя 5×10 + подтягивания',P['ex']==['Армейский жим стоя','Армейский жим стоя','Подтягивания'],P['ex'])
    W3=await pg.evaluate("(()=>{const c=w5Active(),p=w5Build(c,9);return p.preset[0].filter(s=>!s.warm).map(s=>[s.w,s.r,s.amrap||''])})()")
    ok('неделя 3 становая: 5/3/1+ от ТМ 145',W3==[[110,5,''],[122.5,3,''],[137.5,1,'full']],W3)
    DL=await pg.evaluate("w5Build(w5Active(),13).preset[0].filter(s=>!s.warm).map(s=>[s.w,s.r,s.amrap||''])")
    ok('разгрузка: 40/50/60 ×5 без «+», без разминки',DL==[[57.5,5,''],[72.5,5,''],[87.5,5,'']],DL)
    # проходим занятие
    await pg.evaluate("el('w5Sess').querySelector('.disc').click()");await pg.wait_for_timeout(100)
    ok('обзор дня: 3 рабочих + разминка',await pg.evaluate("el('dayList').textContent.includes('+3 разминка')&&el('dayList').textContent.includes('5/5/5+')"),await pg.evaluate("el('dayList').querySelector('.day-row').innerText"))
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(100)
    ok('экран упражнения: цель с ТМ',await pg.evaluate("document.querySelector('#exList .target').textContent.includes('ТМ 55 кг')"),await pg.evaluate("document.querySelector('#exList .target').textContent"))
    if SHOT:await pg.screenshot(path=SHOT+'/w531-workout.png',full_page=False)
    await pg.evaluate("current.sets[0].forEach(s=>s.done=true);current.sets[0][5].r=11;current.sets[1].forEach(s=>s.done=true);finishWorkout()");await pg.wait_for_timeout(200)
    ok('после занятия — экран 5/3/1 с итогом',await pg.evaluate("currentScreen==='w531'&&el('w5Body').textContent.includes('Итог занятия')&&el('w5Body').textContent.includes('47,5 кг × 11')"))
    rec=await pg.evaluate("w5Active().recs[0]")
    ok('расч. 1ПМ 47.5×11 = 64.9',abs(rec['lifts']['press']['e1']-64.9)<0.1 and rec['lifts']['press']['ok'],rec['lifts'])
    ok('в истории: запись 5/3/1, раздел pwr, старая история цела',await pg.evaluate("(()=>{const h=safe.get();return h.length===2&&h[0].name==='Старая'&&h[1].name.startsWith('5/3/1')&&h[1].sec==='pwr'})()"),await pg.evaluate("JSON.stringify(safe.get().map(h=>[h.name,h.sec]))"))
    # рекорд на следующем занятии жима
    nt=await pg.evaluate("w5Build(w5Active(),4).ex[0][5]")
    ok('подсказка «побей рекорд» на 2-й неделе',nt and 'Рекорд' in nt,nt)
    # провал нормы в становой → откат; остальные +2.5/+5
    await pg.evaluate("""(()=>{const v=w5Store(),c=w5Active(v);c.recs.push({uid:'t1',s:9,wave:3,finishedAt:w5Now(),updatedAt:w5Now(),full:false,pr:[],lifts:{dead:{w:137.5,r:0,need:1,amrap:'full',e1:0,ok:false}}});
      c.recs.push({uid:'t0',s:1,wave:1,finishedAt:w5Now(),updatedAt:w5Now(),full:true,pr:[],lifts:{dead:{w:122.5,r:6,need:5,amrap:'full',e1:147,ok:true}}});w5Save(v);})()""")
    S=await pg.evaluate("w5Suggest(w5Active())")
    ok('следующий цикл: жим +2,5; присед +5; становая откат к 90% расч. 1ПМ',S['press']['tm']==57.5 and S['squat']['tm']==130 and S['dead']['tm']==132.5,{k:v['tm'] for k,v in S.items()})
    await pg.evaluate("el('w5NextC').click()");await pg.evaluate("el('w5NextC').click()");await pg.wait_for_timeout(100)
    ok('форма следующего цикла с ТМ',await pg.evaluate("el('w5In_press').value==='57.5'&&el('w5Go').textContent.includes('2')"))
    await pg.click('#w5Go');await pg.wait_for_timeout(100)
    ok('цикл 2 активен, цикл 1 в архиве',await pg.evaluate("(()=>{const v=w5Store();return w5Active(v).n===2&&v.cycles.filter(c=>c.closedAt).length===1&&el('w5Body').textContent.includes('Прошлые циклы')})()"))
    ok('BBB во 2-м цикле — 45% ТМ',await pg.evaluate("w5Build(w5Active(),0).ex[1][7].includes('45% ТМ')"))
    # дни
    cnt=await pg.evaluate("[4,3,2,1].map(d=>{const c=Object.assign({},w5Active(),{days:d});return [w5Sessions(c).length,w5Weeks(c)]})")
    ok('дни: 4→16/4 нед, 3→16/6 нед, 2→8/4, 1→6/6',cnt==[[16,4],[16,6],[8,4],[6,6]],cnt)
    two=await pg.evaluate("(()=>{const c=Object.assign({},w5Active(),{days:2});return w5Build(c,0).ex.map(e=>e[0])})()")
    ok('2 дня: присед + жим лёжа в одном занятии',two[0]=='Приседания со штангой' and 'Жим лёжа' in two,two)
    # соревнования: старт через 6 недель → предсоревновательный
    d=(datetime.date.today()+datetime.timedelta(days=40)).isoformat()
    await pg.evaluate("w5Form=null;renderW5();el('w5Meet').open=true")
    await pg.fill('#w5MDate',d);await pg.fill('#w5G_squat','150');await pg.fill('#w5G_bench','110');await pg.fill('#w5G_dead','180')
    await pg.click('#w5MSave');await pg.wait_for_timeout(100)
    ok('старт сохранён, подходы 85/92,5/100',await pg.evaluate("el('w5Body').textContent.includes('127,5 / 140 / 150')&&w5RecPhase()==='premeet'"),await pg.evaluate("w5RecPhase()"))
    await pg.evaluate("w5Form='new';renderW5()")
    ok('форма предлагает «Предсоревновательный»',await pg.evaluate("el('w5Phase').value==='premeet'"))
    for k,v in {'press':62,'dead':170,'bench':105,'squat':145}.items():await pg.fill(f'#w5In_{k}',str(v))
    await pg.click('#w5Go');await pg.click('#w5Go');await pg.wait_for_timeout(100)
    pre=await pg.evaluate("(()=>{const c=w5Active();return {ph:c.phase,d:w5Build(c,1).preset[0].filter(s=>!s.warm).map(s=>[s.w,s.r,s.single||'',s.amrap||'']),p:w5Build(c,0).preset[0].filter(s=>!s.warm).length,w2:w5Build(c,5).preset[0].filter(s=>!s.warm).map(s=>[s.r,s.amrap||''])}})()")
    ok('предсоревн.: становая 3×3 + синглы 85/92,5% цели (152,5/167,5)',pre['ph']=='premeet' and pre['d'][-2:]==[[152.5,1,'goal',''],[167.5,1,'goal','']] and pre['d'][2][1]==3,pre['d'])
    ok('предсоревн.: жим стоя без синглов, 3×5 без «+»',pre['p']==3 and pre['w2']==[[5,''],[5,''],[5,'']],pre)
    meet=await pg.evaluate("(()=>{const c=Object.assign({},w5Active(),{phase:'meetprep'});return [w5Sessions(c).length,w5Weeks(c),w5Build(c,1).preset[0].filter(s=>s.single).map(s=>s.w),w5Build(c,1).ex.length]})()")
    ok('подводка: 12 занятий + неделя старта, сингл 85%, без подсобки',meet[0]==12 and meet[1]==4 and meet[2]==[152.5] and meet[3]==1,meet)
    mass=await pg.evaluate("(()=>{const c=Object.assign({},w5Active(),{phase:'off_mass'});const p=w5Build(c,0);return [p.ex.map(e=>e[0]),p.preset[0].filter(s=>s.drop).length,p.preset[0].some(s=>s.amrap)]})()")
    ok('межсезонье·масса: подтягивания в суперсет, дроп-сет, без «+», кондиции',mass[0][1]=='Подтягивания' and mass[0][-1]=='Кондиции' and mass[1]==1 and not mass[2],mass)
    # активные программы на главном
    ok('в «Активных программах» есть 5/3/1',await pg.evaluate("mpList().some(x=>x.k==='w531')"))
    # облако: снимок и слияние
    ok('облачный снимок содержит 5/3/1',await pg.evaluate("(()=>{const s=cloudSnapshot();return s.w531&&s.w531.cycles.length===3&&s.w531.meet.goal.dead===180})()"))
    ok('слияние не теряет циклы',await pg.evaluate("(()=>{const a=w5Store(),b={cycles:[{id:'x',createdAt:'2020',recs:[{uid:'u',updatedAt:'1'}]}],activeId:null,meet:null};const m=mergeW5(a,b);return m.cycles.length===4&&m.activeId===a.activeId&&m.meet.goal.squat===150})()"))
    await pg.evaluate("show('w531')");await pg.wait_for_timeout(100)
    ok('без горизонтальной прокрутки',await pg.evaluate("document.documentElement.scrollWidth<=window.innerWidth"))
    if SHOT:await pg.screenshot(path=SHOT+'/w531-meet.png',full_page=True)
    ok('без ошибок JS',not errs,errs)
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
