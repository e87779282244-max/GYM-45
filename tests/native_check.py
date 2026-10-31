# Нативная оболочка (Capacitor, подменённая): уведомление о конце отдыха, напоминания по дням, KeepAwake; в браузере — ничего не меняется.
# Запуск: python3 tests/native_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
MOCK="""window.__n={sched:[],cancel:[],awake:[]};window.firebase={};window.Capacitor={isNativePlatform:()=>true,Plugins:{
  LocalNotifications:{checkPermissions:async()=>({display:'prompt'}),requestPermissions:async()=>({display:'granted'}),schedule:async o=>{__n.sched.push(...o.notifications)},cancel:async o=>{__n.cancel.push(...o.notifications.map(x=>x.id))}},
  KeepAwake:{keepAwake:async()=>__n.awake.push(1),allowSleep:async()=>__n.awake.push(0)}}};"""
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context();await ctx.add_init_script(MOCK);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route("**/*gstatic*",lambda r:r.abort());
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';coolOffer=function(){}")
    ok('в приложении включается режим «натив»',await pg.evaluate("natOn()"))
    await pg.evaluate("startWorkout({name:'Т',focus:'т',sec:'body',ex:[['Жим штанги лёжа',3,'8',80]]},false);el('dayStart').click()");await pg.wait_for_timeout(200)
    await pg.evaluate("document.querySelectorAll('#exList .chk')[0].click()");await pg.wait_for_timeout(400)
    s=await pg.evaluate("__n.sched.filter(x=>x.id===9001)")
    ok('отдых → уведомление на время конца отдыха',len(s)==1 and 'Отдых окончен' in s[0]['title'] and abs(await pg.evaluate("new Date(__n.sched.find(x=>x.id===9001).schedule.at).getTime()-restEnd"))<5,s)
    await pg.evaluate("el('wkRestSkip').click()");await pg.wait_for_timeout(200)
    ok('пропуск отдыха → уведомление отменено',await pg.evaluate("__n.cancel.includes(9001)"))
    await pg.wait_for_timeout(3300)
    ok('во время тренировки — KeepAwake',await pg.evaluate("__n.awake.includes(1)"))
    await pg.evaluate("clearDraft();current=null;show('home');renderToday();el('tdCal').click()");await pg.wait_for_timeout(100)
    ok('в календаре — «Напоминать в приложении»',await pg.evaluate("!!el('calN')"))
    await pg.evaluate("localStorage.setItem('gym45_cal_v1',JSON.stringify({days:['MO','TH'],time:'07:15',dur:60,rem:30}));el('calN').click()");await pg.wait_for_timeout(300)
    r=await pg.evaluate("__n.sched.filter(x=>x.id>9100).map(x=>[x.id,x.schedule.on])")
    ok('напоминания: Пн и Чт в 6:45',sorted(r)==sorted([[9102,{'weekday':2,'hour':6,'minute':45}],[9105,{'weekday':5,'hour':6,'minute':45}]]),r)
    await pg.wait_for_timeout(3300)
    ok('после тренировки экран может гаснуть',await pg.evaluate("__n.awake[__n.awake.length-1]===0"))
    ok('без ошибок JS',not errs,errs[:3])
    # браузер: ничего не планируется
    ctx2=await b.new_context();pg2=await ctx2.new_page();await pg2.goto(URL);await pg2.wait_for_timeout(300)
    ok('в браузере натив выключен',await pg2.evaluate("!natOn()&&typeof Capacitor==='undefined'"))
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
