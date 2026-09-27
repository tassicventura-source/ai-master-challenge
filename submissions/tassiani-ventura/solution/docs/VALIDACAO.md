# Validação da versão reestruturada — 27/09/2026

Validação executada sobre o ZIP `RavenStack_Customer_Journey_reestruturado.zip`, antes de publicar esta versão.

- Instalação em ambiente virtual novo com Python 3.12.14 e `requirements-dev.txt`: concluída.
- `python -m pip check`: nenhuma dependência incompatível.
- Regras de negócio, persistência local, CRM, transformação e regressões: **54 testes aprovados** em 29,90 s.
- Interface com Streamlit AppTest: **33 testes aprovados** em 130,91 s, incluindo as 16 rotas e abertura dos 500 clientes históricos.
- Total: **87 testes aprovados**. Bancos de testes isolados, sem incorporar os registros de teste à entrega.
- Inicialização de `submissions/tassiani-ventura/solution/app.py` a partir da raiz do repositório: tela **Minha fila** carregada sem exceções.
- As cinco fontes CSV conferidas byte a byte com os arquivos originais do projeto: idênticas.
- `BRIEFING_CEO.md` e `TREINAMENTO_FUNCIONARIOS.md`: as cópias do ZIP são idênticas aos documentos enviados separadamente.
- Cache Python e arquivos SQLite temporários WAL/SHM excluídos do pacote publicado.

## Limites desta verificação

AppTest executa a interface Python, mas não substitui uma avaliação visual em navegador. O roteiro Playwright incluído ainda contém seletores da interface anterior; não foi executado nesta validação. As imagens e `browser-results.json` recebidos são evidências históricas, não evidências novas.

Não foi fornecido banco PostgreSQL externo. Sua conexão, gravação e restauração no Streamlit continuam pendentes. Sem `DATABASE_URL`, o aplicativo permanece em demonstração com SQLite local, sujeito a perda após reinício/redeploy. Não há autenticação/SSO/RBAC.

A instalação local e os testes não constituem confirmação de publicação online. O deploy deve ser reconhecido pela tela inicial **Minha fila**, conforme [instruções](DEPLOY_STREAMLIT.md).

> Esta validação substitui checkpoints anteriores de desenvolvimento. Evidências históricas permanecem no Git, mas não devem ser interpretadas como o estado final desta versão.
