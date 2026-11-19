# GVT: перерыв считается и по дню этапа (А/Б/В) — первое занятие каждого дня после перерыва легче;
# «Устал» в GVT — веса −10 % на одно занятие, прогрессия этапа не меняется.
# Запуск: python3 tests/g2_brkday_check.py index.html
import asyncio,sys,os,re,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
HELP=re.search(r'HELP="""(.*?)"""',open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'g2_waves_check.py'),encoding='utf-8').read(),re.S).group(1)
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(400);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate;await E(HELP)
    # три занятия А, Б, В; затем перерыв: А и В — 19 и 18 дней назад, Б — 2 дня назад (первое после перерыва, уже с −15 %)
    r=await E("""(()=>{readiness='Норма';T.fresh(0,{});const out=[];for(let i=0;i<3;i++){const x=T.run([]);out.push(x?x.day:null);}
      const v=g2Store(),P=v.progs[0],tr=P.recs.filter(r=>r.kind==='train');
      tr[0].date=addDays(localDate(),-19);tr[2].date=addDays(localDate(),-18);tr[1].date=addDays(localDate(),-2);tr[1].brk=15;g2Save(v);return out})()""")
    ok('три занятия записаны (А, Б, В)',r==[0,1,2],r)
    # следующее — А: последний раз 19 дней назад, хотя программа была 2 дня назад
    r=await E("(()=>{T.open();const m=el('gvtModal');return [!m.hidden&&!!el('g2BrkY'),el('gvtMbox').textContent]})()")
    ok('А после перерыва: предлагает «Легче на 15 %», хотя Б было 2 дня назад',r[0] and 'Легче на 15 %' in r[1] and 'первое занятие дня' in r[1],r[1][:160])
    r=await E("""(()=>{const P=g2Active(),sl=g2NextSlot(P),plain=g2Build(P,sl);el('g2BrkY').click();T.begin();
      const w=current.program;return [w.focus.includes('после перерыва −15 %'),w.g2.brk,plain.preset.map((ss,i)=>[ss[0].w,current.sets[i][0].w])]})()""")
    ok('веса снижены, занятие помечено как после перерыва (прогрессия не меняется)',r[0] and r[1]==15 and all(a==0 or c<a for a,c in r[2]),r)
    await E("current=null;clearDraft()")
    # «Устал» без перерыва
    r=await E("""(()=>{readiness='Норма';T.fresh(0,{});T.run([]);const P=g2Active(),sl=g2NextSlot(P),plain=g2Build(P,sl);
      readiness='Устал';T.open();const w=current.program;
      return [el('gvtModal').hidden,w.focus.includes('устал −10 %'),w.g2.brk,plain.preset.map((ss,i)=>[ss[0].w,current.sets[i][0].w])]})()""")
    ok('«Устал» без перерыва: без вопроса, веса ≈ −10 % (вниз по шагу), пометка на занятии',r[0] and r[1] and r[2]==10 and all(a==0 or (c<a and c>=a*0.85) for a,c in r[3]),r)
    r=await E("(()=>{const rec=T.finish([]);readiness='Норма';const P=g2Active();return [rec&&rec.brk,P.recs.filter(r=>r.kind==='train').length]})()")
    ok('занятие «Устал» записано с пометкой — рабочие веса этапа не меняет',r[0]==10 and r[1]==2,r)
    r=await E("(()=>{readiness='Норма';T.fresh(0,{});T.run([]);T.open();return [el('gvtModal').hidden,!current.program.g2.brk]})()")
    ok('«Норма» и без перерыва — как обычно',r==[True,True],r)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
