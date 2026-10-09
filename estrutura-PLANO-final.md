# Plano consolidado: Normalidade Contextual de Recursos de API para apoio à triagem de incidentes

## 1. Enquadramento
Este trabalho complementa o pré-projeto de mestrado (sistema multiagente para apoio a incidentes). Não se trata de monitoração em tempo real nem de medir o tempo até a causa raiz (MTTRC). O objetivo é, **dado um incidente registrado**, informar ao operador (ou ao agente que o apoia) se o **período anterior ao registro** estava em **processamento normal** para cada recurso de API envolvido. Se não estava, informar **como, desde quando e de que lado** (provedor ou consumidor) está o desvio, para direcionar a triagem com mais acerto.

## 2. Objetivos
**Objetivo geral:** caracterizar os comportamentos normais de cada recurso de API a partir de Access Logs agregados, e classificar períodos como **Normal** ou **Residual**, gerando informação explicável que apoie a triagem de incidentes.

**Objetivos específicos**
1. Caracterizar estatisticamente o comportamento de cada recurso e confirmar que ele tem vários regimes normais, ligados ao contexto (hora, tipo de dia, lotes).
2. Construir um perfil de normalidade por recurso e por contexto, capaz de separar o estado Normal do Residual.
3. Caracterizar o residual (início, duração, atributos desviados, abrangência entre clientes, lado provável) de forma útil à triagem.
4. Avaliar o método com falhas injetadas e compará-lo a baselines simples.
5. Disponibilizar a informação num formato estruturado para o agente e o operador (JSON).

**Questões de pesquisa**
- **RQ1:** Access Logs agregados por janela permitem caracterizar os regimes normais de cada recurso e separar o Residual do Normal melhor do que abordagens sem contexto?
- **RQ2:** A caracterização do residual (início estimado e lado provável) é precisa o bastante para apoiar o direcionamento da triagem?
- **RQ3:** Quais atributos mais contribuem para identificar e caracterizar o residual?

## 3. Definições
| Termo | Definição |
|---|---|
| Recurso | `CD_RCS_CAT`. **Toda a análise é feita por recurso** |
| Janela | Agregação temporal. Padrão **1h**, configurável (15 min, 30 min, 1h, 4h) |
| Contexto | **Hora (horário de Brasília) × tipo de dia**: útil / sábado / domingo-feriado |
| Feriado | Não há feriado no treino (agosto); **o feriado usa o perfil de domingo**. A lista de feriados é configurável (07/09/2026) |
| **Normal** | A janela está dentro da faixa normal do seu contexto em todos os atributos. Existem vários normais por recurso: dia útil, sábado, domingo, lote, manutenção recorrente |
| **Residual** | Tudo que não é Normal: degradação, transição, evento isolado ou desconhecido |
| Características do residual | Início estimado, duração (janelas seguidas), atributos desviados (z > 3), abrangência entre clientes, lado provável |

## 4. Dados
- **Fonte:** `DADOS/APIs-Agr-20260801-20260908_hash.csv`. Uma linha por minuto × recurso × status HTTP × cliente, com volume (`QT_TTL_TRAN`) e tempo médio (`QT_TMP_MEDI_EXEA`). O `CD_CLI` vem anonimizado por SHA-256 com semente.
- **Fuso:** `TS_EVT` está em **UTC** e é convertido para **America/Sao_Paulo (UTC−3)** antes de calcular o contexto e de dividir treino e teste.
- **Tamanho:** 2,3 milhões de linhas, 12 recursos, 1.825 clientes, de 31/07 21h até 08/09 20h59 no horário de Brasília.
- **Divisão:**

| Conjunto | Período (Brasília) |
|---|---|
| Ajuste do modelo | 01–24/08 |
| Calibração do limiar | 25–31/08 |
| Modelo final | ajustado em 01–31/08 |
| Teste com falhas injetadas | 01–07/09 |

- **Limitações conhecidas:**
  - 17.265 chaves repetidas (serão consolidadas);
  - `18917905`, `18917906`, `18917920` e `18917921` param em 03/09 às 07:11 (Brasília);
  - `17834257` tem só 1 ou 2 clientes, então o lado provável não pode ser determinado;
  - não há percentis de latência, só a média por cliente e minuto;
  - não há histórico de incidentes.

## 5. Requisitos
**Funcionais**
- **RF1:** `consultar(recurso, t_registro, horas_antes=6)` devolve um JSON com o estado do período, o regime esperado, as características do residual, o `motivo_estatistico` e a `sugestao_triagem`.
- **RF2:** estado (Normal ou Residual) de cada janela de cada recurso.
- **RF3:** características do residual (seção 3).
- **RF4:** lado provável por uma matriz heurística documentada (seção 7, notebook 04).
- **RF5:** tudo configurável: janela, datas, fuso, feriados, multiplicador do MAD, meta de alarmes, horas antes do registro, semente.

**Metodológicos e não funcionais**
- **RNF1:** análise e ajuste sempre **por recurso**.
- **RNF2:** **sem vazamento temporal.** O modelo e o limiar usam só agosto, e o teste nunca participa do ajuste.
- **RNF3:** reprodutibilidade:
  - célula de parâmetros no início de cada notebook;
  - sementes fixas;
  - saídas intermediárias em parquet;
  - funções num módulo compartilhado.
- **RNF4:** explicabilidade. Toda decisão pode ser rastreada até um atributo e sua faixa normal.
- **RNF5:** simplicidade. Só pandas, NumPy, SciPy, scikit-learn, statsmodels e Matplotlib.
- **RNF6:** LGPD. Cliente anonimizado, sem payload e sem dados pessoais.

**Critérios de sucesso** (definidos antes da modelagem; valores iniciais para discussão)
| Tipo | Critério | Meta |
|---|---|---|
| Técnico | F1 por episódio versus o melhor baseline | maior, nas 10 sementes |
| Técnico | Janelas limpas marcadas como Residual | ≤ 2% |
| Técnico | Erro no início estimado | ≤ 1 janela (mediana) |
| Negócio | Acurácia do lado provável (episódios detectados) | ≥ 70% |
| Negócio | Consultas de controle (sem falha) com saída "Normal" | ≥ 95% |

## 6. Experimentos
| Id | Experimento | RQ | Como | Métricas |
|---|---|---|---|---|
| **E1** | Caracterização dos regimes | RQ1 | Testes de diferença entre contextos; k-means **só com atributos de comportamento**, depois cruzamento regime × hora × tipo de dia para nomear os regimes | p-valores com correção de Holm, silhouette, Davies-Bouldin, Calinski-Harabasz, estabilidade entre quinzenas (ARI) |
| **E2** | Detecção Normal/Residual | RQ1 | Perfil contextual versus baselines: (a) limiar fixo p99 sem contexto; (b) z-score global; (c) mesma janela da semana anterior. Comparações parciais: 2 versus 3 tipos de dia; sem contexto | Precisão, recall, F1 e PR-AUC por janela e por episódio; % de alarmes em janelas limpas; análise do feriado |
| **E3** | Consulta pré-incidente e caracterização do residual | RQ2 | Para cada episódio, registro sorteado dentro dele e análise das 6h anteriores; consultas de controle em períodos limpos | Sensibilidade, especificidade, erro no início (h), acurácia do lado provável por tipo e intensidade |
| **E4** | Atributos relevantes | RQ3 | Frequência com que cada atributo dispara o Residual, e z médio por tipo de falha | Tabela de atributos × tipo de falha |
| **E5** | Sensibilidade à janela (exploratório) | — | Repetir E2 e E3 com 15 min, 30 min, 1h e 4h | F1, erro no início, % de alarmes |

**Falhas injetadas** (01–07/09, aplicadas nos registros por minuto e cliente, depois reagregadas; 1 a 6 h, sem sobreposição; 10 sementes)
| Tipo | Lado | Baixa / Média / Alta |
|---|---|---|
| Latência elevada | provedor | ×1,5 / ×2,5 / ×4 |
| Pico de 5xx | provedor | 5% / 15% / 40% das respostas 2xx viram 5xx |
| Queda de volume | provedor | mantém 70% / 50% / 20% |
| 4xx concentrado em 1 cliente | consumidor | 30% / 60% / 90% das respostas 2xx do cliente viram 4xx |
| Rajada de 1 cliente | consumidor | volume ×2 / ×4 / ×8 |

## 7. Fases de execução (notebooks)
| Notebook | CRISP-DM | Objetivo | Processamento e algoritmos | Saídas | Exp. |
|---|---|---|---|---|---|
| **01_entendimento** | Negócio + Dados | Registrar o problema e os critérios de sucesso; avaliar a qualidade da base | Texto do negócio; cobertura e grade temporal; repetições; nulos; valores extremos (percentis); recursos e clientes por dia. Ferramenta: pandas | Relatório de qualidade; regras de validade | — |
| **02_preparacao** | Preparação | Gerar a tabela recurso × janela | Conversão UTC → Brasília; consolidação das repetições (soma do volume, média de latência ponderada pelo volume); cálculo dos atributos; contexto; divisão temporal. Ferramenta: pandas | `janelas_<janela>.parquet` | — |
| **03_caracterizacao_regimes** | Dados + Modelagem (descritiva) | Confirmar os vários normais por recurso e nomeá-los | Perfis e mapas de calor hora × tipo de dia; **Kruskal-Wallis** entre horas; **Mann-Whitney** útil × sábado e sábado × domingo, com Holm; **k-means** (`StandardScaler`, k de 2 a 8 por silhouette e cotovelo) com atributos de comportamento; cruzamento regime × contexto; ARI entre quinzenas | Figuras, tabela de regimes por recurso, decisão sobre 2 ou 3 tipos de dia | E1 |
| **04_normalidade** | Modelagem | Decidir Normal ou Residual e descrever o residual | **Perfil contextual:** mediana e MAD por recurso × hora × tipo de dia (reserva por recurso × hora quando há menos de 5 amostras); **z robusto direcional**; Residual se o maior z > τ, com τ calibrado em 25–31/08 para a meta de alarmes; início = primeira janela da sequência residual; **matriz heurística de lado** (abaixo) | Modelo por recurso, τ, estados | — |
| **05_injecao** | Preparação (gabarito) | Criar o conjunto de avaliação | 5 tipos × 3 intensidades; sorteio binomial (NumPy); 10 sementes; reagregação pelas mesmas funções do notebook 02 | Registros com falhas, tabela de episódios | E2–E5 |
| **06_avaliacao** | Avaliação | Responder RQ1 a RQ3 e conferir os critérios de sucesso | Baselines; métricas do sklearn (`precision_recall_fscore_support`, `average_precision_score`, `confusion_matrix`); métricas por episódio; consultas simuladas; média ± desvio-padrão nas sementes; feriado; repetição por janela | Tabelas e figuras do artigo | E2–E5 |
| **07_saida_agente** | Implantação (protótipo) | Entregar a informação ao agente e ao operador | `consultar()` → JSON com `motivo_estatistico` e `sugestao_triagem` gerados das evidências; 2 ou 3 estudos de caso; plano de uso (retreino mensal, recurso novo, feriados) | Função e exemplos | RQ2 |

**Atributos por janela:**
- volume (log);
- taxa de 4xx, taxa de 5xx;
- latência média das respostas 2xx (log);
- número de clientes (log);
- participação do maior cliente no volume;
- fração de clientes com 4xx, fração de clientes com 5xx;
- participação dos 2 maiores clientes nos erros.

**Direção desfavorável de cada atributo:** o volume e o número de clientes contam nos dois sentidos (alta e queda). Os demais contam só na alta.

**Matriz heurística do lado provável** (aplicada às janelas residuais; "concentrado" = os 2 maiores clientes respondem por ≥ 80% dos erros ou do volume adicional)
| Atributo com z > 3 | Abrangência | Lado provável |
|---|---|---|
| Latência 2xx | qualquer | Provedor |
| Taxa de 5xx | espalhado | Provedor |
| Taxa de 5xx | concentrado | Consumidor (ou dependência específica) |
| Taxa de 4xx | espalhado | Provedor (contrato ou validação) |
| Taxa de 4xx | concentrado | Consumidor |
| Volume ↓ e clientes ↓ | espalhado | Provedor ou rede antes do gateway |
| Volume ↑ com o maior cliente concentrando | concentrado | Consumidor (rajada ou retry) |
| Nenhuma regra aplicável | — | Indeterminado |

## 8. Ameaças à validade
- **Falhas sintéticas:** o desempenho mede a capacidade de detectar **os tipos injetados**, não falhas reais. As intensidades variadas e a comparação com baselines reduzem esse viés, mas não o eliminam.
- **Treino curto:** um mês. O perfil de sábado e o de domingo/feriado têm cerca de 5 amostras por hora, e as faixas ficam mais largas nesses dias.
- **Anomalias reais não rotuladas** no teste contam como falso alarme, o que torna a estimativa de alarmes conservadora.
- **Uma organização e 12 recursos:** a generalização para outras APIs fica como trabalho futuro.
- **Manutenções não recorrentes** saem como Residual. Isso é coerente com a definição, mas cabe ao operador cruzar com o calendário de mudanças.

## 9. Avaliação do revisor (disciplina de Mineração de Dados)
> O plano está bem estruturado e aderente ao CRISP-DM: critérios de sucesso definidos antes da modelagem, divisão temporal sem vazamento, baselines e comparações que isolam a contribuição do contexto. A opção por algoritmos simples e explicáveis (mediana e MAD por contexto, k-means só descritivo, heurística documentada) é adequada ao objetivo de apoiar um operador e fácil de defender. O ponto mais frágil é a **validade externa**: sem incidentes reais, a avaliação depende do gerador de falhas. Recomenda-se (i) validar 2 ou 3 casos reais qualitativamente com operadores, mesmo que fora do período; (ii) justificar o multiplicador do MAD e a meta de alarmes com uma curva de sensibilidade, em vez de um valor único; (iii) declarar explicitamente que os recursos com poucos clientes ou com o teste encerrado mais cedo são limitações. **Parecer: adequado para iniciar a construção.**
