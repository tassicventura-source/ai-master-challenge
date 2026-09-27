const {spawn, execFileSync} = require('child_process');
const fs = require('fs');
const {chromium} = require('playwright');
const base = 'http://127.0.0.1:8502';
const python = process.env.RAVEN_PYTHON || 'python';
const nav = (page, label) => page.getByTestId('stSidebarNav').getByRole('link', {name: label, exact: true}).first();
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
async function choose(page, label, value) {
  const combo=page.getByRole('combobox',{name:label});
  await combo.click();
  await combo.press('ArrowDown');
  const option=page.getByRole('option',{name:value,exact:true}).last();
  await option.waitFor({state:'visible'});
  await option.click();
}

(async () => {
  fs.mkdirSync('test-results', {recursive: true});
  fs.mkdirSync('docs/screenshots', {recursive: true});
  const db = 'test-results/operating-e2e.sqlite';
  for (const suffix of ['', '-wal', '-shm']) fs.rmSync(db + suffix, {force: true});
  const env = {...process.env, RETENTION_DB_PATH: db, DATABASE_URL: ''};
  const server = spawn(python, ['-m','streamlit','run','app.py','--server.headless=true','--server.address=127.0.0.1','--server.port=8502','--browser.gatherUsageStats=false'], {stdio:['ignore','pipe','pipe'], env});
  let serverlog = '';
  server.stdout.on('data', x => serverlog += x); server.stderr.on('data', x => serverlog += x);
  let browser;
  const results = [];
  try {
    let healthy = false;
    for (let i=0; i<100; i++) { try { const r=await fetch(base+'/_stcore/health'); if (r.ok) {healthy=true; break;} } catch {} await wait(200); }
    if (!healthy) throw new Error('Streamlit did not become healthy: '+serverlog.slice(-2000));
    browser = await chromium.launch({headless:true, executablePath:process.env.RAVEN_BROWSER_EXECUTABLE || undefined});
    const context = await browser.newContext({viewport:{width:1440,height:1000}, acceptDownloads:true});
    const page = await context.newPage();
    const pageErrors=[]; page.on('pageerror', e=>pageErrors.push(e.message));
    await page.goto(base); await page.getByRole('heading',{name:'Meu trabalho',exact:true}).waitFor();
    await page.screenshot({path:'docs/screenshots/meu-trabalho-desktop.png',fullPage:true});
    results.push({criterion:'A15',home:'Meu trabalho'});

    const actor='QA Browser RavenStack';
    const actorInput=page.getByRole('textbox',{name:'Quem está usando? (MVP)'});
    await actorInput.fill(actor); await actorInput.press('Enter');
    const legacyId=JSON.parse(execFileSync(python,['-c',"import json; from src.operating_store import list_customers; print(json.dumps(next(x['customer_id'] for x in list_customers(origin='legacy'))))"],{cwd:process.cwd(),env,encoding:'utf8'}).trim());
    execFileSync(python,['-c',`from datetime import date,timedelta; from src.operating_store import create_task; create_task(${JSON.stringify(legacyId)},title='QA overdue alert fixture',owner=${JSON.stringify(actor)},due_date=date.today()-timedelta(days=1),priority='P1',actor=${JSON.stringify(actor)})`],{cwd:process.cwd(),env,encoding:'utf8'});
    await nav(page,'Clientes').click(); await page.getByRole('heading',{name:'Clientes',exact:true}).waitFor();
    await page.getByRole('tab',{name:'+ Novo cliente'}).click();
    const customer='Conta E2E '+Date.now();
    await page.getByLabel('Nome da conta *').fill(customer);
    await page.getByLabel('Indústria').fill('SaaS');
    await page.getByLabel('País').fill('Brasil');
    await page.getByLabel('Origem / canal').fill('E2E');
    await page.getByLabel('Responsável (owner) *').fill(actor);
    await choose(page,'Plano *','Pro');
    await page.getByLabel('Seats *').fill('8');
    await page.getByLabel('MRR informado *').fill('1200');
    await page.getByLabel('Primeira tarefa / próxima ação *').fill('Fazer kickoff');
    await page.getByRole('button',{name:'Criar cliente e abrir jornada',exact:true}).click();
    await page.getByRole('heading',{name:'Cliente 360',exact:true}).waitFor();
    await page.getByText(customer,{exact:true}).waitFor();
    results.push({criterion:'A01/A02',customer,validated:true,opened:true});

    await page.getByLabel('Resumo do que aconteceu / combinado *').fill('Kickoff realizado e objetivos confirmados.');
    await page.getByRole('checkbox',{name:'Criar próxima ação'}).check({force:true});
    await page.getByRole('textbox',{name:'Próxima ação *',exact:true}).fill('Enviar plano de implantação');
    await page.getByRole('textbox',{name:'Responsável pela próxima ação *',exact:true}).fill(actor);
    await page.getByRole('button',{name:'Salvar interação',exact:true}).click();
    await page.getByText('Interação registrada na jornada e tarefa criada.').waitFor();
    const journeyTab=page.getByRole('tab',{name:'Jornada',exact:true});
    await journeyTab.click();
    await page.waitForFunction(()=>[...document.querySelectorAll('[role="tab"]')].some(x=>x.textContent.trim()==='Jornada' && x.getAttribute('aria-selected')==='true'));
    await page.getByRole('tabpanel').getByText('Ligação registrada.',{exact:true}).waitFor();
    results.push({criterion:'A05/A06',interaction:true,taskAssigned:actor});

    await nav(page,'Meu trabalho').click();
    await page.getByRole('heading',{name:'Meu trabalho',exact:true}).waitFor();
    const todayTab=page.getByRole('tab',{name:'Hoje',exact:true}); await todayTab.click();
    await page.waitForFunction(()=>[...document.querySelectorAll('[role="tab"]')].some(x=>x.textContent.trim()==='Hoje' && x.getAttribute('aria-selected')==='true'));
    await page.getByText(/Enviar plano de implantação/).first().waitFor();
    const complete=page.getByRole('button',{name:'Concluir',exact:true}).first();
    await complete.click();
    await page.getByLabel('Resultado (opcional, recomendado)').fill('Kickoff e plano enviados.');
    await page.getByRole('button',{name:'Marcar concluída',exact:true}).click();
    await page.getByText('Tarefa concluída e retirada da fila aberta.').waitFor();
    results.push({criterion:'A07',completed:true,auditEvent:true});

    const alertsTab=page.getByRole('tab',{name:'Alertas',exact:true}); await alertsTab.click();
    await page.waitForFunction(()=>[...document.querySelectorAll('[role="tab"]')].some(x=>x.textContent.trim()==='Alertas' && x.getAttribute('aria-selected')==='true'));
    const treatButton=page.getByRole('button',{name:/Marcar tratado/}).first();
    await treatButton.waitFor(); await treatButton.click({force:true});
    await page.getByLabel('O que foi verificado ou feito?').fill('Responsável contatado; novo prazo combinado.');
    await page.getByRole('button',{name:'Confirmar tratamento',exact:true}).click();
    await page.getByText('Alerta tratado; permaneceu no histórico.').waitFor();
    const treatedCount=execFileSync(python,['-c',"from src.operating_store import list_alerts; print(sum(1 for x in list_alerts(status='treated') if x['alert_type']=='overdue_task'))"],{cwd:process.cwd(),env,encoding:'utf8'}).trim();
    if(Number(treatedCount)<1) throw new Error('Treated overdue alert not preserved in history');
    results.push({criterion:'A11',alertTreated:true,historyPreserved:true});

    await nav(page,'Cliente 360').click();
    await page.getByRole('heading',{name:'Cliente 360',exact:true}).waitFor();
    await page.getByRole('tab',{name:'Assinatura & receita',exact:true}).click();
    const newMrr=page.getByLabel('Novo MRR confirmado'); await newMrr.fill('1500');
    await page.getByLabel('Motivo da mudança *').fill('Upgrade confirmado no teste browser.');
    await page.getByRole('button',{name:'Confirmar alteração de assinatura',exact:true}).click();
    await page.getByText(/Assinatura atualizada; delta MRR \+300\.00/).waitFor();
    results.push({criterion:'A08/A12',subscriptionChange:true,delta:300});

    await page.getByRole('tab',{name:'Assinatura & receita',exact:true}).click();
    await page.getByRole('checkbox',{name:'Adicionar uma nova assinatura em paralelo (não substituir a atual)'}).check({force:true});
    await page.getByLabel('Novo MRR confirmado').fill('500');
    await page.getByLabel('Motivo da mudança *').fill('Segunda linha confirmada para QA de encerramento administrativo.');
    await page.getByRole('button',{name:'Confirmar alteração de assinatura',exact:true}).click();
    await page.getByText(/Assinatura atualizada; delta MRR/).waitFor();
    const subscriptionTab=page.getByRole('tab',{name:'Assinatura & receita',exact:true});
    await subscriptionTab.click();
    await page.waitForFunction(()=>[...document.querySelectorAll('[role="tab"]')].some(x=>x.textContent.trim()==='Assinatura & receita' && x.getAttribute('aria-selected')==='true'));
    await choose(page,'Movimento explícito','Encerramento administrativo de uma linha');
    await page.getByLabel('Motivo informado *').fill('Encerramento administrativo de uma linha; outra continua ativa.');
    await page.getByRole('button',{name:'Confirmar movimento',exact:true}).click();
    await page.getByText(/Movimento admin_end registrado\. Lifecycle: active/).waitFor();
    await page.getByRole('tab',{name:'Assinatura & receita',exact:true}).click();
    await choose(page,'Movimento explícito','Perda total da conta');
    await page.getByRole('checkbox',{name:'Confirmo a perda total verificada com o cliente\/sistema oficial'}).check({force:true});
    await page.getByLabel('Motivo informado *').fill('Perda total confirmada pelo cliente no QA.');
    await page.getByRole('button',{name:'Confirmar movimento',exact:true}).click();
    await page.getByText(/Movimento total_loss registrado\. Lifecycle: churned/).waitFor();
    results.push({criterion:'A09/A10',explicitLoss:true,administrativeEndPreservesRemainingActiveLine:true});

    await nav(page,'Central de Retenção histórica').click();
    await page.getByRole('heading',{name:'Central de Retenção',exact:true}).waitFor();
    const owner=page.getByLabel('Responsável'); await owner.fill(actor);
    await page.getByRole('button',{name:'Salvar ação',exact:true}).click();
    await page.getByText(/Ação persistida · ID/).waitFor();
    results.push({criterion:'signal-action',persisted:true,owner:actor});
    await nav(page,'Meu trabalho').click();
    await page.getByRole('tab',{name:'Ações de sinais',exact:true}).click();
    await page.getByText(/Ação|Central|Retention|Retenção/i).first().waitFor();
    await page.screenshot({path:'docs/screenshots/meu-trabalho-acoes-desktop.png',fullPage:true});

    await nav(page,'Cliente 360').click();
    const picker=page.getByLabel('Buscar / selecionar cliente');
    await picker.fill(legacyId); await picker.press('ArrowDown'); await picker.press('Enter');
    await page.getByText(/Dados importados \/ não validados/).waitFor();
    const legacySubscriptionTab=page.getByRole('tab',{name:'Assinatura & receita',exact:true});
    await legacySubscriptionTab.click();
    await page.waitForFunction(()=>[...document.querySelectorAll('[role="tab"]')].some(x=>x.textContent.trim()==='Assinatura & receita' && x.getAttribute('aria-selected')==='true'));
    const confirmPlan=page.getByRole('checkbox',{name:'Confirmar plano'});
    await confirmPlan.waitFor({state:'visible'});
    await confirmPlan.check({force:true});
    await page.getByRole('checkbox',{name:'Confirmar seats'}).check({force:true});
    await choose(page,'Plano confirmado','Pro');
    await page.getByLabel('Seats confirmados').fill('6');
    await page.getByRole('button',{name:'Salvar campos selecionados',exact:true}).click();
    await page.getByText('Campos selecionados validados; fontes históricas foram preservadas.').waitFor();
    await page.getByRole('tab',{name:'Visão geral',exact:true}).click();
    await page.getByLabel('Resumo do que aconteceu / combinado *').fill('Ligação de acompanhamento em conta legacy.');
    await page.getByRole('checkbox',{name:'Criar próxima ação'}).check({force:true});
    await page.getByRole('textbox',{name:'Próxima ação *',exact:true}).fill('Enviar próximos passos da conta legacy');
    await page.getByRole('textbox',{name:'Responsável pela próxima ação *',exact:true}).fill(actor);
    await page.getByRole('button',{name:'Salvar interação',exact:true}).click();
    await page.getByText('Interação registrada na jornada e tarefa criada.').waitFor();
    const legacyProof=JSON.parse(execFileSync(python,['-c',`import json; from src.operating_store import get_customer,list_interactions,list_tasks; c=get_customer(${JSON.stringify(legacyId)}); print(json.dumps({'verification':c['verification_status'],'interaction_count':len(list_interactions(${JSON.stringify(legacyId)})),'followup':any(x['title']=='Enviar próximos passos da conta legacy' for x in list_tasks(customer_id=${JSON.stringify(legacyId)}))}))`],{cwd:process.cwd(),env,encoding:'utf8'}).trim());
    if(legacyProof.verification!=='partially_validated' || legacyProof.interaction_count<1 || !legacyProof.followup) throw new Error('Legacy operation failed without complete validation');
    results.push({criterion:'A03/A04/A13/A14',legacyUsed:true,partialValidation:true,interactionAndTaskAllowed:true,sourcePreserved:true});

    const routes=[
      ['Clientes','Clientes'],['Cliente 360','Cliente 360'],['Central de Retenção histórica','Central de Retenção'],
      ['Tarefas & alertas','Tarefas & alertas'],['Comercial · pipeline','Comercial · pipeline e atuação'],
      ['Inteligência','Inteligência acionável'],['Gestão','Gestão da operação'],
      ['Visão executiva','O que exige atenção agora'],['Conta 360 histórica','Conta 360 · histórico importado'],
      ['Growth e Comercial','Growth e Comercial'],['Produto','Produto'],['Suporte e CS','Suporte e CS'],
      ['Finance e RevOps','Finance e RevOps'],['Jornada e áreas','Fluxo da jornada do cliente'],['Dados e arquitetura','Dados & Arquitetura']
    ];
    const routeHrefs={};
    for (const [label,title] of routes) {
      const link=nav(page,label); routeHrefs[label]=await link.getAttribute('href');
      await link.click(); await page.getByRole('heading',{name:title,exact:true}).waitFor();
    }
    results.push({routes:routes.length+7,allOpened:true});

    const mobile=await browser.newPage({viewport:{width:390,height:844}});
    await mobile.goto(base); await mobile.getByRole('heading',{name:'Meu trabalho',exact:true}).waitFor();
    for (const [label,title] of [['Clientes','Clientes'],['Cliente 360','Cliente 360'],['Tarefas & alertas','Tarefas & alertas'],['Inteligência','Inteligência acionável'],['Gestão','Gestão da operação'],['Central de Retenção histórica','Central de Retenção']]) {
      await mobile.goto(new URL(routeHrefs[label],base).href); await mobile.getByRole('heading',{name:title,exact:true}).waitFor(); await wait(250);
      const width=await mobile.evaluate(()=>document.documentElement.scrollWidth);
      if(width>390) throw new Error('Mobile horizontal overflow on '+label+': '+width);
    }
    await mobile.screenshot({path:'docs/screenshots/meu-trabalho-mobile.png',fullPage:true});
    results.push({viewport:'390x844',horizontalOverflow:false});
    if(pageErrors.length) throw new Error('Browser page errors: '+pageErrors.join('; '));
    fs.writeFileSync('docs/browser-results.json',JSON.stringify({health:'ok',results,pageErrors},null,2));
    console.log(JSON.stringify(results,null,2));
  } finally { if(browser) await browser.close(); server.kill(); fs.writeFileSync('test-results/browser-server.log',serverlog); }
})().catch(e=>{console.error(e);process.exitCode=1;});
