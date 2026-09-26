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
