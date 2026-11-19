# Стритлифтинг 5×5 по нарастающей: подходы 1–4 = 40/55/70/85 % от X (вниз до 1,25 кг), 5-й — X × 5 (A) или X + 2,5 × 3 (B).
# X: после A — её 5-й подход; после B — 5-й подход, если всё сделано, иначе прежний X.
# Запуск: python3 tests/slpyr_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
FIND="""(()=>{const seen=new Set(),out=[];const walk=(o,d)=>{if(!o||typeof o!=='object'||seen.has(o)||d>8)return;seen.add(o);
  if(Array.isArray(o.days))o.days.forEach(dd=>{if(dd&&dd.ex&&dd.ex.some(e=>Array.isArray(e)&&slPyrOf(e)))out.push({p:o,d:dd});});
  (Array.isArray(o)?o:Object.values(o)).forEach(x=>walk(x,d+1));};
  [typeof EXT_PROGS!=='undefined'?EXT_PROGS:null,typeof STREET_PROGS!=='undefined'?STREET_PROGS:null,typeof BP_BEG!=='undefined'?BP_BEG:null,typeof AU_EXTRA!=='undefined'?AU_EXTRA:null].forEach(x=>walk(x,0));
  window.__SL=out;return out.map(x=>x.d.name)})()"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(400);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    days=await E(FIND)
    ok('найдены дни 5×5 по нарастающей (сессии A и B)',any('сессия A' in d for d in days) and any('сессия B' in d for d in days),days)
    async def start(sess):
      return await E(f"""(()=>{{readiness='Норма';const x=__SL.find(q=>q.d.name.includes('подтягивания · сессия {sess}'));const d=Object.assign({{}},x.d,{{sec:'street'}});current=null;clearDraft();
        startWorkout(d,false);el('dayStart').click();const s=current.sets[0];return [s.map(z=>z.w),s.map(z=>z.r),current.program.ex[0][0]]}})()""")
    async def fin(reps):
      await E(f"(()=>{{const R={reps};current.sets[0].forEach((s,j)=>{{s.done=true;s.r=R[j];}});current.sets.slice(1).forEach(ss=>ss.forEach(s=>s.done=true));finishWorkout();}})()")
    await E("safe.set([])")
    r=await start('A')
    ok('первая тренировка A: X = 10 (по программе) → 3,75 / 5 / 6,25 / 7,5 / 10, все по 5',r[0]==[3.75,5,6.25,7.5,10] and r[1]==[5]*5,r)
    await fin([5,5,5,5,5])
    r=await start('B')
    ok('сессия B после A: X = 10 → 4 подхода пирамиды и 5-й 3 × 12,5',r[0]==[3.75,5,6.25,7.5,12.5] and r[1]==[5,5,5,5,3],r)
    await fin([5,5,5,5,3])
    r=await start('A')
    ok('B сделана полностью → X = 12,5: 5 / 6,25 / 8,75 / 10,625↓10 / 12,5',r[0]==[5,6.25,8.75,10,12.5],r)
    await E("current=null;clearDraft()")
    # B не добрал → X прежний
    await E("safe.set([])");await start('B');await fin([5,5,5,5,2])
    r=await start('A')
    ok('B не добрал (2 из 3) → X прежний 10',r[0][-1]==10,r)
    await E("current=null;clearDraft()")
    # предпросмотр дня
    r=await E("(()=>{const x=__SL.find(q=>q.d.name.includes('подтягивания · сессия B'));dayView={p:x.d,computed:false};return planOf(x.d.ex[0],x.d).w})()")
    ok('экран дня показывает всю пирамиду точно (3,75 — не 3,8)',r.count('→')==4 and '3,75' in r,r)
    # «не закрыт план» не срабатывает на 3 повт. в 5-м подходе сессии B
    await E("safe.set([])");await start('B');await fin([5,5,5,5,3])
    ok('B 5-5-5-5-3 — без совета «не закрыт план»',not ('Не закрыт план' in (await E("window.__coachPending||''"))))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
