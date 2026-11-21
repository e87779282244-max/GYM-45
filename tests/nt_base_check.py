# Питание: большой справочник USDA на русском (офлайн) + местная кухня; поиск, меры, скорость.
# Запуск: python3 tests/nt_base_check.py index.html
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(**p.devices['iPhone 13']);pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/index.html');await pg.wait_for_timeout(500);await pg.evaluate("el('login').style.display='none'")
    E=pg.evaluate
    n=await E("[ntAllFoods().length,ntAllFoods().filter(f=>f.usda).length,new Set(ntAllFoods().map(f=>f.id)).size===ntAllFoods().length,new Set(ntAllFoods().map(f=>ntNorm(f.name))).size===ntAllFoods().length]")
    ok('в справочнике больше 2 000 продуктов, из них 1 500+ USDA на русском, id и названия уникальны',n[0]>2000 and n[1]>1500 and n[2] and n[3],n)
    ok('КБЖУ сходятся с ккал (Б·4+Ж·9+У·4 ≈ ккал) у 95%+',await E("(()=>{const a=ntAllFoods().filter(f=>f.usda);const g=a.filter(f=>Math.abs(f.p*4+f.f*9+f.c*4-f.kcal)<=Math.max(25,f.kcal*.15));return g.length/a.length>.95})()"))
    t=await E("(()=>{const t0=performance.now();for(let i=0;i<20;i++){el('ntQ').value='кур';ntSearch();}return (performance.now()-t0)/20})()")
    ok('поиск быстрый (< 60 мс)',t<60,round(t,1) if False else t)
    await E("FOOD_DAY=null;renderFood();show('food');ntTab('diary')")
    async def hits(q):
      await pg.fill('#ntQ',q);await pg.wait_for_timeout(120);return await E("[...el('ntHits').querySelectorAll('.nt-hit span')].map(s=>s.textContent)")
    h=await hits('лосось');ok('«лосось»: найдено несколько видов',len([x for x in h if 'осось' in x or 'Сёмга' in x])>=2,h[:6])
    h=await hits('горбуша');ok('«горбуша» есть',any(x.startswith('Горбуша') for x in h),h[:4])
    h=await hits('говядина фарш');ok('«говядина фарш»: варианты по жирности',sum('% жира' in x for x in h)>=3,h[:6])
    h=await hits('ашлянфу');ok('ашлянфу — местная кухня',h and h[0]=='Ашлянфу',h)
    h=await hits('куурдак');ok('куурдак находится и в другом написании (Куырдак)',any('Куырдак' in x for x in h),h)
    h=await hits('боорсок');ok('боорсок',any('Боорсок' in x for x in h),h)
    await E("[...el('ntHits').querySelectorAll('.nt-hit')].find(b=>b.textContent.startsWith('Боорсок')).click()");await pg.wait_for_timeout(80)
    ok('у местных блюд — меры с граммами',await E("el('ntQUnit').options[0].text")=='Штука · 20 г')
    h=await hits('клубника');await E("[...el('ntHits').querySelectorAll('.nt-hit')].find(b=>/^Клубника, сырая/.test(b.textContent)).click()");await pg.wait_for_timeout(80)
    u=await E("[...el('ntQUnit').options].map(o=>o.text)")
    ok('USDA: бытовые меры из базы (клубника: чашка, крупная/средняя ягода)',any('Средний (шт.) · 12 г' in x for x in u) and any('Чашка' in x for x in u),u)
    ok('источник указан: USDA FoodData Central',await E("el('ntPickRes').textContent.includes('USDA FoodData Central')"))
    h=await hits('яйцо');ok('свои продукты выше USDA (яйцо из справочника Gym 45 — первым)',h and not h[0].startswith('Яйцо,'),h[:5])
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
