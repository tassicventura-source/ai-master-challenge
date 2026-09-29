# Prompt Mestre — Execução de Análise por Plataforma

Use este prompt junto com:

- `data/social_media_dataset.csv`
- `analysis_engine.py`
- `COMBINACOES_ANALITICAS.md`
- `PADRAO_RELATORIO.md`

Substitua `[PLATAFORMA]` pelo nome desejado.

---

Você é responsável por finalizar a investigação de **[PLATAFORMA]** do Challenge 004 — Estratégia Social Media.

## Fonte e método

Use a base completa como fonte factual e `analysis_engine.py` como motor canônico. Não crie uma segunda lógica de cálculo. Leia `COMBINACOES_ANALITICAS.md` como arquitetura mínima da investigação e `PADRAO_RELATORIO.md` como regra obrigatória de comunicação.

## Missão

Responda, com dados auditáveis:

1. O que gera performance e engajamento em [PLATAFORMA] para cada objetivo: visualizações, curtidas, comentários, compartilhamentos, interações totais e eficiência por visualização?
2. Que conteúdo serve melhor para alcance, conversa, compartilhamento e interação total?
3. Patrocínio acrescenta performance? Em quais condições? Para qual objetivo? Quando prejudica? Como mudou no tempo?
4. Que perfis de audiência estão associados a cada comportamento?
5. O que não funciona ou não deve ser usado como regra?
6. O que mudou entre os primeiros e segundos 12 meses e ao longo dos meses?
7. Quais sinais ganharam força, perderam força ou desapareceram?
8. Quais conclusões sobrevivem ao controle por formato, categoria, tamanho do creator, audiência, tempo e outliers?

## Execução obrigatória

- Execute as análises relevantes; não apenas recomende análises.
- Separe objetivos: uma combinação pode funcionar para comentários e não para compartilhamentos.
- Reconstrua a ordem temporal dos acontecimentos.
- Compare mudança de mix com mudança de performance dentro do mesmo segmento.
- Analise top/bottom 1% e 5%.
- Procure efeitos de composição e sinais que mudam após controle.
- Tente derrubar cada conclusão importante antes de aceitá-la.
- Use creator_id apenas dentro dos limites permitidos pela auditoria da chave.
- Não assuma unidade de duração nem timezone.
- Não chame performance de ROI sem custo/receita/conversão.

## Validação de achados

Para cada achado relevante, verifique:

**Pergunta → cálculo → tamanho da amostra → resultado → tamanho da diferença → dispersão → estabilidade temporal → explicações alternativas → evidência contraditória → limitação → implicação para Marketing.**

Classifique conceitualmente como fato, associação, hipótese ou não conclusivo — mas escreva em linguagem de negócio.

## Regra de linguagem

O leitor é um CEO/Head de Marketing, não um cientista de dados.

Não escreva algo como:

> ER agregado +0,16 p.p.; rho = 0,03; AUC 0,50.

Escreva:

> A combinação teve mais interações por visualização no histórico, mas a vantagem caiu no período recente e o padrão não se repete com força suficiente para virar regra editorial. Ela pode orientar um teste, não uma expansão de produção.

A estatística técnica que comprova a frase vai no apêndice.

Nenhum bloco como “vídeo × lifestyle × 50–100k” pode aparecer sem ser traduzido para uma frase: “vídeos da categoria Lifestyle publicados por creators entre 50 mil e 100 mil seguidores”.

Nenhuma recomendação de teste pode aparecer sem explicar **por que ela merece o teste e o que o teste precisa comprovar**.

## Entregas para [PLATAFORMA]

1. `RESULTADOS_[PLATAFORMA].md`
   - resposta completa da investigação em linguagem de gestão;
   - números e contexto suficientes para auditoria;
   - sem depender da abertura de tabelas auxiliares.

2. `Relatorio_[PLATAFORMA].html`
   - narrativa executiva;
   - respostas por objetivo;
   - evolução temporal;
   - patrocínio;
   - audiência;
   - o que não funciona;
   - decisões: fazer, testar, parar, medir;
   - investigação técnica em apêndice.

3. As análises devem permanecer reproduzíveis no notebook canônico e exploráveis no dashboard único cross-platform. Não criar dashboard ou motor separado para a plataforma.

## Critério final

Um Head de Marketing deve conseguir entender em menos de 5 minutos:

- o que aconteceu;
- por que isso importa;
- o que os dados permitem afirmar;
- o que ainda é hipótese;
- o que fazer na segunda-feira.
