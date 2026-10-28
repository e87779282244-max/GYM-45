# Авторские программы: учёт прохождения, «следующая» в блоке автора, отметка «пройдена», запись au в истории.
# Запуск: python3 tests/au_progress_check.py index.html [папка_скриншотов]
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools,json
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);O=sys.argv[2] if len(sys.argv)>2 else None;tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(300)
    await pg.evaluate("el('login').style.display='none';show('body')")
    ok('изначально «следующая» — первая программа (Фулбади Картера)',await pg.evaluate("auNextHint().id==='pcfb'&&!!el('bodyProgs').querySelector('.au-cur')"))
    await pg.evaluate("const p=AUTH.find(x=>x.id==='wl');authSetWeek(p,0);authOpen(p);el('bodyDays').querySelectorAll('.disc')[0].click();el('dayStart').click()")
    await pg.wait_for_timeout(100)
    ok('в тренировке есть метка программы',await pg.evaluate("current.program.au&&current.program.au.id==='wl'"))
    await pg.evaluate("current.sets.forEach(se=>se.forEach(s=>s.done=true));finishWorkout()");await pg.wait_for_timeout(150)
    ok('в истории запись с au',await pg.evaluate("safe.get().slice(-1)[0].au.id==='wl'"))
    ok('счётчик Warlock = 1',await pg.evaluate("auCount('wl')===1"))
    ok('совет после тренировки: прогресс программы',await pg.evaluate("el('coachText').textContent.includes('1 из 32')"),await pg.evaluate("el('coachText').textContent"))
    # старая запись без au считается по уникальному названию дня
    await pg.evaluate("const h=safe.get();h.push({date:'2026-10-20',name:'Вт · Низ · акцент квадрицепс',vol:1000,log:{},sec:'body'});localStorage.setItem(KEY,JSON.stringify(h))")
    ok('старая запись без au учитывается по названию дня',await pg.evaluate("auCount('wl')===2"))
    await pg.evaluate("show('body');renderBody()")
    ok('в списке у Warlock — «2 / 32 трен.»',await pg.evaluate("[...el('bodyProgs').querySelectorAll('.disc')].some(b=>b.textContent.includes('Штурм без пощады')&&b.textContent.includes('2 / 32'))"))
    # отметка «пройдена» → «Дальше: …» (у Медоуза одна программа — следующая по порядку)
    await pg.evaluate("authOpen(AUTH.find(x=>x.id==='wl'));el('bodyDays').querySelector('.au-mark').click()");await pg.wait_for_timeout(80)
    nx=await pg.evaluate("auNext(AUTH.find(x=>x.id==='wl')).name.split(' · ')[0]")
    ok('после отметки — «Дальше: '+nx+'»',await pg.evaluate("!!el('bodyDays').querySelector('.au-next')&&el('bodyDays').querySelector('.au-next').textContent.includes("+json.dumps(nx)+")"))
    if O:await pg.screenshot(path=O+'/au-prog.png')
    await pg.evaluate("el('bodyDays').querySelector('.au-next').click()");await pg.wait_for_timeout(80)
    ok('кнопка открывает следующую программу',await pg.evaluate("el('bodyName').textContent.includes("+json.dumps(nx)+")"))
    ok('пройденная — «✓ пройдена» в списке',await pg.evaluate("show('body');renderBody();[...el('bodyProgs').querySelectorAll('.disc.au-done')].some(b=>b.textContent.includes('Штурм без пощады'))"))
    ok('блок пройден → следующая по сложности',await pg.evaluate("(()=>{const v=auSt();v.done.pcfb=1;v.done.pcul=1;auSave(v);return auNext(AUTH.find(x=>x.id==='pcul')).lvl>=1})()"))
    ok('отметка в облачном снимке',await pg.evaluate("!!cloudSnapshot().auprog.done.wl"))
    await pg.evaluate("show('body');renderBody()");
    if O:await pg.evaluate("el('bodyProgs').scrollIntoView()");await pg.screenshot(path=O+'/au-list.png') if O else None
    ok('без горизонтальной прокрутки',await pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f"\n{sum(R)}/{len(R)} PASS");sys.exit(0 if all(R) else 1)
asyncio.run(m())
