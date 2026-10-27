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
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
