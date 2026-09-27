# Publicar esta versão no Streamlit

No Streamlit Community Cloud, abra o app existente ou escolha **Create app**.

| Campo | Valor |
|---|---|
| Repository | `tassicventura-source/ai-master-challenge` |
| Branch | `submission/tassiani-ventura` |
| Main file path | `submissions/tassiani-ventura/solution/app.py` |
| Python | `3.12` |

O arquivo `requirements.txt` está ao lado do ponto de entrada. A aplicação resolve os caminhos a partir dos arquivos Python, inclusive quando iniciada pela raiz do repositório.

Se o app existente acompanha essa branch e esse caminho, o push deve disparar sua atualização. Se continuar na versão anterior, confira as configurações e os logs; use **Reboot app** quando necessário. Não é necessário apagar o app existente.

## Como reconhecer a versão nova

A tela inicial deve ser **Minha fila**. A navegação deve incluir **Clientes**, **Ficha do cliente**, **Tarefas e alertas**, **Vendas e oportunidades**, **Prioridades da carteira** e **Acompanhamento da equipe**. Uma página inicial chamada **Central de Retenção** indica a versão antiga.

## Gravações após reinício

Sem banco externo, o app funciona em modo demonstração com SQLite local. As alterações podem desaparecer após reinício ou redeploy no Community Cloud.

Para persistência durável, configure um PostgreSQL acessível ao Streamlit em **Settings → Secrets**:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require"
```

Substitua os valores pelos dados do banco. Não coloque credenciais no GitHub nem em documentos públicos. O app cria as tabelas ao inicializar. Esta entrega não migra registros operacionais de uma instalação anterior automaticamente.

Depois de configurar o banco, cadastre uma conta de teste sintética, registre uma interação e uma tarefa, reinicie o app e confirme a permanência dos três registros e da jornada. Essa verificação no serviço publicado é necessária antes de depender da persistência externa.

## Escopo desta publicação

O app utiliza dados sintéticos. Operadores informam seus nomes; ainda não há autenticação de identidade nem permissões por função. Consulte [Persistência](PERSISTENCIA_ACOES.md) antes de um uso com dados reais.

As capturas e os registros de testes de navegador incluídos no ZIP são históricos. Não representam uma nova validação do deploy.
