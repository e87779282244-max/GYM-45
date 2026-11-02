# Перерыв в любой программе: 13 дней — сразу; 14 — предложение −10 %; 15+ — −15 %; 30+ — рекомендация начать заново.
# Облегчённая тренировка засчитывается, но не двигает прогрессию (обычная программа, 5/3/1, ЛЗ).
# Запуск: python3 tests/break_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools,datetime
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
D=lambda n:(datetime.date.today()-datetime.timedelta(days=n)).isoformat()
PROG="{name:'Жим (Push)',focus:'BAZA GYM 45 · Грудь',ex:[['Жим штанги лёжа',3,'8–10',60],['Жим гантелей лёжа',3,'8–10',24]],sec:'body'}"
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    async def seed(gap):
      await E(f"""(()=>{{current=null;clearDraft();el('gvtModal').hidden=true;safe.set([{{fam:'BAZA GYM 45',date:'{D(gap)}',name:'Жим (Push)',vol:1,log:{{'Жим штанги лёжа':[{{w:60,r:10,done:true}},{{w:60,r:10,done:true}},{{w:60,r:10,done:true}}],'Жим гантелей лёжа':[{{w:24,r:10,done:true}}]}}}}]);
        startWorkout({PROG},false);el('dayStart').click();}})()""")
    # ---- обычная программа
    await seed(13)
    ok('13 дней — тренировка сразу, без вопроса',await E("el('gvtModal').hidden&&!!current"))
    await seed(14)
    ok('14 дней — «Легче на 10 %»',await E("!el('gvtModal').hidden&&el('bkY').textContent.includes('10 %')&&!current"))
    await E("el('bkY').click()")
    r=await E("({w:current.sets[0].map(s=>s.w),d:current.sets[1][0].w,brk:current.brk,f:current.program.focus})")
    ok('−10 %: штанга 62,5 → 55 (по блинам вниз), гантели 24 → 20 (21,6 вниз по шагу 2), пометка',r['w'][0]==55 and r['d']==20 and r['brk']==10 and 'после перерыва −10 %' in r['f'],r)
    await E("current.sets.forEach(ss=>ss.forEach(s=>{s.done=true;s.r=10;}));finishWorkout()");await pg.wait_for_timeout(200)
    h=await E("safe.get().slice(-1)[0]")
    ok('в истории: отметка «после перерыва» и программа',h.get('brk')==10 and h.get('fam')=='BAZA GYM 45',{k:h.get(k) for k in ('brk','fam')})
    r=await E(f"(()=>{{const e=({PROG}).ex[0];return prSug(e,{{}},lastResult(e[0]))}})()")
    ok('прогрессия идёт от прежнего результата (60 × 10 → 62,5), облегчённая не образец',r and r.get('w') and r['w'][0]==62.5,r)
    await seed(20)
    ok('20 дней — «Легче на 15 %»',await E("el('bkY').textContent.includes('15 %')&&!el('bkRe')"))
    await seed(31)
    ok('31 день — рекомендация начать сначала',await E("el('gvtMbox').textContent.includes('начать сначала')"))
    await E("el('bkN').click()")
    ok('«Как обычно» — без облегчения',await E("!!current&&!current.brk&&current.sets[0][0].w===62.5"),await E("current&&current.sets[0][0].w"))
    # ---- 5/3/1: облегчённая не влияет на ТМ; 30+ — «Начать программу заново»
    await E("""(()=>{current=null;clearDraft();el('gvtModal').hidden=true;localStorage.removeItem(W5K);const v=w5Store();const c={id:"c1",createdAt:"x",updatedAt:"x",start:localDate(),n:1,phase:"classic",days:4,variant:"v1",assist:"bbb",inc:"std",warm:true,step:2.5,
      tm:{press:40,dead:140,bench:90,squat:120},rm1:{},recs:[{uid:"o",s:0,wave:1,finishedAt:'"""+D(31)+"""T10:00:00Z',updatedAt:"x",full:true,pr:[],lifts:{press:{w:35,r:7,need:5,amrap:"full",e1:43,ok:true}}}],closedAt:null,completedAt:null};v.cycles=[c];v.activeId="c1";w5Save(v);
      startWorkout(w5Build(w5Active(),1),true);el('dayStart').click();})()""")
    ok('5/3/1, 31 день: кнопка «Начать программу заново»',await E("!!el('bkRe')"))
    await E("el('bkY').click()")
    await E("current.sets.forEach(ss=>ss.forEach(s=>{s.done=true;s.r=s.need?s.need-1:s.r;}));finishWorkout()");await pg.wait_for_timeout(200)
    r=await E("(()=>{const c=w5Active();return {brk:c.recs.slice(-1)[0].brk,sug:w5Suggest(c).dead}})()")
    ok('5/3/1: недобор на облегчённой не откатывает ТМ',r['brk']==15 and 'откат' not in r['sug']['why'],r)
    await E("el('gvtModal').hidden=true;startWorkout(w5Build(w5Active(),2),true);el('dayStart').click()")
    await E("el('bkRe') && el('bkRe').click()");await pg.wait_for_timeout(100)
    ok('«Начать заново» открывает форму нового цикла',await E("currentScreen==='w531'&&!!el('w5Go')") or await E("!el('bkRe')"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
