# Питание: листание дней в дневнике и аналитика питания.
# Запуск: python3 tests/food_days_check.py index.html [папка_скриншотов]
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
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    await pg.evaluate("""(()=>{const L=[];for(let i=0;i<10;i++){const d=new Date();d.setDate(d.getDate()-i);if(i===4)continue;L.push({id:'t'+i,date:localDate(d),name:'Тест '+i,kcal:2000+i*50,p:150,f:70,c:200});}localStorage.setItem(FOODK,JSON.stringify(L));})()""")
    await pg.evaluate("FOOD_DAY=null;renderFood();show('food')");await pg.wait_for_timeout(150)
    ok('сегодня: заголовок и стрелка «вперёд» выключена',await pg.evaluate("el('foodDayLbl').textContent==='Сегодня'&&el('foodNext').disabled&&el('foodToToday').hidden&&el('foodKcal').textContent==='2000'"))
    await pg.evaluate("el('foodPrev').click()");await pg.wait_for_timeout(100)
    ok('‹ — вчера: свои записи и калории',await pg.evaluate("el('foodDayLbl').textContent==='Вчера'&&el('foodKcal').textContent==='2050'&&el('foodListH').textContent==='Приёмы за вчера'&&!el('foodNext').disabled&&!el('foodToToday').hidden"))
    if SHOT:await pg.screenshot(path=SHOT+'/food-yday.png')
    for _ in range(3):await pg.evaluate("el('foodPrev').click()")
    await pg.wait_for_timeout(100)
    ok('пустой день — подсказка дописать',await pg.evaluate("el('foodList').textContent.includes('дописать')&&el('foodKcal').textContent==='0'"))
    await pg.evaluate("el('fName').value='Забытый ужин';el('fKcal').value='500';el('fAdd').click()");await pg.wait_for_timeout(100)
    ok('запись добавляется в выбранный день',await pg.evaluate("(()=>{const d=new Date();d.setDate(d.getDate()-4);const r=foodGet().find(x=>x.name==='Забытый ужин');return r&&r.date===localDate(d)&&el('foodKcal').textContent==='500'})()"))
    await pg.evaluate("el('foodToToday').click()");await pg.wait_for_timeout(100)
    ok('«Вернуться к сегодня»',await pg.evaluate("el('foodDayLbl').textContent==='Сегодня'&&el('foodKcal').textContent==='2000'"))
    await pg.evaluate("for(let i=0;i<3;i++)el('foodPrev').click();for(let i=0;i<5;i++)el('foodNext').click()");await pg.wait_for_timeout(100)
    ok('в будущее не уходит',await pg.evaluate("foodToday()===localDate()"))
    # аналитика
    await pg.evaluate("AN_UI.tab='food';AN_UI.fp=7;show('progress');anRender()");await pg.wait_for_timeout(200)
    ok('вкладка «Питание» в Прогрессе',await pg.evaluate("!el('anFood').hidden&&[...el('anTabs').querySelectorAll('button')].some(b=>b.dataset.v==='food'&&b.classList.contains('on'))"))
    ok('7 дней: 7 из 7 с записями (4-й день дописан)',await pg.evaluate("el('anFood').textContent.includes('7 / 7')"),await pg.evaluate("el('anFood').innerText.slice(0,400)"))
    ok('серия: 10 дней подряд',await pg.evaluate("anFoodStreak(anFoodDays())===10"))
    ok('график: 7 столбиков, подпись дня',await pg.evaluate("el('anFoodChart').querySelectorAll('.b').length===7&&el('anFoodChart').querySelector('.an-cap').textContent.includes('000 ккал')"))
    if SHOT:await pg.screenshot(path=SHOT+'/an-food.png',full_page=True)
    await pg.evaluate("[...el('anFp').querySelectorAll('button')].find(b=>b.dataset.v==='30').click()");await pg.wait_for_timeout(150)
    ok('30 дней: 30 столбиков, 10 дней с записями',await pg.evaluate("el('anFoodChart').querySelectorAll('.b').length===30&&el('anFood').textContent.includes('10 / 30')"))
    await pg.evaluate("el('anFoodChart').querySelectorAll('g[data-i]')[27].dispatchEvent(new MouseEvent('click',{bubbles:true}))");await pg.wait_for_timeout(80)
    await pg.evaluate("el('anFoodOpen').click()");await pg.wait_for_timeout(150)
    ok('«Открыть день в дневнике» → нужный день',await pg.evaluate("currentScreen==='food'&&el('foodDayLbl').textContent!=='Сегодня'&&el('foodKcal').textContent==='2100'"))
    ok('без горизонтальной прокрутки',await pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f'\n{sum(R)}/{len(R)} PASS');sys.exit(0 if all(R) else 1)
asyncio.run(m())
