# Проверка обновления: данные, созданные СТАРОЙ версией, должны пережить переход на НОВУЮ байт в байт.
# Запуск: python3 upgrade_check.py OLD.html NEW.html
import asyncio,json,os,sys,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
OLD,NEW=sys.argv[1],sys.argv[2]
tmp=tempfile.mkdtemp();shutil.copy(OLD,tmp+'/old.html');shutil.copy(NEW,tmp+'/new.html');os.symlink(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','media'),tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();BASE=f'http://127.0.0.1:{srv.server_address[1]}/'
R=[]
def ok(n,c,x=''):R.append(c);print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
DUMP="JSON.stringify(Object.fromEntries(Object.keys(localStorage).filter(k=>k.startsWith('gym45_')&&k!=='gym45_safety_v1').sort().map(k=>[k,localStorage.getItem(k)])))"
async def gvt_sets(pg,limit):
  n=0
  for k in range(limit):
    r=await pg.evaluate("(()=>{const x=[...el('scr-workout').querySelectorAll('.chk')].find(x=>x.offsetParent&&!x.classList.contains('on'));if(!x)return 0;x.click();return 1})()")
    if not r:break
    n+=1;await pg.evaluate("!el('wkRest').hidden&&el('wkRestSkip').click()")
  return n
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    # ---------- СТАРАЯ версия: тренируемся ----------
    await pg.goto(BASE+'old.html');await pg.wait_for_timeout(400);await pg.evaluate("el('login').style.display='none'")
    await pg.evaluate("show('gvt');g2Render()");await pg.fill('#g2Bw','85');await pg.evaluate("el('g2Go').click()");await pg.wait_for_timeout(150)
    for k,v in [('dDecl','24'),('squat','80'),('lcurl','30'),('dips','0'),('hammer','14'),('pull','0')]:await pg.fill('#g2w_'+k,v)
    await pg.evaluate("el('g2SetGo').click()");await pg.wait_for_timeout(120)
    await pg.evaluate("el('g2Open').click()");await pg.wait_for_timeout(150);await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(150)
    for i in range(6):
      await gvt_sets(pg,80);await pg.wait_for_timeout(900);await gvt_sets(pg,80);await pg.evaluate("el('wkNext').click()");await pg.wait_for_timeout(300)
      if await pg.evaluate("currentScreen")!='workout':break
    # закрываем решение по весу, если открыто
    await pg.evaluate("show('gvt');g2Render()");await pg.wait_for_timeout(100)
    # вторая тренировка — НЕ завершаем: 7 подходов, меняем вес и повторы
    await pg.evaluate("el('g2Open').click()");await pg.wait_for_timeout(150);await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(150)
    await gvt_sets(pg,7)
    await pg.evaluate("(()=>{const i=[...el('scr-workout').querySelectorAll('input')].find(x=>x.offsetParent);i.value='27,5';i.dispatchEvent(new Event('input',{bubbles:true}));})()")
    mid=json.loads(await pg.evaluate("JSON.stringify(current.sets.map(s=>s.filter(x=>x.done).length))"))
    # прочие данные
    await pg.evaluate("""(()=>{const h=safe.get();h.push({date:localDate(),name:'Жим лёжа 5×5',vol:4000,log:{'Жим лёжа':[{w:100,r:5,done:true},{w:100,r:5,done:true}]}});safe.set(h);
      const f=foodGet();f.push({id:'t1',date:localDate(),name:'Гречка',kcal:500,p:20,f:8,c:90});foodSet(f);
      if(typeof cfGet==='function'){const c=cfGet();c.res.push({id:'r1',wod:'fran',name:'Fran',v:'rx',sex:'m',sc:'time',t:400,date:localDate(),ts:Date.now(),pr:true});cfSave(c);}
      const s=skGet();s.start=localDate();skSave(s);})()""")
    before=json.loads(await pg.evaluate(DUMP));hist_before=await pg.evaluate("safe.get().length")
    ok('старая версия: создано разделов данных',len(before)>=6,len(before))
    # ---------- НОВАЯ версия (обновление посреди тренировки) ----------
    await pg.goto(BASE+'new.html');await pg.wait_for_timeout(500);await pg.evaluate("el('login').style.display='none'")
    after=json.loads(await pg.evaluate(DUMP))
    changed=[k for k in before if after.get(k)!=before[k]]
    ok('все данные старой версии на месте байт в байт',not changed,changed)
    ok('новые ключи только служебные',all(k in before or k in ('gym45_safety_v1',) for k in after),[k for k in after if k not in before])
    snap=await pg.evaluate("(()=>{try{const s=JSON.parse(localStorage.getItem('gym45_safety_v1'));return s.snaps.length}catch(e){return -1}})()")
    ok('автоснимок сделан при запуске',snap>=1 if await pg.evaluate("typeof DS_K!=='undefined'") else True,snap)
    await pg.evaluate("show('home')");await pg.wait_for_timeout(100)
    ok('незавершённая тренировка: есть «Продолжить»',await pg.evaluate("!el('draftBanner').hidden"))
    await pg.evaluate("el('draftResume').click()");await pg.wait_for_timeout(150)
    now=json.loads(await pg.evaluate("JSON.stringify(current.sets.map(s=>s.filter(x=>x.done).length))"))
    ok('продолжена с тех же подходов',now==mid,(mid,now))
    ok('изменённый вес 27,5 сохранился',await pg.evaluate("current.sets.some(s=>s.some(x=>x.w===27.5))"))
    for i in range(6):
      await gvt_sets(pg,80);await pg.wait_for_timeout(900);await gvt_sets(pg,80);await pg.evaluate("el('wkNext').click()");await pg.wait_for_timeout(300)
      if await pg.evaluate("currentScreen")!='workout':break
    ok('вторая тренировка GVT завершена в новой версии',await pg.evaluate("g2Active().recs.filter(r=>r.kind==='train').length===2"))
    ok('история: +1 тренировка, старые не тронуты',await pg.evaluate("safe.get().length")==hist_before+1)
    await pg.evaluate("show('progress')");await pg.wait_for_timeout(150)
    ok('«Прогресс» открывается',await pg.evaluate("currentScreen==='progress'&&el('hist').children.length>0"))
    if await pg.evaluate("!!el('dsBox')"):
      ok('карточка «Сохранность данных» показана',await pg.evaluate("el('dsBox').textContent.includes('Сохранить копию в файл')"))
      # «ошибочное обновление» портит историю → откат к снимку
      good=await pg.evaluate("localStorage.getItem('gym45_history_v1')")
      # следующий запуск: снимок фиксирует актуальные данные ДО кода новой версии; затем «ошибочный код» портит историю
      await pg.reload();await pg.wait_for_timeout(500)
      await pg.evaluate("localStorage.setItem('gym45_history_v1','[]');location.reload()");await pg.wait_for_timeout(600)
      await pg.evaluate("el('login').style.display='none';show('progress')");await pg.wait_for_timeout(150)
      await pg.evaluate("document.querySelector('.ds-snaps').open=true;const b=[...document.querySelectorAll('.ds-snap button')][1];b.click();b.click()");await pg.wait_for_timeout(1500)
      ok('откат к снимку вернул историю',await pg.evaluate("localStorage.getItem('gym45_history_v1')")==good)
      need=[k for k in before if k!='gym45_draft_v1' and not k.startswith('gym45_backup')]
      have=json.loads(await pg.evaluate("JSON.stringify(Object.keys(dsAll()))"))
      ok('копия в файл: все разделы данных (черновик завершён — его нет)',all(k in have for k in need),[k for k in need if k not in have])
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f'\n{sum(R)}/{len(R)} PASS');sys.exit(0 if all(R) else 1)
asyncio.run(m())
