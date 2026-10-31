# GVT: прибавка доп. веса (брусья, подтягивания) — шаг 2,5 кг, а не округление общей нагрузки; починка старых нерешённых предложений.
# Запуск: python3 tests/g2bw_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    prog="(k,w)=>{const P=g2New({bw:96,step:2,stepDb:2});const rec={dec:[]};g2Progress(P,0,{key:k,main:true,sets:Array.from({length:10},()=>({done:true,r:10,w:w,pr:10}))},rec);return {w:P.st[0].ws[k].w,d:rec.dec.map(d=>d.type+':'+d.txt)};}"
    r=await pg.evaluate(f"({prog})('dips',15)")
    ok('брусья 15 кг доп. → 17,5 без лишнего подтверждения',r['w']==17.5 and r['d'][0].startswith('inc:'),r)
    r=await pg.evaluate(f"({prog})('pull',0)")
    ok('подтягивания без веса → +2,5 кг',r['w']==2.5,r)
    r=await pg.evaluate(f"({prog})('bench',60)")
    ok('штанга: +5 % → ближайший собираемый из блинов вес вверх (63 → 65, просит подтвердить)',r['d'][0].startswith('inc_confirm') and '65 кг' in r['d'][0],r)
    ok('волны: доп. вес кратен 2,5',await pg.evaluate("(()=>{const P=g2New({bw:96});const w=g2FromLoad(P,'dips',(96+15)*1.065);return w%2.5===0})()"))
    # старое нерешённое «22 кг» превращается в 17,5
    await pg.evaluate("""(()=>{const v=g2Store();const P=g2New({bw:96,step:2,stepDb:2});P.recs.push({uid:'r1',stage:0,variant:'B',status:'full',setsDone:100,setsPlanned:100,ton:16300,durMin:61,
      dec:[{key:'dips',type:'inc_confirm',cur:15,sug:22,pct:6.3,txt:'Отжимания на брусьях: 10×10 выполнено. Ближайший доступный вес 22 кг доп.'}]});P.st[0].ws.dips={w:15};v.progs.push(P);v.activeId=P.id;g2Save(v);g2Summary('r1');})()""")
    ok('старое предложение исправлено на 17,5',await pg.evaluate("el('gvtMbox').textContent.includes('Подтвердить 17,5 кг доп.')&&!el('gvtMbox').textContent.includes('22 кг')"))
    await pg.evaluate("el('gvtMbox').querySelector('[data-o=yes]').click()");await pg.wait_for_timeout(100)
    ok('подтверждение ставит 17,5',await pg.evaluate("g2Store().progs.slice(-1)[0].st[0].ws.dips.w===17.5"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
