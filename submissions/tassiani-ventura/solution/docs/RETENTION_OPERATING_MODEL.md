# Modelo operacional de retenção

## Objetivo e ciclo

O sistema guia o trabalho por: **dado → sinal → contexto → decisão → ação → responsável → acompanhamento → resultado**.

- **Dado:** tabela canônica preserva o grão e as anomalias temporais já documentadas.
- **Sinal:** regra determinística com ID estável, evidência de origem e critério de inclusão.
- **Contexto:** explicação humana do evento e sua relevância, mais incerteza/limite.
- **Decisão:** pessoa responsável avalia a evidência; a interface não conclui causalidade.
- **Ação:** tarefa e prioridade selecionadas por uma pessoa.
- **Responsável/prazo/status/observação/resultado:** persistidos e rastreáveis no modo demo.

Um sinal é uma **sugestão de triagem** e não uma declaração de conta em risco, cancelada ou com receita perdida. O modelo não atribui probabilidade.

## Regras da versão

A ordem é operacional e auditável: prioridade categórica **P1 → P2 → P3**, data de observação mais antiga primeiro e `signal_id` como desempate estável. Não há soma ponderada, pesos, score composto, probabilidade, nem cálculo de receita em risco. A data do sinal é histórica (a base termina em 2024), não uma promessa de recência operacional. Filas paginam em blocos de 25 depois dos filtros; páginas preservam a mesma ordenação determinística. Antes de intervir, valide o estado atual fora deste conjunto congelado.

| Fila | Regra de inclusão | Evidência mostrada | Interpretação proibida |
|---|---|---|---|
| Growth/Comercial · P3 | Signup em 2024, referral `organic`, primeiro plano pago `Enterprise`, `eligible_90d=True`; 22 contas conforme coorte comparável documentada. | Data/plano pagos iniciais, valor inicial registrado, elegibilidade D90, evento legado sim/não, contagem de uso/tickets válidos. | Concluir risco individual, churn ou que o `churn_event` foi saída real. A pertinência ao grupo é para revisar origem/handoff. |
| Produto · P2 | Somar `error_count` por conta × feature; `>= 5` somente onde `temporal_status=within_subscription`. | Feature, soma de erros e usos, quantidade de registros, datas e cada `usage_event_id`. | Chamar erro de falha por usuário ou causa de perda. `usage_count` e `error_count` têm semântica/unidade não esclarecida. |
| CS/Suporte · P1 | Ticket em ou após signup com `priority=urgent` **ou** `escalation_flag=True`. | `ticket_id`, data de abertura, prioridade, flag, resposta/resolução armazenadas e satisfação se existente. | Inferir insatisfação ou churn. `submitted_at` é apenas data; o histórico registra Suporte, não contatos de CS. |
| Finance/RevOps · P1/P2/P3 | Um item por linha de `lifecycle_events`, no grão evento. P1 se refund informado > 0 e contexto `paid_line_active`; P2 se contexto pago vigente sem refund positivo; P3 demais contextos. | ID/data, reason code como registrado, contexto pago, refund como informado, status `unreconciled` e próxima linha observada. | Considerar refund liquidado, churn de cliente/receita, MRR atual ou causa. Linha paga vigente não comprova pagamento. |

### Prioridade e ordem

- **P1** chama atenção primeiro para verificação humana de ticket urgente/escalado ou conferência de evento financeiro com valor registrado em contexto pago. Não é severidade clínica, segurança, probabilidade ou garantia de receita.
- **P2** agenda o próximo ciclo para sinal de Produto acima do limiar fixo ou evento Finance com linha paga vigente.
- **P3** mantém casos para revisão planejada da coorte Growth ou reconciliação sem contexto pago observado.
- Ordenar registros antigos primeiro apenas impede que itens históricos antigos sejam escondidos. Não chamar isso de “risco mais alto”. O cutoff de dados permanece 31/12/2024.
- Limiar P95 do Produto é descritivo do log observado: percentil 95 por linha válida é 4; regra >= 5 por conta × feature é um critério de triagem escolhido e registrado, sem calibração de retenção.

## Registro e acompanhamento da ação

O operador pode criar múltiplas ações para um sinal ou editar uma existente. Cada ação exige texto, responsável, prioridade e prazo; estado permitido: `Aberta`, `Em andamento`, `Bloqueada`, `Concluída`, `Cancelada`. Concluir exige campo `resultado` não vazio. Observação pode registrar progresso; resultado é texto informado por quem opera, não outcome verificado automaticamente.

Uma ação armazena:

- sinal/área/conta/situação e prioridade;
- texto da ação, pessoa responsável, prioridade operacional, prazo, status;
- observação e resultado declarados;
- snapshot JSON dos detalhes do sinal no momento da última gravação;
- timestamps UTC de criação/atualização;
- evento append-only com campos alterados a cada criação/edição.

Sinais atuais são reconstruídos dos arquivos processados. A snapshot preserva o contexto usado, mesmo que futuras versões dos arquivos mudem. O histórico não contém login: responsável é um campo livre, não identidade autenticada.

## Limites da evidência

As regras mantêm os limites originais do projeto: 531/600 eventos legados coincidem com linha paga vigente, 67 antecedem a primeira linha paga, 2 estão entre relações pagas; 400/500 contas divergem entre indicadores de churn. Usage elegível na janela: 5.568/25.000; tickets pós-signup: 923/2.000. Subscriptions se sobrepõem e não sustentam receita atual por conta. O dado é sintético e tem corte em 31/12/2024.

Logo, o sistema **não** cria churn canônico, MRR atual, perda econômica, health score, previsão, sentimento ou causalidade. Resultado de ação permanece vazio até registro humano.

## Trabalho diário sugerido

1. Revisar Central e fila da área; reconhecer que os sinais são historicamente limitados.
2. Abrir o item e confirmar evidência/IDs na Conta 360 ou sistema de origem.
3. Registrar uma próxima ação executável, responsável real, prazo e prioridade acordados.
4. Atualizar status e observações à medida que a ação progride.
5. Registrar resultado observado, incluindo “sem perda confirmada” quando for o caso; não forçar uma classificação econômica.
6. Finance/RevOps reconcilia contrato, fatura, pagamento, assinatura e movimento antes/depois; só sistemas de origem podem confirmar o outcome.
