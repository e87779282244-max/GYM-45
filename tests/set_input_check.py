# Поля подходов: при нажатии число выделено целиком; введённые вес/повторы подставляются в следующие подходы (не ломая схемы с разными весами).
# Запуск: python3 tests/set_input_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(viewport={'width':390,'height':844},has_touch=True,is_mobile=True);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';coolOffer=function(){}")
    await pg.evaluate("startWorkout({name:'Т',focus:'т',sec:'body',ex:[['Жим штанги лёжа',4,'8',60]]},false);el('dayStart').click()");await pg.wait_for_timeout(200)
    W=lambda k:f"#exList input[data-s='{k}'][data-f='w']";Rp=lambda k:f"#exList input[data-s='{k}'][data-f='r']"
    await pg.evaluate("current.sets[0].forEach(s=>s.w=60);renderWorkout()")
    await pg.tap(W(0));await pg.wait_for_timeout(120)
    ok('нажатие на вес — число выделено целиком',await pg.evaluate(f"(()=>{{const t=document.querySelector(\"{W(0)}\");return document.activeElement===t&&t.selectionStart===0&&t.selectionEnd===t.value.length&&t.value.length>0}})()"),await pg.evaluate(f"(()=>{{const t=document.querySelector(\"{W(0)}\");return [document.activeElement===t,t.value,t.selectionStart,t.selectionEnd]}})()"))
    await pg.keyboard.type('72.5')
    ok('ввод заменяет старое число',await pg.evaluate(f"document.querySelector(\"{W(0)}\").value")=='72.5')
    ok('вес подставился во все следующие подходы',await pg.evaluate("current.sets[0].filter(s=>!s.warm).every(s=>s.w===72.5)")and await pg.evaluate(f"document.querySelector(\"{W(3)}\").value")=='72.5')
    await pg.tap(Rp(0));await pg.wait_for_timeout(120);await pg.keyboard.press('Backspace')
    ok('«удалить» стирает всё число',await pg.evaluate(f"document.querySelector(\"{Rp(0)}\").value")=='')
    await pg.keyboard.type('10')
    ok('повторы подставились в следующие',await pg.evaluate("current.sets[0].map(s=>s.r).join()")=='10,10,10,10')
    # отмеченный подход не трогаем; изменение во 2-м меняет только 3-й и 4-й
    await pg.evaluate("document.querySelectorAll('#exList .chk')[0].click()");await pg.wait_for_timeout(100)
    await pg.evaluate("el('wkRestSkip')&&el('wkRestSkip').click()")
    await pg.tap(W(1));await pg.wait_for_timeout(120);await pg.keyboard.type('70')
    ok('изменение во 2-м: 1-й (выполнен) не меняется, 3-й и 4-й — да',await pg.evaluate("current.sets[0].map(s=>s.w).join()")=='72.5,70,70,70')
    # схема с разными весами по подходам не ломается
    await pg.evaluate("current.sets[0]=[{w:50,r:5,done:false},{w:60,r:3,done:false},{w:70,r:1,done:false}];renderWorkout()")
    await pg.tap(W(0));await pg.wait_for_timeout(120);await pg.keyboard.type('55')
    ok('пирамида: другие веса не перезаписаны',await pg.evaluate("current.sets[0].map(s=>s.w).join()")=='55,60,70')
    ok('выделение работает и в питании/других числовых полях',await pg.evaluate("(()=>{const i=document.createElement('input');i.inputMode='decimal';i.value='150';document.body.appendChild(i);i.focus();const r=i.selectionStart===0&&i.selectionEnd===3;i.remove();return r})()"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
