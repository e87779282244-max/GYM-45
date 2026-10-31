# Напоминания в календарь: ссылка Google с повтором по дням, файл .ics с напоминанием (вне Claude).
# Запуск: python3 tests/calendar_check.py index.html
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
    ok('без ошибок JS',not errs,errs[:3])
    await b.close()
asyncio.run(m());print(f'{sum(R)}/{len(R)}'+(' PASS' if all(R) else ''))
