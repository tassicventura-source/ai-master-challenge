# Revisão do projeto original

- Navegação agrupada por objetivo, mantendo as oito telas do sistema.
- Página executiva com três indicadores, duas questões centrais e links para investigação.
- Filtros por origem/plano e caminhos diretos das quatro áreas para Conta 360.
- Timeline com seleção de tipos, anomalias opcionais, IDs e exportação.
- Tabelas com rótulos em português, datas compactas e download do recorte.
- Diagramas técnicos recolhidos por padrão.
- Denominador de 90 dias corrigido para contas com janela completa.
- Flag de reativação preservada sem inferência de tipo de evento.
- Cache, índices SQLite, leitura restrita, build atômico do banco e reconstrução automática quando ausente.
- Dependências fixadas, lock de ambiente, scripts locais com tratamento de erro e workflow GitHub Actions.
- Testes de navegação, 500 contas, filtros, cálculos e reconstrução limpa.

As fontes brutas e os campos históricos originais foram preservados. Nenhum repositório remoto ou deploy foi publicado.

## Sistema Operacional de Retenção — 26/09/2026

- Central paginada de até 25 sinais por vez, filtros por área/prioridade e busca; corte histórico exibido na interface.
- Regras determinísticas P1/P2/P3 para 4 filas, explicação por item, evidências/IDs de origem, incerteza e próxima ação; sem score composto/preditivo.
- Conta 360 operacional e roteamento das filas Growth/Comercial, Produto, CS/Suporte e Finance/RevOps, preservando as análises/drill-downs anteriores.
- Ações editáveis com responsável, prioridade, prazo, status, observação, resultado, snapshot e trilha de eventos em SQLite local demo; resultado requerido para concluir.
- Documentação de operação, arquitetura de produção, segurança e limites do Streamlit Community Cloud.
- Testes adicionais de regras/coortes, fonte e cutoff, eventos de auditoria, transições, persistência entre processos e UI; QA em Chromium desktop/mobile.

Arquivos brutos permanecem idênticos; regras canônicas, fatos de origem e semântica econômica preexistentes não foram reescritos.
