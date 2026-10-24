# Круги и суперсеты: автопереход A1 → A2 → A3 → отдых → снова A1.
# Запуск: python3 tests/circuit_check.py index.html [папка_скриншотов]
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
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'");await pg.wait_for_timeout(100)
    # распознавание групп
    g=await pg.evaluate("""(()=>{const st=d=>{current={program:{ex:d.ex},sets:d.ex.map(e=>[])};const r=[];for(let i=0;i<d.ex.length;i++){const g=wkGroup(i);r.push(g?g.join('-'):'');}current=null;return r.join(',');};
      const fst=AUTH.find(p=>p.id==='fst7').weeks[4].days, jp=AUTH.find(p=>p.id==='jpcm').weeks[0].days;
      return {trx1:st(TRX_PROGS[0].days[0]),trx2:st(TRX_PROGS[0].days[1]),trx8:st(TRX_PROGS[0].days[7]),hero4:st(TRX_PROGS[1].days[3]),fstChest:st(fst[0]),fstLegsA:st(fst[1]),
        jpClusters:jp.every(d=>d.ex.every((e,i)=>{current={program:{ex:d.ex}};const r=!wkGroup(i)||/сразу|→/.test(e[5]||'');current=null;return r;})),body:st(BODY[0].days[0])};})()""")
    ok('TRX 1: круг из 3',g['trx1']=='0-2,0-2,0-2',g['trx1'])
    ok('TRX 2: два круга A(3) и B(2)',g['trx2']=='0-2,0-2,0-2,3-4,3-4',g['trx2'])
    ok('TRX 8 (300 повторов): без кругов',g['trx8'].strip(',')=='',g['trx8'])
    ok('HERO 4: три круга по 3 (пауза 8 с)',g['hero4']=='0-2,0-2,0-2,3-5,3-5,3-5,6-8,6-8,6-8',g['hero4'])
    ok('FST-7 фаза 2, грудь: суперсет 1+2, дальше одиночные',g['fstChest'].startswith('0-1,0-1,,,'),g['fstChest'])
    ok('FST-7 ноги А: трисет 1+2+3',g['fstLegsA'].startswith('0-2,0-2,0-2,,'),g['fstLegsA'])
    ok('кластеры Completely Massive — не круги',g['jpClusters'])
    ok('базовые программы — без кругов',g['body'].strip(',')=='',g['body'])
    # прохождение круга TRX 1
    await pg.evaluate("show('trx');renderTrx();el('trxProgs').querySelector('.disc').click()");await pg.wait_for_timeout(100)
    await pg.evaluate("el('bodyDays').querySelectorAll('.disc')[0].click()");await pg.wait_for_timeout(100)
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(150)
    ok('метка круга на карточке',await pg.evaluate("!!document.querySelector('.wk-circ')&&document.querySelector('.wk-circ').textContent.includes('1 из 5')"),await pg.evaluate("document.querySelector('.wk-circ')&&document.querySelector('.wk-circ').textContent"))
    if SHOT:await pg.screenshot(path=SHOT+'/circ-1.png')
    click="el('exList').querySelector('.set-row.cur .chk').click()"
    await pg.evaluate(click);await pg.wait_for_timeout(500)
    ok('A1 отмечен → сразу A2, без отдыха',await pg.evaluate("current.idx===1&&el('wkRest').hidden"))
    await pg.evaluate(click);await pg.wait_for_timeout(500)
    ok('A2 отмечен → сразу A3',await pg.evaluate("current.idx===2&&el('wkRest').hidden"))
    await pg.evaluate(click);await pg.wait_for_timeout(200)
    ok('A3 отмечен → отдых 30 с после круга',await pg.evaluate("!el('wkRest').hidden&&restTotal===30"))
    await pg.evaluate("restDone()");await pg.wait_for_timeout(200)
    ok('после отдыха → снова A1, второй подход',await pg.evaluate("current.idx===0&&current.sets[0][0].done&&!current.sets[0][1].done&&el('exList').querySelectorAll('.set-row.cur').length===1"))
    ok('метка: круг 2 из 5',await pg.evaluate("document.querySelector('.wk-circ').textContent.includes('2 из 5')"))
    if SHOT:await pg.screenshot(path=SHOT+'/circ-2.png')
    for _ in range(4):
      for k in range(3):
        await pg.evaluate(click);await pg.wait_for_timeout(450 if k<2 else 150)
      if await pg.evaluate("!el('wkRest').hidden"):await pg.evaluate("restDone()");await pg.wait_for_timeout(150)
    ok('все 5 кругов → окно «Тренировка завершена»',await pg.evaluate("wkAllSetsDone()&&!el('gvtModal').hidden&&el('gvtMbox').textContent.includes('Тренировка завершена')"))
    await pg.evaluate("el('wkDoneGo').click()");await pg.wait_for_timeout(150)
    # суперсет FST-7 → после последнего круга обычный переход к следующему упражнению
    await pg.evaluate("authSetWeek(AUTH.find(p=>p.id==='fst7'),4);authOpen(AUTH.find(p=>p.id==='fst7'))");await pg.wait_for_timeout(100)
    await pg.evaluate("el('bodyDays').querySelectorAll('.disc')[0].click()");await pg.wait_for_timeout(100)
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(150)
    await pg.evaluate("current.sets[0].forEach((s,j)=>{if(j<3)s.done=true});current.sets[1].forEach((s,j)=>{if(j<3)s.done=true});saveDraft();goEx(0)");await pg.wait_for_timeout(100)
    await pg.evaluate(click);await pg.wait_for_timeout(500)
    ok('суперсет: последний подход 1-го → 2-е',await pg.evaluate("current.idx===1"))
    await pg.evaluate(click);await pg.wait_for_timeout(200)
    ok('суперсет закрыт → обычный отдых и переход к 3-му',await pg.evaluate("!el('wkRest').hidden"))
    await pg.evaluate("restDone()");await pg.wait_for_timeout(200)
    ok('после отдыха — 3-е упражнение',await pg.evaluate("current.idx===2"))
    ok('без горизонтальной прокрутки',await pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f'\n{sum(R)}/{len(R)} PASS');sys.exit(0 if all(R) else 1)
asyncio.run(m())
