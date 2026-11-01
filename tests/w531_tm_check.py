# 5/3/1 «Батя в здании»: ТМ на следующий цикл — разгрузка не влияет, неотмеченный последний подход → вопрос
# «не смог / не делал», движение без данных — ТМ без изменений, один срыв — откат; веса из блинов и не легче грифа;
# сверка этапа подготовки с датой старта.
# Запуск: python3 tests/w531_tm_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools,datetime
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
HELP="""(()=>{window.T={
 mk(o){localStorage.removeItem(W5K);const v=w5Store();const c=Object.assign({id:"c1",createdAt:"x",updatedAt:"x",start:localDate(),n:1,phase:"classic",days:4,variant:"v1",assist:"bbb",inc:"std",warm:true,step:2.5,
   tm:{press:40,dead:140,bench:90,squat:120},rm1:{},recs:[],closedAt:null,completedAt:null},o||{});v.cycles=[c];v.activeId="c1";w5Save(v);return c;},
 /* f(lift,wave,lastSet) → повторы в последнем подходе; null — подход не отмечен */
 cycle(f){const S=w5Sessions(w5Active());for(let i=0;i<S.length;i++)T.one(i,f);return w5Suggest(w5Active());},
 one(i,f){const p=w5Build(w5Active(),i);current={program:p,sets:p.preset.map(ss=>ss.map(s=>Object.assign({},s))),startedAt:new Date().toISOString()};
   p.w5.rows.forEach((R,k)=>{if(!R.main)return;const st=current.sets[k],wk=st.filter(s=>!s.warm&&s.need&&!s.drop);st.forEach(s=>{s.done=true;});const last=wk[wk.length-1],x=f(R.lift,p.w5.wave,last);
     if(x===null){last.done=false;last.r=0;}else last.r=x;});const r=w5Record();current=null;return r;},
 good(l,w,s){return s.need+(s.amrap?2:0);}};})()"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'");await pg.evaluate(HELP)
    E=pg.evaluate
    # ---- разгрузка не влияет
    r=await E("T.mk();T.cycle((l,w,s)=>w===4&&l==='squat'?4:T.good(l,w,s)).squat")
    ok('разгрузка 4 из 5 → присед растёт по правилам (120 → 125)',r['tm']==125,r)
    # ---- один срыв — откат
    r=await E("T.mk();T.cycle((l,w,s)=>w===3&&l==='bench'?0:T.good(l,w,s)).bench")
    ok('срыв нормы (неделя 3) → откат жима к 90% расч. 1ПМ',r['tm']<90 and 'откат' in r['why'],r)
    # ---- неотмеченный подход → вопрос; «не делал» → без изменений
    await E("T.mk();for(let i=0;i<10;i++)T.one(i,T.good)")
    rec=await E("T.one(10,(l,w,s)=>l==='bench'?null:T.good(l,w,s))")
    ok('неотмеченный последний подход: «нет данных», не срыв',rec['lifts']['bench'].get('unk') and not rec['lifts']['bench']['ok'],rec['lifts']['bench'])
    await E("show('w531');renderW5()")
    ok('на экране программы просьба ответить',await E("!!el('w5Unk')"))
    await E("el('w5Unk').click()")
    ok('вопрос «Не смог / Не делал»',await E("!el('gvtModal').hidden&&el('gvtMbox').textContent.includes('Не смог')&&el('gvtMbox').textContent.includes('Не делал')"))
    await E("el('gvtMbox').querySelector('[data-o=skip]').click()")
    r=await E("(()=>{for(let i=11;i<16;i++)T.one(i,T.good);return w5Suggest(w5Active()).bench})()")
    ok('«не делал» → подход не учитывается, жим растёт по остальным неделям (90 → 92,5)',r['tm']==92.5,r)
    # «не смог» с числом повторов → срыв
    await E("T.mk();for(let i=0;i<10;i++)T.one(i,T.good)")
    rec=await E("T.one(10,(l,w,s)=>l==='bench'?null:T.good(l,w,s))")
    await E("w5AskUnk('"+rec['uid']+"');el('w5u_bench').value='0';el('gvtMbox').querySelector('[data-o=fail]').click()")
    r=await E("(()=>{for(let i=11;i<16;i++)T.one(i,T.good);return w5Suggest(w5Active()).bench})()")
    ok('«не смог» → срыв → откат',r['tm']<90 and 'откат' in r['why'],r)
    # ---- движение без записей
    r=await E("(()=>{T.mk();for(let i=0;i<3;i++)T.one(i,T.good);return w5Suggest(w5Active()).squat})()")
    ok('присед не делали → ТМ без изменений с причиной',r['tm']==120 and 'не тренировалось' in r['why'],r)
    # ---- веса из блинов, не легче грифа
    r=await E("(()=>{const c=T.mk({step:1,tm:{press:40,dead:143,bench:93,squat:121}});const all=[];w5Sessions(c).forEach((_,i)=>w5Build(c,i).preset.forEach((ss,k)=>{if(w5Build(c,i).w5.rows[k].main)ss.forEach(s=>all.push(s.w));}));return all})()")
    bad=[w for w in r if w<20 or abs(((w-20)/2)/1.25-round(((w-20)/2)/1.25))>1e-6]
    ok('все веса основных движений собираются из блинов и не легче грифа 20 кг',not bad,bad[:6])
    ok('в форме нет «Округление 1 кг»',await E("(()=>{w5Form='new';renderW5();const t=el('w5Body').textContent;w5Form=null;return !t.includes('1 кг')&&t.includes('блин')})()"))
    # ---- этап и дата старта
    async def start(weeks,ph):
      d=(datetime.date.today()+datetime.timedelta(days=weeks*7-2)).isoformat()
      await E(f"""(()=>{{localStorage.removeItem(W5K);const v=w5Store();v.meet={{date:'{d}',goal:{{squat:150,bench:110,dead:180}},updatedAt:w5Now()}};w5Save(v);w5Form='new';renderW5();
        ['press','dead','bench','squat'].forEach((l,i)=>el('w5In_'+l).value=[60,160,100,140][i]);el('w5Phase').value='{ph}';w5FormPhase();window.__t=[];const _t=toast;toast=m=>{{__t.push(m);}};el('w5Go').click();toast=_t;}})()""")
      return await E("({started:!!w5Active(),msg:__t.join(' | ')})")
    r=await start(3,'meetprep')
    ok('подводка за 3 недели до старта → предупреждение, не начата',not r['started'] and 'тренировочную неделю' in r['msg'],r)
    r=await start(4,'meetprep')
    ok('подводка за 4 недели → без предупреждения',r['started'],r)
    r=await start(3,'premeet')
    ok('предсоревновательный за 3 недели → предупреждение',not r['started'] and 'подводки' in r['msg'],r)
    r=await start(7,'premeet')
    ok('предсоревновательный за 7 недель → без предупреждения',r['started'],r)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
