# Аналитика: нагрузка, упражнения, тело, восстановление, история с RPE, запись RIR/времени/отдыха.
# Запуск: python3 tests/analytics_check.py index.html [папка_скриншотов]
import asyncio,json,os,sys,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
HTML=os.path.abspath(sys.argv[1]);SHOT=sys.argv[2] if len(sys.argv)>2 else None
tmp=tempfile.mkdtemp();shutil.copy(HTML,tmp+'/index.html')
if os.path.isdir(os.path.dirname(HTML)+'/media'):os.symlink(os.path.dirname(HTML)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
SEED='''(()=>{const D=n=>{const d=new Date();d.setDate(d.getDate()-n);return localDate(d);};const h=[];
for(let k=0;k<12;k++){const n=40-k*3.4|0,w=80+k*2.5;
 h.push({date:D(n),name:k%2?"Верх / Низ":"5×5 · Сила · неделя "+(k+1),vol:Math.round(w*5*5+60*10*3),sec:k%2?"body":"pwr",dur:3600+k*60,rest:150-k*3,
  log:{"Жим лёжа":[{w:w,r:5,done:true,rir:k>9?"2":"1"},{w:w,r:5,done:true},{w:w,r:5,done:true}],"Подтягивания":[{w:0,r:8+k%3,done:true},{w:0,r:8,done:true}],"Тяга штанги":[{w:60,r:10,done:true},{w:60,r:10,done:false}]}});}
h.push({date:D(2),name:"Сотка · день 3",sw:true,circles:5,target:5,pct:100,secs:900});
h.push({date:D(1),name:"Fran",cross:true,score:"6:40",secs:400});
h.push({date:D(30),name:"Старая запись",vol:1000,log:[[100,5]]});
h.sort((a,b)=>a.date.localeCompare(b.date));localStorage.setItem("gym45_history_v1",JSON.stringify(h));
localStorage.setItem("gym45_nutrition_target_v1",JSON.stringify({sex:"male",goal:"maintain",activity:"light",age:45,weight:96,height:180,bf:20,src:{units:"metric",w:"96",h:"180"},updatedAt:1}));})()'''
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate(SEED);await pg.reload();await pg.wait_for_timeout(300)
    hist0=await pg.evaluate("localStorage.getItem('gym45_history_v1')")
    await pg.evaluate("el('login').style.display='none';show('progress')");await pg.wait_for_timeout(200)
    ok('«Прогресс»: без демо-данных («пример»)',await pg.evaluate("!el('scr-progress').innerText.includes('пример')"))
    ok('плитки: тренировок и тонн за 7 дней с динамикой',await pg.evaluate("+el('tWeek').textContent>=1&&el('tVol').textContent!==''"))
    ok('4 вкладки, по умолчанию «Нагрузка»',await pg.evaluate("el('anTabs').querySelectorAll('button').length===4&&!el('anLoad').hidden&&el('anEx').hidden"))
    ok('нагрузка: 8 недельных столбцов',await pg.evaluate("el('anBars').querySelectorAll('.an-bar').length===8"))
    await pg.evaluate("el('anBars').querySelectorAll('.an-bar')[5].dispatchEvent(new MouseEvent('click',{bubbles:true}))")
    ok('нажатие на столбец — подробности недели',await pg.evaluate("el('anBars').querySelector('.an-cap').innerText.startsWith('Неделя с')"),await pg.evaluate("el('anBars').querySelector('.an-cap').innerText"))
    if SHOT:await pg.screenshot(path=SHOT+'/an-load.png',full_page=False)
    for met in ['sets','n','time','rpe','rir']:
      await pg.evaluate(f"document.querySelector('#anMet [data-v=\"{met}\"]').click()");await pg.wait_for_timeout(30)
    ok('метрики переключаются (тоннаж/подходы/тренировки/время/RPE/RIR)',await pg.evaluate("AN_UI.met==='rir'&&el('anBars').querySelectorAll('.an-bar').length===8"))
    await pg.evaluate("document.querySelector('#anDisc [data-v=\"pwr\"]').click()");await pg.wait_for_timeout(30)
    pw=await pg.evaluate("anRecs().filter(r=>r.sec==='pwr').length")
    ok('фильтр «Пауэрлифтинг»',await pg.evaluate("AN_UI.sec==='pwr'") and pw==6,pw)
    await pg.evaluate("document.querySelector('#anDisc [data-v=\"cross\"]').click()");await pg.wait_for_timeout(30)
    ok('«Кроссфит»: свои метрики без тоннажа',await pg.evaluate("![...el('anMet').querySelectorAll('button')].some(b=>b.dataset.v==='vol')"))
    await pg.evaluate("document.querySelector('#anDisc [data-v=\"sw\"]').click()");await pg.wait_for_timeout(30)
    ok('«Стрит-воркаут»: последние круговые',await pg.evaluate("el('anLoad').innerText.includes('Сотка · день 3')"))
    await pg.evaluate("document.querySelector('#anDisc [data-v=\"all\"]').click();document.querySelector('#anMet [data-v=\"vol\"]').click()")
    # упражнения
    await pg.evaluate("document.querySelector('#anTabs [data-v=\"ex\"]').click()");await pg.wait_for_timeout(60)
    await pg.select_option('#anExSel','Жим лёжа');await pg.wait_for_timeout(60)
    e=json.loads(await pg.evaluate("JSON.stringify(anExData(anRecs())['Жим лёжа'].map(s=>Math.round(s.e1rm*10)/10))"))
    ok('расчётный 1ПМ по Эпли (80×5 → 93,3 кг)',e[0]==93.3 and len(e)==12,e[:3])
    ok('график 1ПМ с рекордами и подписью',await pg.evaluate("el('anExChart').querySelectorAll('.an-pt.pr').length>=5&&el('anExChart').querySelector('.an-cap').innerText.includes('рекорд')"))
    ok('последние подходы показывают RIR',await pg.evaluate("el('anEx').innerText.includes('RIR 2')"))
    await pg.select_option('#anExSel','Подтягивания');await pg.wait_for_timeout(60)
    ok('собственный вес: метрики по повторам',await pg.evaluate("[...el('anExM').querySelectorAll('button')].map(b=>b.dataset.v).join()==='maxr,reps'"))
    if SHOT:await pg.select_option('#anExSel','Жим лёжа');await pg.wait_for_timeout(60);await pg.evaluate("el('anTabs').scrollIntoView()");await pg.screenshot(path=SHOT+'/an-ex.png')
    # тело
    await pg.evaluate("document.querySelector('#anTabs [data-v=\"body\"]').click()");await pg.wait_for_timeout(60)
    await pg.fill('#anW','95,4');await pg.evaluate("el('anBody').querySelector('details').open=true");await pg.fill('#anM_waist','92');await pg.click('#anBSave');await pg.wait_for_timeout(80)
    ok('замер тела сохранён',await pg.evaluate("anSt().body.some(x=>x.w===95.4&&x.waist===92)"))
    ok('предложение обновить вес в профиле',await pg.evaluate("!!el('anBUp')"))
    await pg.click('#anBUp');await pg.wait_for_timeout(60)
    ok('вес обновлён в норме и профиле',await pg.evaluate("ntT().weight===95.4&&pfGet().weight===95.4"))
    await pg.evaluate("(()=>{const s=anSt();for(let i=1;i<10;i++){const d=new Date();d.setDate(d.getDate()-i*2);s.body.push({date:localDate(d),w:96+i*0.1,waist:93})}anSave(s)})()");await pg.evaluate("anRender()")
    ok('график веса со средним за 7 дней',await pg.evaluate("!!el('anWChart').querySelector('.an-avg')&&el('anBody').innerText.includes('среднее за неделю')"))
    if SHOT:await pg.evaluate("el('anTabs').scrollIntoView()");await pg.screenshot(path=SHOT+'/an-body.png')
    # восстановление
    await pg.evaluate("document.querySelector('#anTabs [data-v=\"rec\"]').click()");await pg.wait_for_timeout(60)
    await pg.evaluate("document.querySelector('#anSlQ [data-v=\"7\"]').click()");await pg.click('#anSlP');await pg.evaluate("document.querySelector('#anFeel [data-v=\"4\"]').click()")
    ok('сон 7 → +0,5 = 7,5 ч и самочувствие сохранены',await pg.evaluate("(s=>s.h===7.5&&s.f==='4')(anSt().sleep[localDate()])"))
    ok('график сна за 14 дней',await pg.evaluate("el('anSlChart').querySelectorAll('.an-bar').length===14"))
    if SHOT:await pg.evaluate("el('anTabs').scrollIntoView()");await pg.screenshot(path=SHOT+'/an-rec.png')
    # история и RPE
    await pg.evaluate("el('hist').querySelector('details').open=true")
    await pg.evaluate("el('hist').querySelectorAll('details')[2].open=true;el('hist').querySelectorAll('details')[2].querySelector('.an-rpe [data-v=\"8\"]').click()")
    ok('RPE в истории сохраняется и показывается',await pg.evaluate("Object.values(anSt().rpe).includes(8)&&!!el('hist').querySelector('.an-rpe-b')"))
    ok('история показывает подходы и время',await pg.evaluate("el('hist').querySelectorAll('details')[2].innerText.includes('Жим лёжа')"))
    ok('история тренировок не изменена',await pg.evaluate("localStorage.getItem('gym45_history_v1')")==hist0)
    ok('без горизонтальной прокрутки',await pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    # тренировка: RIR, время и отдых записываются
    await pg.evaluate("show('body')");await pg.wait_for_timeout(60)
    await pg.evaluate("openProg(BODY[0],'Бодибилдинг · программа');el('bodyProgs')&&0")
    await pg.wait_for_timeout(100)
    started=await pg.evaluate("(()=>{const b=document.querySelector('#scr-bodyprog .disc, #bodyDays .disc');if(b){b.click();return 1}return 0})()")
    await pg.wait_for_timeout(100)
    await pg.evaluate("(()=>{const b=[...document.querySelectorAll('#scr-day button')].find(x=>/Начать/.test(x.textContent));b&&b.click()})()");await pg.wait_for_timeout(150)
    inw=await pg.evaluate("currentScreen==='workout'&&!!current")
    ok('тренировка бодибилдинга открыта',inw,started)
    if inw:
      ok('под упражнением — «Запас повторов (RIR)»',await pg.evaluate("!!el('exList').querySelector('.rir-row')"))
      await pg.evaluate("el('exList').querySelector('.rir-row [data-v=\"2\"]').click()")
      await pg.evaluate("current.startedAt=new Date(Date.now()-50*60000).toISOString();current.sets.forEach((se,i)=>se.forEach((s,j)=>{s.done=true;s.at=Date.now()-(40-i*4-j)*60000;}))")
      await pg.evaluate("finishWorkout()");await pg.wait_for_timeout(200)
      last=json.loads(await pg.evaluate("JSON.stringify(safe.get().slice(-1)[0])"))
      fx=list(last['log'].values())[0]
      ok('в истории: раздел, время, отдых, RIR и время подходов',last.get('sec')=='body' and last.get('dur',0)>=2900 and last.get('rest') and any(s.get('rir')=='2' for s in fx) and all('at' in s for s in fx),{k:last.get(k) for k in ('sec','dur','rest')})
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f'\n{sum(R)}/{len(R)} PASS');sys.exit(0 if all(R) else 1)
asyncio.run(m())
