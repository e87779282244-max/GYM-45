# Своё облако (Firebase) для версии на GitHub Pages — на подменённом Firebase (без сети):
# вход/регистрация/ошибки, запись частями, объединение двух устройств, большие данные, выход, «без входа».
# Запуск: python3 tests/firebase_check.py index.html [папка_скриншотов]
import asyncio,os,sys,shutil,tempfile,http.server,threading,functools,json
from playwright.async_api import async_playwright
HTML=os.path.abspath(sys.argv[1]);SHOT=sys.argv[2] if len(sys.argv)>2 else None
tmp=tempfile.mkdtemp();shutil.copy(HTML,tmp+'/index.html')
if os.path.isdir(os.path.dirname(HTML)+'/media'):os.symlink(os.path.dirname(HTML)+'/media',tmp+'/media')
srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=tmp))
threading.Thread(target=srv.serve_forever,daemon=True).start();URL=f'http://127.0.0.1:{srv.server_address[1]}/index.html'
R=[]
def ok(n,c,x=''):R.append(bool(c));print(('PASS ' if c else 'FAIL ')+n+(' · '+str(x) if x!='' else ''))
FS={};ACC={};WR=[0]
def fs(op,a=None,b=None):
  if op=='get':return FS.get(a)
  if op=='commit':
    WR[0]+=1
    for o in a:
      if o[0]=='set':FS[o[1]]=o[2]
      else:FS.pop(o[1],None)
    return True
  if op=='signin':
    if a not in ACC:return {'code':'auth/user-not-found'}
    if ACC[a]!=b:return {'code':'auth/invalid-credential'}
    return {'uid':'u_'+str(abs(hash(a))%10**8),'email':a}
  if op=='signup':
    if a in ACC:return {'code':'auth/email-already-in-use'}
    if len(b)<6:return {'code':'auth/weak-password'}
    ACC[a]=b;return {'uid':'u_'+str(abs(hash(a))%10**8),'email':a}
MOCK=r'''(()=>{const L=[];let cur=null;try{cur=JSON.parse(localStorage.getItem("__mauth")||"null");}catch(e){}
const setU=u=>{cur=u;localStorage.setItem("__mauth",JSON.stringify(u));L.forEach(f=>f(u));};
const call=async(op,a,b)=>{const r=await window.__fs(op,a,b);if(r&&r.code){const e=new Error(r.code);e.code=r.code;throw e;}return r;};
const auth={get currentUser(){return cur;},onAuthStateChanged(f){L.push(f);setTimeout(()=>f(cur),0);},getRedirectResult:async()=>null,
  signInWithEmailAndPassword:async(m,p)=>{setU(await call("signin",m,p));},createUserWithEmailAndPassword:async(m,p)=>{setU(await call("signup",m,p));},
  sendPasswordResetEmail:async m=>{window.__reset=m;},signOut:async()=>setU(null),signInWithPopup:async()=>{setU({uid:"u_google",email:"g@gmail.com"});}};
const ref=p=>({collection:c=>({doc:d=>ref(p+"/"+c+"/"+d)}),path:p,get:async()=>{const v=await window.__fs("get",p);return {exists:v!=null,data:()=>v};}});
const store={collection:c=>({doc:d=>ref(c+"/"+d)}),batch(){const ops=[];return {set:(r,v)=>ops.push(["set",r.path,v]),delete:r=>ops.push(["del",r.path]),commit:()=>window.__fs("commit",ops)};}};
const fb={apps:[],initializeApp(c){fb.apps.push(c);window.__cfg=c;},auth:()=>auth,firestore:()=>store};fb.auth.GoogleAuthProvider=function(){};window.firebase=fb;})();'''
def hist(n,tag):return [{'date':'2026-0%d-%02d'%(1+i%9,1+i%28),'name':tag+' '+str(i),'vol':1000+i,'log':[{'n':'Жим лёжа','sets':[[80+i%20,5]]*4}],'dur':3600} for i in range(n)]
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch();errs=[]
    async def dev(local_hist=None):
      c=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2);await c.expose_function('__fs',fs);await c.add_init_script(MOCK)
      pg=await c.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
      if local_hist is not None:
        await pg.goto(URL);await pg.evaluate("h=>{localStorage.setItem(KEY,JSON.stringify(h))}",local_hist)
      await pg.goto(URL);await pg.wait_for_timeout(400);return c,pg
    A,a=await dev()
    ok('вход: форма облака, без демо-пароля',await a.evaluate("getComputedStyle(el('login')).display!=='none'&&!!el('fbGoogle')&&!!el('fbSkip')&&el('pass').value===''&&!el('login').textContent.includes('Демо')"))
    ok('Firebase получил конфиг проекта gym-45-8aa8e',await a.evaluate("window.__cfg&&window.__cfg.projectId==='gym-45-8aa8e'"))
    if SHOT:await a.screenshot(path=SHOT+'/fb-login.png')
    await a.fill('#email','ev@mail.ru');await a.fill('#pass','123');await a.click('#fbReg');await a.wait_for_timeout(200)
    ok('короткий пароль — понятная ошибка',await a.evaluate("el('fbMsg').textContent.includes('минимум 6')"))
    await a.fill('#pass','secret77');await a.click('#loginBtn');await a.wait_for_timeout(200)
    ok('вход в несуществующий аккаунт — подсказка создать',await a.evaluate("el('fbMsg').textContent.includes('Создать аккаунт')"))
    await a.click('#fbForgot');await a.wait_for_timeout(150)
    ok('«Забыли пароль?» отправляет письмо',await a.evaluate("window.__reset==='ev@mail.ru'&&el('fbMsg').textContent.includes('Письмо')"))
    await a.click('#fbReg');await a.wait_for_timeout(700)
    ok('регистрация: вход скрыт, облако подключено',await a.evaluate("el('login').style.display==='none'&&el('cloudStatus').textContent.includes('Синхронизация')"),await a.evaluate("el('cloudStatus').textContent"))
    uid=[k for k in FS if k.endswith('/meta')]
    ok('в облаке создан users/{uid}/data/meta',len(uid)==1,list(FS)[:3])
    base=uid[0][:-5]
    await a.evaluate("h=>{localStorage.setItem(KEY,JSON.stringify(h));cloudPush();}",hist(2,'A'));await a.wait_for_timeout(1900)
    def cloud():
      md=FS[base+'/meta'];return json.loads(''.join(FS[base+'/c%d'%i]['s'] for i in range(md['n'])))
    ok('запись после тренировки ушла в облако',len(cloud()['history'])==2)
    # второе устройство со своей записью
    B,bb=await dev(hist(1,'B'))
    await bb.fill('#email','ev@mail.ru');await bb.fill('#pass','wrong!!');await bb.click('#loginBtn');await bb.wait_for_timeout(200)
    ok('неверный пароль — ошибка',await bb.evaluate("el('fbMsg').textContent.includes('Неверная')"))
    await bb.fill('#pass','secret77');await bb.click('#loginBtn');await bb.wait_for_timeout(700)
    ok('второе устройство: записи объединены (2+1), ничего не потеряно',await bb.evaluate("safe.get().length")==3 and len(cloud()['history'])==3)
    # большие данные: >200 тыс. символов → несколько частей
    big=hist(2,'A')+hist(1,'B')+hist(2500,'X')
    await bb.evaluate("h=>{localStorage.setItem(KEY,JSON.stringify(h));cloudPush();}",big);await bb.wait_for_timeout(1900)
    n=FS[base+'/meta']['n'];ok('большая история пишется частями',n>=2,f'частей {n}, размер {FS[base+"/meta"]["size"]}')
    ok('части читаются обратно целиком',len(cloud()['history'])==2503)
    # первое устройство вернулось в приложение — подтянуло записи
    await a.evaluate("cloudInit()");await a.wait_for_timeout(500)
    ok('первое устройство получило записи второго',await a.evaluate("safe.get().length")==2503)
    # история уменьшилась → лишние части удаляются
    await bb.evaluate("()=>{const h=safe.get().slice(0,3);localStorage.setItem(KEY,JSON.stringify(h));CLOUD.db.doc().set(cloudSnapshot());}");await bb.wait_for_timeout(300)
    ok('старые части удалены',not any(k.startswith(base+'/c') and int(k.split('/c')[-1])>=FS[base+'/meta']['n'] for k in FS))
    # перезапуск: вход сохраняется, экран входа не показывается
    await a.reload();await a.wait_for_timeout(50)
    ok('перезапуск: экрана входа нет сразу',await a.evaluate("el('login').style.display==='none'"))
    await a.wait_for_timeout(500)
    # профиль: аккаунт и выход
    await bb.evaluate("show('profile')");await bb.wait_for_timeout(100)
    ok('профиль показывает аккаунт',await bb.evaluate("el('fbAcc').textContent.includes('ev@mail.ru')&&!!el('fbOut')"))
    if SHOT:await bb.screenshot(path=SHOT+'/fb-profile.png')
    await bb.click('#fbOut');await bb.wait_for_timeout(300)
    ok('выход: снова экран входа, записи на телефоне остались',await bb.evaluate("el('login').style.display!=='none'&&safe.get().length>0"))
    # Google
    await bb.click('#fbGoogle');await bb.wait_for_timeout(600)
    ok('вход через Google',await bb.evaluate("el('login').style.display==='none'&&CLOUD_UID==='u_google'"))
    # без входа
    C,cc=await dev()
    await cc.click('#fbSkip');await cc.wait_for_timeout(100)
    ok('«без входа»: приложение открыто, облака нет',await cc.evaluate("el('login').style.display==='none'&&!CLOUD"))
    await cc.reload();await cc.wait_for_timeout(400)
    ok('«без входа» запоминается',await cc.evaluate("el('login').style.display==='none'"))
    await cc.evaluate("show('profile')");ok('в профиле — «Войти и сохранять в облако»',await cc.evaluate("!!el('fbIn')"))
    ok('без ошибок JS',not errs,errs[:3])
    # обычный режим (локальный адрес без Firebase) — прежний вход
    D=await b.new_context();dp=await D.new_page();await dp.goto(URL);await dp.wait_for_timeout(300)
    ok('без Firebase — прежнее поведение, облако не грузится',await dp.evaluate("!fbMode()&&el('login').textContent.includes('Демо')&&!document.querySelector('script[src*=gstatic]')"))
    await b.close()
asyncio.run(m());srv.shutdown();print(f'{sum(R)}/{len(R)}');sys.exit(0 if all(R) else 1)
