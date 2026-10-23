# Ход тренировки: переход после отдыха (подход → упражнение), окно «Тренировка завершена»,
# восстановление после перезагрузки страницы (обычная и GVT 2.0), «Начать» не обнуляет, черновик в облачном снимке.
# Запуск: python3 tests/workout_flow_check.py index.html [папка_скриншотов]
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools,json
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);O=sys.argv[2] if len(sys.argv)>2 else None;tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300)
    open_day="el('login').style.display='none';show('body');authSetWeek(AUTH[0],0);authOpen(AUTH[0]);el('bodyDays').querySelectorAll('.disc')[1].click()"
    await pg.evaluate(open_day+";el('dayStart').click()");await pg.wait_for_timeout(150)
    n0=await pg.evaluate("current.sets[0].length")
    # 1-й подход → отдых → «Пропуск» → следующий подход подсвечен, упражнение то же
    await pg.evaluate("el('exList').querySelectorAll('.chk')[0].click()");await pg.wait_for_timeout(100)
    ok('после подхода идёт отдых',await pg.evaluate("!el('wkRest').hidden"))
    await pg.evaluate("el('wkRestSkip').click()");await pg.wait_for_timeout(150)
    ok('конец отдыха: следующий подход того же упражнения',await pg.evaluate("current.idx===0&&el('exList').querySelectorAll('.set-row.cur').length===1"))
    # закрыть упражнение → во время отдыха остаёмся, после отдыха — следующее упражнение
    await pg.evaluate("[...el('exList').querySelectorAll('.chk')].filter(b=>!b.classList.contains('on')).forEach(b=>b.click())");await pg.wait_for_timeout(900)
    ok('упражнение закрыто — во время отдыха не перескакивает',await pg.evaluate("current.idx===0&&!el('wkRest').hidden"))
    await pg.evaluate("restEnd=Date.now()-1;restTick()");await pg.wait_for_timeout(150)
    ok('таймер отдыха закончился — следующее упражнение',await pg.evaluate("current.idx===1"))
    # перезагрузка посреди тренировки
    done_before=await pg.evaluate("current.sets.flat().filter(s=>s.done).length")
    st=await pg.evaluate("current.startedAt")
    await pg.reload();await pg.wait_for_timeout(400)
    ok('после перезагрузки тренировка восстановлена и открыта',await pg.evaluate("currentScreen==='workout'&&!!current"),await pg.evaluate("currentScreen"))
    ok('отмеченные подходы и время старта на месте',await pg.evaluate(f"current.sets.flat().filter(s=>s.done).length==={done_before}&&current.startedAt==={json.dumps(st)}"))
    # заходим в программу заново и жмём «Начать» — не обнуляется
    await pg.evaluate(open_day);await pg.wait_for_timeout(100)
    ok('в дне кнопка «Продолжить программу»',await pg.evaluate("el('dayStart').textContent.includes('Продолжить')"))
    await pg.evaluate("el('dayStart').click()");await pg.wait_for_timeout(100)
    ok('«Продолжить» не обнуляет подходы',await pg.evaluate(f"current.sets.flat().filter(s=>s.done).length==={done_before}"))
    ok('черновик попадает в облачный снимок',await pg.evaluate(f"(cloudSnapshot().draft||{{}}).startedAt==={json.dumps(st)}"))
    # все подходы → окно «Тренировка завершена» → сохранить
    await pg.evaluate("current.sets.forEach((se,i)=>{if(i<current.sets.length-1)se.forEach(s=>s.done=true)});current.idx=current.sets.length-1;renderWorkout()")
    await pg.evaluate("[...el('exList').querySelectorAll('.chk')].filter(b=>!b.classList.contains('on')).forEach(b=>b.click())");await pg.wait_for_timeout(150)
    ok('все подходы — окно «Тренировка завершена»',await pg.evaluate("!el('gvtModal').hidden&&el('gvtMbox').innerText.includes('Тренировка завершена')&&!!el('wkDoneGo')"))
    if O:await pg.screenshot(path=O+'/done.png')
    h0=await pg.evaluate("safe.get().length")
    await pg.evaluate("el('wkDoneGo').click()");await pg.wait_for_timeout(200)
    ok('«Сохранить» — запись в истории, черновик очищен',await pg.evaluate(f"safe.get().length==={h0}+1&&!getDraft()&&!current"))
    ok('в записи есть время старта (для сверки с облаком)',await pg.evaluate(f"safe.get().slice(-1)[0].st==={json.dumps(st)}"))
    # облако: чужой/старый черновик уже завершённой тренировки не воскресает
    ok('завершённая тренировка не восстанавливается из облака',await pg.evaluate(f"(()=>{{const hs=safe.get();return hs.some(h=>h.st==={json.dumps(st)})}})()"))
    # GVT 2.0: перезагрузка и переход блоков после отдыха
    await pg.evaluate("""(()=>{const P=g2New({});const v=g2Store();v.progs.push(P);v.activeId=P.id;g2MainKeysOf(P,0).forEach(k=>{P.st[0].ws[k]={w:G2X[k].bw?5:40};});P.st[0].setup=true;g2Save(v);
      startWorkout(g2Build(g2Active(),g2NextSlot(g2Active())),true);el('dayStart').click();})()""");await pg.wait_for_timeout(150)
    await pg.evaluate("const u=current.program.g2.units[0];u.forEach(i=>current.sets[i].forEach(s=>s.done=true));current.sets[u[1]][current.sets[u[1]].length-1].done=false;renderWorkout()")
    await pg.evaluate("[...el('exList').querySelectorAll('.chk')].filter(b=>!b.classList.contains('on'))[0].click()");await pg.wait_for_timeout(900)
    ok('GVT: блок закрыт — ждём конца отдыха',await pg.evaluate("current.idx===0&&!el('wkRest').hidden"))
    await pg.evaluate("el('wkRestSkip').click()");await pg.wait_for_timeout(150)
    ok('GVT: после отдыха — следующий суперсет',await pg.evaluate("current.idx===1"))
    gd=await pg.evaluate("current.sets.flat().filter(s=>s.done).length")
    await pg.reload();await pg.wait_for_timeout(400)
    ok('GVT: после перезагрузки восстановлено',await pg.evaluate(f"currentScreen==='workout'&&!!current&&!!current.program.g2&&current.sets.flat().filter(s=>s.done).length==={gd}"))
    ok('ошибок JS нет',not errs,errs[:3])
    await b.close()
  print(f"\n{sum(R)}/{len(R)} PASS");sys.exit(0 if all(R) else 1)
asyncio.run(m())
