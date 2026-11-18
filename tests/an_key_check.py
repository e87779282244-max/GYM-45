# Аналитика: главные движения (расчётный 1ПМ, рост за 8 недель, рекорд) и выполнение плана недели.
# Запуск: python3 tests/an_key_check.py index.html [папка_скриншотов]
import asyncio,os,sys,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
HTML=os.path.abspath(sys.argv[1]);SHOT=sys.argv[2] if len(sys.argv)>2 else None
tmp=tempfile.mkdtemp();shutil.copy(HTML,tmp+'/index.html')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    await pg.evaluate("show('progress')");await pg.wait_for_timeout(100)
    ok('без данных: подсказка вместо пустоты',await pg.evaluate("el('anKey').textContent.includes('После первой тренировки')"))
    # история: присед 70 дней назад 100×5, неделю назад 120×5 (+ старое имя «Присед со штангой»), жим 80×8
    await pg.evaluate("""(()=>{const d=n=>{const x=new Date();x.setDate(x.getDate()-n);return localDate(x);};
      localStorage.setItem(KEY,JSON.stringify([{date:d(70),name:'a',vol:1,log:{'Присед со штангой':[{w:100,r:5,done:true}]}},
       {date:d(7),name:'b',vol:1,log:{'Приседания со штангой':[{w:120,r:5,done:true}],'Жим лёжа':[{w:80,r:8,done:true}]}}]));show('home');show('progress');})()""");await pg.wait_for_timeout(150)
    L=await pg.evaluate("anKeyLifts(anRecs())")
    sq=[x for x in L if x['t']=='Присед'][0]
    ok('присед: старое и новое имя — одно движение, рост за 8 недель',round(sq['cur'],1)==140 and round(sq['delta'],1)==23.3 and sq['since']=='за 8 нед.' and sq['cnt']==2,{k:sq[k] for k in ['cur','delta','since','cnt']})
    ok('жим: расчётный 1ПМ, «с начала»',any(x['t']=='Жим лёжа' and x['since']=='с начала' for x in L))
    ok('карточка: 2 движения, рост +23,3 кг',await pg.evaluate("el('anKey').querySelectorAll('.an-keyr').length===2&&el('anKey').textContent.includes('+23,3')"),await pg.evaluate("el('anKey').innerText"))
    if SHOT:await pg.screenshot(path=SHOT+'/an-key.png',full_page=False)
    await pg.evaluate("el('anKey').querySelector('.an-keyr').click()");await pg.wait_for_timeout(150)
    ok('нажатие → вкладка «Упражнения» с этим движением',await pg.evaluate("AN_UI.tab==='ex'&&AN_UI.ex==='Приседания со штангой'&&!el('anEx').hidden"))
    # план недели
    ok('без активных программ: «с понедельника»',await pg.evaluate("el('tStreakL').textContent==='с понедельника'"))
    await pg.evaluate("const v=auSt();v.act={y3t:{start:localDate(),base:0}};auSave(v);show('home');show('progress')");await pg.wait_for_timeout(100)
    ok('с Y3T: плитка «N/5 по плану недели»',await pg.evaluate("el('tStreak').textContent.endsWith('/5')&&el('tStreakL').textContent==='по плану недели'"),await pg.evaluate("el('tStreak').textContent"))
    ok('«дней подряд» больше нет',await pg.evaluate("!el('scr-progress').textContent.includes('дней подряд')"))
    # GVT: 10×10 на ≈60 % — не «падение» 1ПМ
    await pg.evaluate("""(()=>{const d=n=>{const x=new Date();x.setDate(x.getDate()-n);return localDate(x);};const g=[];for(let i=0;i<10;i++)g.push({w:62.5,r:10,done:true});
      localStorage.setItem(KEY,JSON.stringify([{date:d(20),name:'Мясорубка',vol:1,log:{'Приседания со штангой':[{w:70,r:10,done:true}]}},
       {date:d(1),name:'German Volume Training',fam:'g2',vol:1,log:{'Приседания со штангой':g}}]));AN_UI.tab='load';show('home');show('progress');})()""");await pg.wait_for_timeout(150)
    L=await pg.evaluate("anKeyLifts(anRecs())");sq=[x for x in L if x['t']=='Присед'][0]
    ok('GVT 62,5×10 не снижает расчётный 1ПМ (93,3, ±0)',round(sq['cur'],1)==93.3 and round(sq['delta'],1)==0 and sq['cnt']==1,{k:sq[k] for k in ['cur','delta','cnt']})
    await pg.evaluate("el('anKey').querySelector('.an-keyr').click()");await pg.wait_for_timeout(150)
    t=await pg.evaluate("el('anEx').innerText")
    ok('упражнение: последний 1ПМ 93,3, без −11 %, пояснение про GVT','83,3 кг' not in t.split('Последние подходы')[0] and 'GVT в расчётный 1ПМ не входят' in t and '62,5×10' in t,t[:300])
    await pg.evaluate("[...document.querySelectorAll('#anExM button')].find(b=>b.dataset.v==='maxw').click()");await pg.wait_for_timeout(100)
    ok('«Макс. вес» по-прежнему видит тренировку GVT',(await pg.evaluate("el('anEx').innerText")).count('62,5')>=1)
    await pg.evaluate("""(()=>{const g=[];for(let i=0;i<10;i++)g.push({w:62.5,r:10,done:true});localStorage.setItem(KEY,JSON.stringify([{date:localDate(),name:'GVT · Этап I',vol:1,log:{'Приседания со штангой':g}}]));AN_UI.exm='e1rm';show('home');show('progress');AN_UI.tab='ex';anRender();})()""");await pg.wait_for_timeout(150)
    ok('только GVT: вместо 1ПМ — макс. вес с пояснением, без ошибок',await pg.evaluate("el('anEx').innerText.includes('Пока только тренировки GVT')"))
    # сумма личных рекордов троеборья
    await pg.evaluate("""(()=>{const d=n=>{const x=new Date();x.setDate(x.getDate()-n);return localDate(x);};
      localStorage.setItem(KEY,JSON.stringify([{date:d(70),name:'a',vol:1,log:{'Приседания со штангой':[{w:150,r:1,done:true}],'Жим лёжа':[{w:100,r:1,done:true}],'Становая тяга':[{w:180,r:1,done:true}]}},
       {date:d(5),name:'b',vol:1,log:{'Приседания со штангой':[{w:155,r:1,done:true}],'Жим лёжа':[{w:105,r:1,done:true}],'Становая тяга':[{w:190,r:1,done:true}]}}]));AN_UI.tab='load';show('home');show('progress');})()""");await pg.wait_for_timeout(150)
    t=await pg.evaluate("el('anKey').innerText")
    ok('сумма личных рекордов 450 кг, +20 кг (+4,7 %), факт по одиночным',all(x in t for x in ['Сумма личных рекордов','450 кг','+20 кг (+4,7 %)','факт по одиночным 450 кг']),t[-200:])
    # GVT: повторы из 100
    await pg.evaluate("""(()=>{const d=n=>{const x=new Date();x.setDate(x.getDate()-n);return localDate(x);};
      const g=(w,a)=>a.map(r=>({w:w,r:r,p:10,done:true}));
      localStorage.setItem(KEY,JSON.stringify([{date:d(10),name:'German Volume Training',fam:'g2',vol:1,log:{'Приседания со штангой':g(60,[10,10,10,10,10,9,8,7,6,6])}},
       {date:d(6),name:'German Volume Training',fam:'g2',vol:1,log:{'Приседания со штангой':g(60,[10,10,10,10,10,10,10,9,8,7])}},
       {date:d(2),name:'German Volume Training',fam:'g2',vol:1,log:{'Приседания со штангой':g(62.5,[10,10,10,10,10,10,10,10,10,9])}}]));
      show('home');show('progress');AN_UI.tab='ex';AN_UI.trainSub='ex';AN_UI.ex='Приседания со штангой';anRender();})()""");await pg.wait_for_timeout(150)
    t=await pg.evaluate("el('anEx').innerText")
    ok('GVT: 86/100 → 94/100 (+8 повт. с 60 кг) → 99/100 (вес +2,5 кг)',all(x in t for x in ['GVT · повторы из плана','86/100','94/100','+8 повт. с 60 кг','99/100','вес +2,5 кг']),t[:600])
    ok('плитка: «объём работы, т»',await pg.evaluate("document.querySelector('#tVol').parentElement.textContent.includes('объём работы, т')"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
