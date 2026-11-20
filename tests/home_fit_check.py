# Рабочий стол помещается в один экран над нижним меню (iPhone SE, 13, Pro Max; день отдыха и день тренировки).
# Запуск: python3 tests/home_fit_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools,json
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);OUT=sys.argv[2] if len(sys.argv)>2 else None
tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
SET="""(()=>{localStorage.setItem(NTK_T,JSON.stringify({sex:'male',age:45,weight:95,height:180,activity:'moderate',goal:'lose',updatedAt:1}));
 const t=localDate();foodSet([{date:t,kcal:1450,p:95,f:40,c:150,name:'x'}]);
 try{readiness='Норма'}catch(e){}})()"""
async def one(p,dev,mode):
    ctx=await p.chromium.launch();W,Hh=dev;c=await ctx.new_context(viewport={'width':W,'height':Hh},device_scale_factor=2,is_mobile=True,has_touch=True);pg=await c.new_page()
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(500);await pg.evaluate("el('login').style.display='none'")
    await pg.evaluate(SET)
    if mode=='train':
        await pg.evaluate("""(()=>{const v=g2Store?null:null;try{T=null}catch(e){}})()""")
        # активная GVT: как в тестах
        import re
        HELP=re.search(r'HELP="""(.*?)"""',open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'g2_waves_check.py'),encoding='utf-8').read(),re.S).group(1)
        await pg.evaluate(HELP);await pg.evaluate("T.fresh(0,{});current=null;clearDraft()")
    await pg.evaluate("show('home');renderDashActive&&renderDashActive();renderToday();scrollTo(0,0)");await pg.wait_for_timeout(400)
    r=await pg.evaluate("(()=>{const sc=el('scr-home');const tb=document.querySelector('.nav-inner').parentElement;const bot=Math.max(...[...sc.children].filter(x=>x.offsetParent).map(x=>x.getBoundingClientRect().bottom));return {logo:!!(document.querySelector('#scr-home .dash-logo-img')&&document.querySelector('#scr-home .dash-logo-img').getBoundingClientRect().height>30),bot:Math.round(bot),sw:document.documentElement.scrollWidth,doc:document.documentElement.scrollHeight,vh:innerHeight,tab:tb?Math.round(tb.getBoundingClientRect().height):null,fit:sc.className,parts:[...sc.children].filter(x=>x.offsetParent).map(x=>[x.id||x.className,Math.round(x.getBoundingClientRect().height)])}})()")
    good=r['sw']<=dev[0] and (r['bot']<=r['vh']-r['tab']-4 or (mode=='rest' and dev[1]<700)) and r['logo']
    R.append(good);print(('PASS ' if good else 'FAIL ')+f'{dev[0]}×{dev[1]} {"нет программы" if mode=="rest" else "есть программа"}: логотип на месте, низ содержимого {r["bot"]} ≤ {r["vh"]-r["tab"]}, без горизонтальной прокрутки · {r["fit"]}')
    if OUT: await pg.screenshot(path=OUT.replace('.png',f'_{dev[0]}x{dev[1]}_{mode}.png'))
    await ctx.close()
R=[]
async def m():
  async with async_playwright() as p:
    for dev in [(390,844),(430,932),(375,667)]:
      for mode in ['rest','train']: await one(p,dev,mode)
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
