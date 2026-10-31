# 1ПМ из теста стритлифтинга: обновляется и при снижении (рекорд в аналитике остаётся), хранит дату и источник;
# подтягивания и брусья везде считаются через полную нагрузку с массой тела из профиля.
# Запуск: python3 tests/rm_bw_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
# проходка ЛЗ: test — {lift:вес}
TEST="""(test=>{const P=lzActive(),st=lzState(P);startWorkout(lzPlan(P,st,"dtest"),true);el('dayStart').click();
  current.program.lz.rows.forEach((R,i)=>{const ws=current.sets[i].filter(s=>!s.warm);current.sets[i].forEach(s=>s.done=!!s.warm);
    if(R.test){const t=test[R.lift];if(t){ws[0].w=t;ws[0].done=true;}}});
  finishWorkout();return current==null;})"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    today=await E("gvtDD(localDate())")

    # ---- первый вес в программе 5×5 (стритлифтинг): масса тела из профиля
    await E("pfWrite(Object.assign({},pfRaw()||{},{weight:90}));rmPut('Подтягивания с весом',30,'Тест ЛЗ')")
    r=await E("(()=>{const e=STREET_PROGS[1].days[0].ex[0];return [e[0],prSug(e,{},null)]})()")
    ok('5×5: 1ПМ +30 при массе 90 → первый доп. вес 2,5 (а не 22,5)',r[0]=='Подтягивания с весом' and r[1]['w'][0]==2.5,r[1])
    ok('в подсказке источник и дата 1ПМ',f'Тест ЛЗ · {today}' in r[1]['why'] and 'массе тела 90' in r[1]['why'],r[1]['why'])
    await E("pfWrite(Object.assign({},pfRaw()||{},{weight:''}))")
    r=await E("prSug(STREET_PROGS[1].days[0].ex[0],{},null)")
    ok('без массы тела в профиле — напоминание, вес не подставлен',r.get('first') and 'массу тела' in r['why'],r)
    await E("pfWrite(Object.assign({},pfRaw()||{},{weight:90}))")

    # ---- GVT 2.0: масса тела из профиля, если в программе не указана
    r=await E("""(()=>{const P=g2New({stage:4});return [g2Bw(P),g2Load(P,'pull',10),g2Suggest(P,4,'pull')]})()""")
    ok('GVT 2.0 без массы в программе берёт из профиля (90)',r[0]==90 and r[1]==100,r[:2])
    ok('GVT 2.0: подсказка из 1ПМ +30 → 10ПМ доп. 0 (120/1,333=90 − 90) и источник',r[2] and r[2]['w']==0 and 'Тест ЛЗ' in r[2]['txt'],r[2])
    r=await E("(()=>{const P=g2New({stage:4,bw:80});return g2Bw(P)})()")
    ok('масса, указанная в программе, важнее профиля',r==80,r)

    # ---- тест ЛЗ: рост и снижение
    await E("document.querySelector('.disc[data-disc=\"Стритлифтинг\"]').click()");await pg.wait_for_timeout(100)
    await E("[...el('streetDays').querySelectorAll('.disc')].find(b=>b.textContent.includes('Рождённый ползать')).click()");await pg.wait_for_timeout(100)
    await pg.fill('#lzRm_pull','20');await pg.fill('#lzRm_dip','30');await pg.click('#lzGo');await pg.wait_for_timeout(100)
    await E(TEST+"({dip:40,pull:27.5})")
    r=await E("[rmReg()['Отжимания на брусьях с весом'],rmReg()['Подтягивания с весом'],rmMeta()['Подтягивания с весом'].src]")
    ok('тест ЛЗ с ростом: 1ПМ 40 / 27,5, источник «Тест ЛЗ»',r==[40,27.5,'Тест ЛЗ'],r)
    await E(TEST+"({dip:35,pull:25})")
    r=await E("[rmReg()['Отжимания на брусьях с весом'],rmReg()['Подтягивания с весом']]")
    ok('тест ЛЗ ниже прежнего: 1ПМ обновлён до 35 / 25 (текущая форма)',r==[35,25],r)
    r=await E("(()=>{const st=lzState(lzActive());return [st.lifts.dip.rm,st.lifts.pull.rm]})()")
    ok('ЛЗ считает рабочие веса от нового 1ПМ',r==[35,25],r)
    ok('тест без отметок не стирает 1ПМ',await E("(()=>{const before=rmReg()['Подтягивания с весом'];"+TEST+"({});return rmReg()['Подтягивания с весом']===before})()"))

    # ---- ручное изменение в «Рабочих весах» тоже помечается
    await E("rmPut('Жим лёжа',100,'вручную')")
    ok('ручной ввод: источник «вручную» и дата',await E("rmMeta()['Жим лёжа'].src==='вручную'&&!!rmMeta()['Жим лёжа'].at"))

    # ---- синхронизация: побеждает более свежий 1ПМ по дате
    r=await E("""(async()=>{localStorage.setItem(RMK,JSON.stringify({"Подтягивания с весом":25}));localStorage.setItem(RMMK,JSON.stringify({"Подтягивания с весом":{at:"2026-10-01T00:00:00Z",src:"Тест ЛЗ"}}));
      const cloud={rm:{"Подтягивания с весом":20},rmMeta:{"Подтягивания с весом":{at:"2026-10-30T00:00:00Z",src:"Тест ЛЗ"}}};
      const doc={get:async()=>({exists:true,data:()=>cloud}),set:async()=>{}};CLOUD={db:{doc:()=>doc},user:{}};await cloudInit();CLOUD=null;cloudReady=false;
      return [rmReg()["Подтягивания с весом"],rmMeta()["Подтягивания с весом"].at]})()""")
    ok('облако: более свежий тест (20 от 30.10) заменяет старый 25 от 01.10',r[0]==20 and r[1].startswith('2026-10-30'),r)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
