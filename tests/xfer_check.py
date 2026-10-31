# Перенос данных между версиями: сводка и фото в файле, предпросмотр «Объединить / Заменить», без потерь и дублей,
# автосверка после перезапуска, старые копии без сводки, откат к снимку без «переноса».
# Два независимых браузера: «старая» версия (откуда) и «новая» (куда).
# Запуск: python3 tests/xfer_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools,json
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
PNG="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
SEED="""(async()=>{const h=[];for(let i=0;i<5;i++)h.push({date:"2026-10-0"+(i+1),name:"Тренировка "+i,vol:1000+i,log:{}});localStorage.setItem(KEY,JSON.stringify(h));
  const v={progs:[],activeId:null};const P=g2New({stage:0});P.recs=[{uid:"g1",stage:0,kind:"train",updatedAt:"a",finishedAt:"a",ex:[],dec:[]},{uid:"g2",stage:0,kind:"train",updatedAt:"b",finishedAt:"b",ex:[],dec:[]}];v.progs.push(P);v.activeId=P.id;localStorage.setItem(G2K,JSON.stringify(v));
  localStorage.setItem(FOODK,JSON.stringify([{id:1,name:"Гречка",date:"2026-10-01"},{id:2,name:"Курица",date:"2026-10-01"}]));
  rmPut("Жим лёжа",100,"вручную");pfWrite({weight:90,name:"Я"});
  const bin=atob('"""+PNG+"""'),u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);const blob=new Blob([u],{type:"image/png"});
  await phIdbPut("ph-a",blob);phSet([{id:"ph-a",date:"2026-10-01",at:"x",kind:"idb"},{id:"ph-b",date:"2026-10-02",at:"y",kind:"asset",url:"data:image/png;base64,"""+PNG+"""",ref:"r1"}]);
  return true;})()"""
async def fresh(b):
  ctx=await b.new_context();pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'");return ctx,pg,errs
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    # ---- источник: готовим данные и файл копии
    ca,A,ea=await fresh(b)
    await A.evaluate(SEED)
    pack=await A.evaluate("dsPack()")
    ok('в файле сводка по разделам',pack['format']==2 and pack['sum']['Тренировки в истории']==5 and pack['sum']['German Volume Training · записи']==2 and pack['sum']['1ПМ в «Рабочих весах»']==1,pack['sum'])
    ok('в файле оба фото (с устройства и из хранилища по ссылке)',sorted(x['id'] for x in pack['photos'])==['ph-a','ph-b'] and all(x['b64'] for x in pack['photos']))

    # ---- приёмник: свои записи, которых нет в файле
    cb,B,eb=await fresh(b)
    await B.evaluate("""(()=>{localStorage.setItem(KEY,JSON.stringify([{date:"2026-10-20",name:"Только тут",vol:5,log:{}}]));localStorage.setItem(FOODK,JSON.stringify([{id:9,name:"Творог",date:"2026-10-20"}]));})()""")
    await B.evaluate("p=>dsPreview(p,'тест')",pack)
    txt=await B.evaluate("el('gvtMbox').textContent")
    ok('предпросмотр: в файле / на устройстве',('Тренировки в истории' in txt) and ('5' in txt) and ('Объединить' in txt) and ('Заменить' in txt),txt[:200])
    await B.evaluate("el('dsMerge').click()");await B.wait_for_timeout(1500);await B.wait_for_load_state();await B.wait_for_timeout(500)
    await B.evaluate("el('login').style.display='none'")
    r=await B.evaluate("""(async()=>{const h=JSON.parse(localStorage.getItem(KEY)),f=JSON.parse(localStorage.getItem(FOODK)),P=g2Store().progs[0],ph=phMeta();
      const imgs=await Promise.all(ph.map(x=>phIdbGet(x.id)));return {h:h.length,only:h.some(x=>x.name==="Только тут"),f:f.length,g:P.recs.length,rm:rmReg()["Жим лёжа"],src:(rmMeta()["Жим лёжа"]||{}).src,
      w:pfGet().weight,ph:ph.map(x=>x.kind).sort(),img:imgs.every(Boolean),snap:dsSnaps().some(s=>s.build==="перед объединением")}})()""")
    ok('объединение: 5 + 1 тренировка, своя запись на месте',r['h']==6 and r['only'],r)
    ok('объединение: питание 2 + 1, GVT 2 записи, 1ПМ с источником, профиль',r['f']==3 and r['g']==2 and r['rm']==100 and r['src']=='вручную' and r['w']==90,r)
    ok('фото перенесены на устройство и открываются',r['ph']==['idb','idb'] and r['img'],r)
    ok('перед объединением сделан снимок',r['snap'])
    chk=await B.evaluate("(()=>{const c=dsCheck();return {ok:c.ok,rows:c.rows.filter(x=>!x.ok)}})()")
    ok('автосверка: всё на месте ✓',chk['ok'],chk)
    await B.evaluate("show('progress')");await B.wait_for_timeout(200)
    ok('итог сверки виден в «Сохранности данных»','Перенос проверен' in await B.evaluate("el('dsBox').textContent"))

    # ---- повторный перенос того же файла — без дублей
    await B.evaluate("p=>dsApply(p,'merge','повтор')",pack);await B.wait_for_timeout(1500);await B.wait_for_load_state();await B.wait_for_timeout(500)
    r=await B.evaluate("[JSON.parse(localStorage.getItem(KEY)).length,JSON.parse(localStorage.getItem(FOODK)).length,g2Store().progs[0].recs.length,phMeta().length]")
    ok('повторный перенос: ни одного дубля',r==[6,3,2,2],r)

    # ---- «Заменить»
    await B.evaluate("p=>dsApply(p,'replace','замена')",pack);await B.wait_for_timeout(1500);await B.wait_for_load_state();await B.wait_for_timeout(500)
    r=await B.evaluate("[JSON.parse(localStorage.getItem(KEY)).length,JSON.parse(localStorage.getItem(FOODK)).length,dsCheck().ok,phMeta().map(x=>x.kind).sort().join()]")
    ok('замена: ровно данные файла, сверка ✓, фото с устройства',r==[5,2,True,'idb,idb'],r)

    # ---- старая копия (без сводки и фото)
    old={"app":"Gym 45","format":1,"at":"2026-10-01T00:00:00Z","data":pack['data']}
    cc,C,ec=await fresh(b)
    await C.evaluate("p=>dsPreview(p,'старая')",old)
    ok('старая копия: предпросмотр работает','Тренировки в истории' in await C.evaluate("el('gvtMbox').textContent"))
    await C.evaluate("el('dsMerge').click()");await C.wait_for_timeout(1500);await C.wait_for_load_state();await C.wait_for_timeout(500)
    r=await C.evaluate("(()=>{const c=dsCheck();return [JSON.parse(localStorage.getItem(KEY)).length,c.ok,c.x.file['Фото прогресса']]})()")
    ok('старая копия: перенос и сверка по содержимому (фото не ждём)',r==[5,True,0],r)

    # ---- откат к снимку — без записи «переноса»
    await C.evaluate("localStorage.removeItem(DS_XK)")
    await C.evaluate("(()=>{const s=dsSnaps().slice(-1)[0];dsRestore(s.data,'снимок')})()");await C.wait_for_timeout(1500);await C.wait_for_load_state();await C.wait_for_timeout(300)
    ok('откат к снимку не записывает перенос',await C.evaluate("localStorage.getItem(DS_XK)===null"))
    ok('без ошибок JS',not (ea+eb+ec),(ea+eb+ec)[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
