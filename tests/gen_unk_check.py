# Общий движок (обычные и авторские программы): неотмеченный подход → «Не смог / Не делал».
# «Не делал» — прибавка по отмеченным подходам; «Не смог» — вес тот же; ответ не теряется при синхронизации.
# Запуск: python3 tests/gen_unk_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
PROG="{name:'Жим (Push)',focus:'BAZA GYM 45 · Грудь',ex:[['Жим штанги лёжа',3,'8–10',60],['Отжимания',3,15,0]],sec:'body'}"
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    async def train(marks):
      # marks: список повторов для жима (None — не отмечен)
      await E(f"""(m=>{{current=null;clearDraft();el('gvtModal').hidden=true;startWorkout({PROG},false);el('dayStart').click();
        current.sets[0].forEach((s,j)=>{{if(s.warm){{s.done=true;return;}}const x=m[j];if(x==null)s.done=false;else{{s.done=true;s.r=x;s.w=60;}}}});current.sets[1].forEach(s=>s.done=true);finishWorkout();}})""",marks)
      await pg.wait_for_timeout(600)
    await E("safe.set([])")
    await train([10,10,None])
    ok('после тренировки — вопрос «Не смог / Не делал» по жиму',await E("!el('gvtModal').hidden&&el('gvtMbox').textContent.includes('Жим штанги лёжа')&&!!el('gvtMbox').querySelector('[data-o=skip]')"))
    ok('упражнение без веса (отжимания) не спрашивается',await E("!el('gvtMbox').textContent.includes('Отжимания')"))
    await E("el('guX').click();show('home');renderToday()")
    ok('«Позже» → на главной «Не все подходы отмечены» и «Ответить»',await E("!!el('guGo')"))
    r=await E(f"(()=>{{const e=({PROG}).ex[0];return prSug(e,{{}},lastResult(e[0]))}})()")
    ok('пока не ответил — вес тот же, с подсказкой',r and not r.get('up') and 'не все подходы' in r['why'],r)
    await E("el('guGo').click();el('gvtMbox').querySelector('[data-o=skip]').click()")
    r=await E(f"(()=>{{const e=({PROG}).ex[0];return prSug(e,{{}},lastResult(e[0]))}})()")
    ok('«Не делал»: 10/10 по отмеченным → +2,5 (62,5)',r and r.get('up') and r['w'][0]==62.5,r)
    ok('вопрос и строка на главной пропали',await E("(()=>{renderToday();return el('gvtModal').hidden&&!el('guGo')})()"))
    # «Не смог»
    await E("safe.set([])");await train([10,10,None])
    await E("el('gvtMbox').querySelector('[data-o=fail]').click()")
    r=await E(f"(()=>{{const e=({PROG}).ex[0];return prSug(e,{{}},lastResult(e[0]))}})()")
    ok('«Не смог»: вес тот же',r and not r.get('up'),r)
    # всё отмечено — вопроса нет
    await E("safe.set([])");await train([10,10,10])
    ok('все подходы отмечены — вопроса нет',await E("el('gvtModal').hidden&&!safe.get().slice(-1)[0].unk"))
    # синхронизация: ответ на одном устройстве не теряется при слиянии
    r=await E("""(()=>{const h={date:'2026-11-01',name:'X',vol:1,log:{A:[{w:60,r:10,done:true},{w:60,r:0,done:false}]},unk:['A']};const cloud=[JSON.parse(JSON.stringify(h))];
      const local=[Object.assign(JSON.parse(JSON.stringify(h)),{skipEx:{A:true}})];delete local[0].unk;const M=mergeHistory(local,cloud),N=mergeHistory(cloud,local);
      return [M.length,!M[0].unk,!!(M[0].skipEx&&M[0].skipEx.A),N.length,!N[0].unk]})()""")
    ok('слияние с облаком: одна запись, ответ «не делал» сохранён (оба направления)',r==[1,True,True,1,True],r)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
