# «Тяжёлая артиллерия»: подсобка помнит вес; после круга — предложение обновить 1ПМ (только рост, по подтверждению);
# «Пропустить день» не сдвигает неделю; гантельный вариант с шагом 2, штанга по блинам и не легче грифа.
# Запуск: python3 tests/cj_fix_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
HELP="""(()=>{window.T={
 mk(rm){localStorage.removeItem(CJK);localStorage.removeItem(KEY);const v=cjStore();const P={id:"c1",createdAt:"x",updatedAt:"x",start:localDate(),cfg:{rm:rm||{sq:140,bp:100,dl:180}},recs:[]};v.progs=[P];v.activeId="c1";cjSave(v);},
 /* провести следующий день: me — вес для попыток (null — как предложено), acc — вес подсобки, если поле пустое */
 day(me,acc){const P=cjActive(),st=cjState(P);startWorkout(cjPlan(P,st),true);current=null;el('dayStart').click();const p=current.program;
   current.sets.forEach((ss,i)=>ss.forEach(s=>{s.done=true;if(p.cj.rows[i].me&&!s.warm&&me!=null)s.w=me;if(!p.cj.rows[i].me&&p.ex[i][3]===null&&!(s.w>0)&&acc)s.w=acc;}));
   const out={kind:p.cj.kind,ex:p.ex.map((e,i)=>({n:e[0],w:current.sets[i].map(s=>s.w),tgt:e[7]}))};finishWorkout();el('gvtModal').hidden=true;return out;}};})()"""
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none'");await pg.evaluate(HELP)
    E=pg.evaluate
    # ---- подсобка помнит вес
    await E("T.mk()")
    d1=await E("T.day(null,30)")
    await E("T.day(null,30);T.day(null,30);T.day(null,30)")
    d5=await E("T.day(null,null)")
    acc=[x for x in d5['ex'] if x['n']=='Гиперэкстензия']
    ok('подсобка: вес прошлой тренировки подставлен (30) и подпись «в прошлый раз»',acc and acc[0]['w'][0]==30 and 'в прошлый раз 30' in acc[0]['tgt'],acc)
    # ---- пропуск дня не сдвигает неделю
    await E("T.mk();T.day(null,30);T.day(null,30);T.day(null,30);show('cj');renderCj()")
    ok('кнопка «Пропустить …»',await E("!!el('cjSkip')&&el('cjSkip').textContent.includes('Сб')"))
    await E("el('cjSkip').click();el('cjSkip').click()")
    r=await E("(()=>{const st=cjState(cjActive());return [st.next,st.week]})()")
    ok('пропуск субботы → следующий день: Пн максимум (низ) новой недели',r==['mel',2],r)
    # ---- гантельный вариант и штанга по блинам
    r=await E("""(()=>{T.mk({sq:140,bp:100,dl:180});const st=cjState(cjActive());st.set=0;st.week=4;const p=cjPlan(cjActive(),st,'meu');return {n:p.ex[0][0],w:p.preset[0].map(s=>s.w)}})()""")
    ok('«Жим гантелей лёжа»: все веса кратны 2',r['n']=='Жим гантелей лёжа' and all(abs(w/2-round(w/2))<1e-9 for w in r['w']),r)
    ok('попытки гантелей: ориентир и +2',r['w'][-1]-r['w'][-2]==2,r['w'][-2:])
    r=await E("""(()=>{T.mk({sq:60,bp:45,dl:80});const all=[];['mel','meu','del','deu'].forEach(k=>{const st=cjState(cjActive());const p=cjPlan(cjActive(),st,k);p.cj.rows.forEach((R,i)=>{if(R.me||(k==='del'&&i<2)||(k==='deu'&&i<1))p.preset[i].forEach(s=>{if(!/гантел/i.test(p.ex[i][0]))all.push(s.w)});});});return all})()""")
    bad=[w for w in r if w<20 or abs(((w-20)/2)/1.25-round(((w-20)/2)/1.25))>1e-6]
    ok('штанга: все веса из блинов и не легче грифа 20 кг',not bad,bad[:6])
    # ---- обновление 1ПМ после круга
    await E("T.mk({sq:140,bp:100,dl:180})")
    # круг: 24 тренировки; в дни максимума выкладываем 160 кг (для приседа/тяги) и 110 (для жима)
    await E("(()=>{for(let i=0;i<24;i++)T.day(null,30);})()")  # в каждом варианте — ориентир и +2,5
    await E("show('cj');renderCj()")
    t=await E("el('cjBody').textContent")
    ok('после 6 недель — «Круг 1 завершён · 1ПМ» с расчётом',('Круг 1 завершён' in t) and ('→' in t),t[:200])
    S=await E("cjRmSug(cjActive(),1)")
    ok('оценка: 1ПМ растёт, но не больше +10 % за круг',all(S[k]['up'] and S[k]['nw']<=S[k]['cur']*1.1 for k in S),{k:(S[k]['cur'],S[k]['nw']) for k in S})
    fs=await E("(()=>{const S=cjRmSug(cjActive(),1);return Object.values(S).map(o=>o.src?cjVarF(o.src.n).f:1)})()")
    ok('варианты с малым коэффициентом (наклоны, гантели, фронтальный) не участвуют',all(f>=0.8 for f in fs),fs)
    await E("el('cjRmY').click()")
    r=await E("(()=>{const P=cjActive();return {rm:P.cfg.rm,card:el('cjBody').textContent.includes('Круг 1 завершён'),speed:cjPlan(P,cjState(P),'del').preset[0][0].w}})()")
    ok('«Обновить»: 1ПМ применён, карточка исчезла, скоростной день от нового 1ПМ',r['rm']['sq']==S['sq']['nw'] and not r['card'] and r['speed']==await E(f"w5Bar({S['sq']['nw']}*0.75)"),r)
    # рекорды ниже → без изменений
    await E("T.mk({sq:300,bp:250,dl:350});for(let i=0;i<24;i++)T.day(50,30);show('cj');renderCj()")
    r=await E("(()=>{const S=cjRmSug(cjActive(),1);return [S.sq.up,S.bp.up,S.dl.up,!!el('cjRmY'),el('cjBody').textContent.includes('без изменений')]})()")
    ok('рекорды ниже 1ПМ — без изменений, кнопки «Обновить» нет',r==[False,False,False,False,True],r)
    await E("el('cjRmN').click()")
    ok('«Понятно» — карточка закрыта и не появляется снова',await E("(()=>{renderCj();return !el('cjBody').textContent.includes('Круг 1 завершён')})()"))
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
