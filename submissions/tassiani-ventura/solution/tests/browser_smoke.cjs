const {spawn}=require('child_process');
const fs=require('fs');
const {chromium}=require('playwright');
(async()=>{
 fs.mkdirSync('test-results',{recursive:true});fs.mkdirSync('docs/screenshots',{recursive:true});
 for(const suffix of ['', '-wal', '-shm'])fs.rmSync('test-results/retention_actions.sqlite'+suffix,{force:true});

 const server=spawn(process.env.RAVEN_PYTHON || (process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python'),['-m','streamlit','run','app.py','--server.headless=true','--server.address=127.0.0.1','--server.port=8502','--browser.gatherUsageStats=false'],{stdio:['ignore','pipe','pipe'],env:{...process.env,RETENTION_DB_PATH:'test-results/retention_actions.sqlite'}});
 let serverlog=''; server.stdout.on('data',x=>serverlog+=x);server.stderr.on('data',x=>serverlog+=x);
 let browser;
 try {
  for(let i=0;i<80;i++) {try{let r=await fetch('http://127.0.0.1:8502/_stcore/health');if(r.ok)break}catch{} await new Promise(r=>setTimeout(r,150));}
  browser=await chromium.launch({headless:true,executablePath:process.env.RAVEN_BROWSER_EXECUTABLE || undefined});
  const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
  const page=await context.newPage(); const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8502');
  await page.getByRole('heading',{name:'Central de Retenção',exact:true}).waitFor();
  await page.getByText('Sinais para triagem',{exact:true}).waitFor();await page.waitForTimeout(1200);
  await page.screenshot({path:'docs/screenshots/00-central-desktop.png',fullPage:true});
  const routes=[['Central de Retenção','Central de Retenção'],['Visão executiva','O que exige atenção agora'],['Conta 360','Conta 360'],['Growth e Comercial','Growth e Comercial'],['Produto','Produto'],['Suporte e CS','Suporte e CS'],['Finance e RevOps','Finance e RevOps'],['Jornada e áreas','Fluxo da jornada do cliente'],['Dados e arquitetura','Dados & Arquitetura']];
  const results=[];const mobileRoutes=[];
  const owner=page.getByLabel('Responsável');await owner.fill('QA Retenção');
  await page.getByRole('button',{name:'Salvar ação',exact:true}).click();
  await page.getByText(/1 ação persistida no modo demo/).waitFor();results.push({action:'created',owner:'QA Retenção',persisted:true});
  for(const [label,title] of routes){
   const nav=page.getByTestId('stSidebarNav').getByRole('link',{name:label,exact:true});
   mobileRoutes.push([label,title,await nav.getAttribute('href')]);
   await nav.click();
   await page.getByRole('heading',{name:title,exact:true}).waitFor();
   if(label==='Central de Retenção')await page.getByText(/1 ação persistida no modo demo/).waitFor();
   await page.waitForTimeout(1500);
   if(await page.getByTestId('stException').count())throw Error('Streamlit exception in '+label);
   const downloads=page.getByRole('button',{name:'Baixar este recorte em CSV',exact:true});
   if(await downloads.count() && await downloads.first().isEnabled()){
    const dl=page.waitForEvent('download');await downloads.first().click(); const file=await dl;
    const path=await file.path(); const bytes=fs.readFileSync(path);
    if(bytes.length<20)throw Error('Empty CSV '+label);
    results.push({route:label,csv:file.suggestedFilename(),bytes:bytes.length});
   }else results.push({route:label});
   await page.evaluate(()=>document.querySelector('[data-testid=stMain]').scrollTo(0,0));await page.waitForTimeout(300);
   const screenshotBase=label==='Central de Retenção'?'00-central':label.toLowerCase().replace(/[^a-z0-9]/g,'-');
   await page.screenshot({path:'docs/screenshots/'+screenshotBase+'-desktop.png',fullPage:true});
  }
  await page.getByTestId('stSidebarNav').getByRole('link',{name:'Finance e RevOps',exact:true}).click();
  await page.getByRole('heading',{name:'Finance e RevOps',exact:true}).waitFor();
  await page.getByRole('button',{name:'Abrir Conta 360',exact:true}).click();
  await page.getByRole('heading',{name:'Conta 360',exact:true}).waitFor();
  results.push({drilldown:'Finance → Conta 360',ok:true});
  const mobile=await context.newPage({viewport:{width:390,height:844}}).catch(()=>null);
  const mp=mobile||await context.newPage();await mp.setViewportSize({width:390,height:844});
  await mp.goto('http://127.0.0.1:8502');await mp.getByRole('heading',{name:'Central de Retenção',exact:true}).waitFor();
  await mp.getByText('Ações fora do prazo',{exact:true}).waitFor();await mp.waitForTimeout(1200);
  await mp.screenshot({path:'docs/screenshots/00-central-mobile.png',fullPage:true});
  await mp.getByLabel('Responsável').fill('QA Mobile');
  await mp.getByRole('button',{name:'Salvar ação',exact:true}).click();
  await mp.getByText(/2 ações persistidas no modo demo/).waitFor();results.push({action:'created-mobile',owner:'QA Mobile',persisted:true});
  results.push({mobileWidth:390,documentWidth:await mp.evaluate(()=>document.documentElement.scrollWidth),clientWidth:await mp.evaluate(()=>document.documentElement.clientWidth)});
  for(const [label,title,href] of mobileRoutes){
    await mp.goto(new URL(href,'http://127.0.0.1:8502').href);
    await mp.getByRole('heading',{name:title,exact:true}).waitFor();await mp.waitForTimeout(1500);
    if(await mp.getByTestId('stException').count())throw Error('Mobile exception in '+label);
    const width=await mp.evaluate(()=>document.documentElement.scrollWidth);
    if(width>390)throw Error('Mobile overflow '+label+' '+width);
    const screenshotBase=label==='Central de Retenção'?'00-central':label.toLowerCase().replace(/[^a-z0-9]/g,'-');
    await mp.screenshot({path:'docs/screenshots/'+screenshotBase+'-mobile.png',fullPage:true});
    results.push({mobile:label,documentWidth:width});
  }
  if(errors.length)throw Error(errors.join('\n'));
  fs.writeFileSync('docs/browser-results.json',JSON.stringify({health:'ok',routes:results,pageErrors:errors},null,2));
  console.log(JSON.stringify(results));
 }finally{if(browser)await browser.close();server.kill();fs.writeFileSync('test-results/browser-server.log',serverlog)}
})().catch(e=>{console.error(e);process.exitCode=1});
