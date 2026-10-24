# Фулбади для новичков: 8 недель, активация, следующая тренировка по порядку, переход к Картеру.
# Запуск: python3 tests/fbn_check.py index.html [папка_скриншотов]
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
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';show('programs');show('body')");await pg.wait_for_timeout(150)
    ok('данные: 8 недель × 3, 24 тренировки, A-B-A / B-A-B',await pg.evaluate("FBN_PROG.weeks.length===8&&FBN_PROG.weeks.every(w=>w.days.length===3)&&FBN_PROG.total===24&&FBN_PROG.weeks[0].days.map(d=>d.name.slice(-1)).join('')==='ABA'&&FBN_PROG.weeks[1].days.map(d=>d.name.slice(-1)).join('')==='BAB'"))
    ok('прогрессия: 3×10 → 4×8 → 4×6',await pg.evaluate("const e=k=>FBN_PROG.weeks[k].days[0].ex[0];e(0)[1]===3&&e(0)[2]===10&&e(4)[1]===4&&e(4)[2]===8&&e(6)[2]===6&&e(6)[3]>e(0)[3]"))
    ok('в списке «С чего начать» — 8 недель',await pg.evaluate("[...el('bodyProgs').querySelectorAll('.disc')].some(b=>b.textContent.includes('Фулбади для новичков')&&b.textContent.includes('8 недель'))&&!BODY.some(p=>p.name==='Фулбади для новичков')"))
    await pg.evaluate("[...el('bodyProgs').querySelectorAll('.disc')].find(b=>b.textContent.includes('Фулбади для новичков')).click()");await pg.wait_for_timeout(150)
    ok('кнопка «Начать программу» и «Следующий шаг»',await pg.evaluate("!!el('bodyDays').querySelector('.au-start')&&!!el('bodyDays').querySelector('.next-step')"))
    await pg.evaluate("el('bodyDays').querySelector('.au-start').click()");await pg.wait_for_timeout(150)
    ok('активна: следующая — Нед. 1 · Пн · День A',await pg.evaluate("el('bodyDays').querySelector('.au-go').textContent.includes('Нед. 1 · Пн · День A')"))
    if SHOT:await pg.screenshot(path=SHOT+'/fbn_act.png')
    await pg.evaluate("show('home')");await pg.wait_for_timeout(100)
    ok('на главной в «Активных программах»',await pg.evaluate("el('dashActive').textContent.includes('Фулбади для новичков')&&el('dashActive').textContent.includes('тренировка 1 из 24')"))
    # провести тренировку
    async def train():
      await pg.evaluate("[...el('dashActive').querySelectorAll('.mp-open')].find(b=>b.textContent.includes('Фулбади')).click()");await pg.wait_for_timeout(150)
      await pg.evaluate("el('bodyDays').querySelector('.au-go').click()");await pg.wait_for_timeout(120);await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(150)
      await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));finishWorkout()");await pg.wait_for_timeout(150);await pg.evaluate("show('home')");await pg.wait_for_timeout(80)
    await train()
    ok('после 1-й: следующая Ср · День B',await pg.evaluate("auPlanNext(FBN_PROG).w===0&&auPlanNext(FBN_PROG).d===1&&auCount('fbn')===1"))
    await train();await train()
    ok('после 3-й: переход на неделю 2 (B)',await pg.evaluate("auPlanNext(FBN_PROG).w===1&&FBN_PROG.weeks[1].days[0].name.endsWith('B')"))
    await pg.evaluate("[...el('dashActive').querySelectorAll('.mp-open')].find(b=>b.textContent.includes('Фулбади')).click()");await pg.wait_for_timeout(150)
    ok('открывается сразу неделя 2',await pg.evaluate("el('auWk').querySelector('.on').textContent.includes('Нед. 2')"))
    await pg.evaluate("el('bodyDays').querySelector('.au-go').click()");await pg.wait_for_timeout(120);await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(150)
    ok('повторы из плана, вес из прошлой тренировки',await pg.evaluate("current.sets[0][0].r===10&&current.sets[0][0].w>0"))
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>{s.done=true;}));finishWorkout()");await pg.wait_for_timeout(150)
    # прыжок в конец: симулируем 24 тренировки
    await pg.evaluate("const h=safe.get();FBN_PROG.weeks.forEach((w,wi)=>w.days.forEach(d=>h.push({date:'2026-01-01',name:d.name,vol:1,log:{},au:{id:'fbn',w:wi},sec:'body'})));safe.set?safe.set(h):localStorage.setItem(HK,JSON.stringify(h))")
    await pg.evaluate("authOpen(FBN_PROG)");await pg.wait_for_timeout(150)
    ok('пройдена: «Дальше: Фулбади Картера» и «Завершить и сохранить итог»',await pg.evaluate("auPlanNext(FBN_PROG)===null&&!!el('bodyDays').querySelector('.au-fin')&&el('bodyDays').querySelector('.au-next').textContent.includes('Фулбади 3 дня')"))
    await pg.evaluate("el('bodyDays').querySelector('.au-fin').click()");await pg.wait_for_timeout(150)
    ok('итог в архиве, программа больше не активна',await pg.evaluate("parGet().some(r=>r.prog==='au:fbn')&&!auSt().act.fbn&&!mpList().some(x=>x.k==='au:fbn')"))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f'\n{sum(R)}/{len(R)} PASS');sys.exit(0 if all(R) else 1)
asyncio.run(m())
