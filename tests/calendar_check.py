# Напоминания в календарь: ссылка Google с повтором по дням, файл .ics с напоминанием (вне Claude).
# Запуск: python3 tests/calendar_check.py index.html
import datetime
import asyncio,sys,os,shutil,tempfile,http.server,threading,functools,urllib.parse
from playwright.async_api import async_playwright
H=os.path.abspath(sys.argv[1]);tmp=tempfile.mkdtemp();shutil.copy(H,tmp+'/index.html');os.symlink(os.path.dirname(H)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp));threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();ctx=await b.new_context(timezone_id='Asia/Aqtobe',viewport={'width':390,'height':844});pg=await ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto(URL);await pg.wait_for_timeout(300);await pg.evaluate("el('login').style.display='none';show('home');renderToday()")
    ok('на главной — «Напоминания в календарь»',await pg.evaluate("!!el('tdCal')"))
    await pg.evaluate("el('tdCal').click()");await pg.wait_for_timeout(100)
    ok('по умолчанию Пн Ср Пт, 18:00',await pg.evaluate("[...document.querySelectorAll('.cal-days .on')].map(b=>b.dataset.k).join()==='MO,WE,FR'&&el('calT').value==='18:00'"))
    await pg.evaluate("document.querySelector('.cal-days [data-k=TU]').click()")
    await pg.fill('#calT','07:30');await pg.evaluate("el('calT').dispatchEvent(new Event('input'))")
    href=await pg.evaluate("el('calG').href");q=urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
    ok('ссылка Google: повтор, время, часовой пояс',href.startswith('https://calendar.google.com/calendar/render') and q['recur'][0]=='RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,FR' and q['dates'][0][9:13]=='0730' and q['ctz'][0]=='Asia/Aqtobe' and q['action'][0]=='TEMPLATE',q)
    ics=await pg.evaluate("calIcs(calCfg())")
    ok('файл .ics: повтор и напоминание за 30 мин','RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,FR' in ics and 'TRIGGER:-PT30M' in ics and 'DTSTART:' in ics and ics.startswith('BEGIN:VCALENDAR'))
    ok('настройки запомнены',await pg.evaluate("calCfg().time==='07:30'&&calCfg().days.length===4"))
    # спецрежим: через N дней отдыха, без привязки к дням недели
    await pg.evaluate("document.querySelector('#calMode [data-m=rest]').click()")
    ok('спецрежим: дни недели скрыты, видны «дни отдыха» и дата',await pg.evaluate("el('calWk').hidden&&!el('calRs').hidden&&!!el('calS').value"))
    d0=(datetime.date.today()+datetime.timedelta(days=1)).isoformat()
    await pg.fill('#calS',d0);await pg.evaluate("el('calS').dispatchEvent(new Event('change'));document.querySelector('#calRest [data-r=\"2\"]').click()")
    href=await pg.evaluate("el('calG').href");q=urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
    ok('Google: каждые 3 дня с выбранной даты (2 дня отдыха)',q['recur'][0]=='RRULE:FREQ=DAILY;INTERVAL=3' and q['dates'][0][:8]==d0.replace('-',''),q)
    ics=await pg.evaluate("calIcs(calCfg())")
    ok('.ics: тот же повтор и напоминание','RRULE:FREQ=DAILY;INTERVAL=3' in ics and 'DTSTART:'+d0.replace('-','') in ics and 'TRIGGER:-PT30M' in ics)
    pv=await pg.evaluate("el('calPv').textContent")
    dates=[datetime.date.today()+datetime.timedelta(days=1+3*k) for k in range(3)]
    ok('превью: даты ровно через 3 дня, в любой день недели',all(str(x.day) in pv for x in dates) and 'каждые 3 дня' in await pg.evaluate("el('calNote').textContent"),pv)
    await pg.evaluate("document.querySelector('#calRest [data-r=\"1\"]').click()")
    ok('1 день отдыха → каждые 2 дня',await pg.evaluate("calRule(calCfg())")=='RRULE:FREQ=DAILY;INTERVAL=2')
    await pg.evaluate("document.querySelector('#calRest [data-r=\"3\"]').click()")
    ok('3 дня отдыха → каждые 4 дня; режим запомнен',await pg.evaluate("calCfg().mode==='rest'&&calCfg().rest===3&&calRule(calCfg())==='RRULE:FREQ=DAILY;INTERVAL=4'"))
    past=(datetime.date.today()-datetime.timedelta(days=5)).isoformat()
    first=await pg.evaluate(f"(()=>{{const c=Object.assign({{}},calCfg(),{{start:'{past}',rest:2,time:'00:01'}});const d=calFirst(c);return [d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')]}})()")
    exp=(datetime.date.today()-datetime.timedelta(days=5)+datetime.timedelta(days=6)).isoformat()
    ok('дата в прошлом → первая будущая тренировка по тому же шагу',first[0]==exp,[first,exp])
    await pg.evaluate("document.querySelector('#calMode [data-m=week]').click()")
    ok('обратно «Дни недели» — прежний недельный повтор',await pg.evaluate("calRule(calCfg()).startsWith('RRULE:FREQ=WEEKLY;BYDAY=')&&!el('calWk').hidden"))
    # iPhone: кнопка календаря iPhone первая и открывает само событие, а не меню «Поделиться»
    ci=await b.new_context(timezone_id='Asia/Aqtobe',viewport={'width':390,'height':844},user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1')
    pi=await ci.new_page();pi.on('pageerror',lambda e:errs.append(str(e)))
    await pi.goto(URL);await pi.wait_for_timeout(300);await pi.evaluate("el('login').style.display='none';show('home');renderToday();el('tdCal').click()")
    r=await pi.evaluate("""(async()=>{const box=el('coolModal');const first=box.querySelector('.btn').id;let go=null,file=0,type='';const _c=URL.createObjectURL;
      URL.createObjectURL=b=>{type=b.type;return _c.call(URL,b);};window.calGo=u=>{go=u;};const _f=fileOut;fileOut=()=>{file++;};
      el('calI').click();const t=await (await fetch(go)).text();const r1={first:first,blob:String(go).startsWith('blob:'),type:type,ics:t.startsWith('BEGIN:VCALENDAR')&&t.includes('TRIGGER:-PT30M'),file:file};
      el('calF').click();r1.fileAfter=file;fileOut=_f;return r1;})()""")
    ok('iPhone: «Добавить в календарь iPhone» первая и открывает событие напрямую (без «Поделиться»)',r['first']=='calI' and r['blob'] and r['type'].startswith('text/calendar') and r['ics'] and r['file']==0,r)
    ok('запасной путь «Не открылось? Сохранить файл»',r['fileAfter']==1,r)
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
