# Plano de fases e notebooks

**Premissas comuns a todos os notebooks**
- A análise é sempre **por recurso** (`CD_RCS_CAT`).
- Há dois estados: **Normal**, que pode ser qualquer um dos regimes normais esperados no contexto, e **Residual**, que é todo o resto.
- Treino em agosto de 2026; teste em 01–07/09 com falhas injetadas.
- Janela parametrizada, padrão 1h.
- Ferramentas: pandas, NumPy, SciPy, scikit-learn, statsmodels e Matplotlib.
- Funções compartilhadas ficam em `normalidade/`. Cada notebook começa com uma célula de parâmetros e grava suas saídas em `resultados/`.

---

### 00_entendimento_negocio · CRISP-DM: Entendimento do Negócio
**Objetivo:** documentar o problema e os critérios de sucesso antes de qualquer modelagem.
- **Problema:** subsidiar a triagem de incidentes, dizendo se o período antes do registro estava normal para cada recurso e, se não estava, como estava.
- **Premissas:** vários regimes normais por recurso; dois estados; decisão por recurso.
- **Critérios de sucesso** (valores propostos, você ajusta):
  - Técnicos: F1 por episódio maior que o dos baselines; até 2% de janelas limpas marcadas como residual; erro no início estimado de até 1 janela.
  - De negócio: acurácia do lado provável (provedor ou consumidor) de pelo menos 70%.
- **Riscos e limitações:** não há incidentes reais; o teste inclui um feriado; 4 recursos param em 03/09; o recurso `17834257` tem 1 ou 2 clientes.
- **Algoritmos:** nenhum; é só texto.

### 01_qualidade_dados · CRISP-DM: Entendimento dos Dados
**Objetivo:** mostrar que a base é confiável e documentar as regras de validade.
- **Análises:** período e cobertura por recurso; minutos sem registro; chaves repetidas; valores nulos e inválidos; distribuição de volume e latência; latências extremas; recursos e clientes por dia.
- **Técnicas:** contagens e grade temporal completa em pandas, percentis, regra IQR/percentil para valores extremos.
- **Saída:** relatório de qualidade (tabela para o artigo) e a lista de regras de validade usadas no notebook 02.

### 02_preparacao · CRISP-DM: Preparação dos Dados
**Objetivo:** produzir a tabela recurso × janela que alimenta todos os modelos.
- **Consolidação:** as linhas repetidas viram uma só, somando o volume e usando a média de latência ponderada pelo volume.
- **Atributos por janela:**

| Grupo | Atributos |
|---|---|
| Volume | log do volume |
| Erros | taxa de 4xx, taxa de 5xx |
| Latência | log da latência média das respostas 2xx |
| Clientes | log do número de clientes, participação do maior cliente no volume, fração de clientes com 4xx, fração de clientes com 5xx |
| Contexto | hora, tipo de dia (útil / não útil, ou útil / sábado / domingo-feriado, conforme o notebook 03) |

- **Divisão temporal:** treino em agosto, com a última semana de agosto separada para calibrar o limiar; teste de 01 a 07/09.
- **Técnicas:** `groupby`/`floor` do pandas e média ponderada.
- **Saída:** um parquet de janelas por tamanho de janela.

### 03_caracterizacao · CRISP-DM: Entendimento dos Dados
**Objetivo:** confirmar empiricamente que cada recurso tem **vários comportamentos normais** ligados ao contexto (é a evidência para a RQ1).
- **Perfis:** mediana e intervalo interquartil por hora × tipo de dia, com mapas de calor e curvas por recurso.
- **Sazonalidade:** autocorrelação (ACF do statsmodels) nas defasagens de 24h e 168h. Opcionalmente, decomposição STL com período de 24h.
- **Testes estatísticos:**
  - Kruskal-Wallis entre as horas do dia: o comportamento varia com a hora?
  - Mann-Whitney entre dia útil e não útil, e entre sábado e domingo, com correção de Holm.
  - O resultado decide quantas categorias de tipo de dia usar e volta para o notebook 02.
- **Saída:** figuras com os regimes visíveis (lote das 3h, das 19h, madrugada, fim de semana) e a decisão sobre as categorias de tipo de dia.

### 04_regimes · CRISP-DM: Modelagem (descoberta)
**Objetivo:** descobrir e nomear os regimes normais de cada recurso e saber quais são esperados em cada contexto.
- **Algoritmos:**
  - Padronização com `StandardScaler`.
  - **k-means** com k de 2 a 8, escolhido pelo silhouette e pelo método do cotovelo.
  - Para comparar: **agrupamento hierárquico ward**, com dendrograma (scipy).
  - O DBSCAN fica opcional.
- **Qualidade dos regimes:** silhouette, Davies-Bouldin e Calinski-Harabasz.
- **Estabilidade:** ajustar na 1ª quinzena, ajustar na 2ª, e comparar as duas partições pelo índice ARI.
- **Regime por contexto:** uma tabela de contingência regime × (hora, tipo de dia) dá os regimes esperados em cada contexto.
- **Nomes dos regimes:** atribuídos depois, olhando as medianas dos atributos de cada um (por exemplo, "lote 3h", "madrugada", "comercial").
- **Saída:** número e descrição dos regimes por recurso, e o mapa de contexto para regimes.

### 05_injecao_falhas · CRISP-DM: Preparação dos Dados (conjunto de avaliação)
**Objetivo:** criar o gabarito da semana de teste.
- **Falhas:**

| Tipo | Lado | Como é injetada |
|---|---|---|
| Latência elevada | provedor | latência multiplicada por 1,5, 2,5 ou 4 |
| Pico de 5xx | provedor | 5%, 15% ou 40% das respostas 2xx viram 503 |
| Queda de volume | provedor | mantém 70%, 50% ou 20% do volume |
| 4xx concentrado | consumidor | um cliente tem 30%, 60% ou 90% das respostas 2xx convertidas em 400 |
| Rajada | consumidor | um cliente com volume multiplicado por 2, 4 ou 8 |

- Duração de 1 a 6h, sem sobreposição entre episódios, aplicada nos registros por minuto e cliente e depois reagregada pelo notebook 02.
- **Técnicas:** sorteio binomial (NumPy), semente fixa, **10 repetições** com sementes diferentes.
- **Saída:** registros com as falhas injetadas e a tabela de episódios (recurso, tipo, intensidade, lado, início, fim).

### 06_modelo_normalidade · CRISP-DM: Modelagem (decisão Normal/Residual)
**Objetivo:** classificar cada janela como Normal ou Residual e descrever o residual.
- **Modelo A, perfil contextual:** mediana e MAD por recurso × hora × tipo de dia. Cada atributo recebe um z robusto contando só a direção desfavorável, e o escore da janela é o maior deles.
- **Modelo B, regimes contextuais:** a distância da janela ao centróide mais próximo **entre os regimes esperados naquele contexto**, dividida pela tolerância do regime (percentil 99 das distâncias no treino).
- **Limiar:**
  - ajustar com 01–24/08;
  - calibrar o limiar em 25–31/08, com a meta de até 1–2% de janelas residuais;
  - reajustar o modelo com agosto inteiro, mantendo o limiar.
- **Características do residual:** início (primeira janela da sequência), duração, atributos fora da faixa (z > 3), abrangência entre clientes e lado provável, este último por uma regra simples a partir das evidências.
- **Saída:** estado e características de cada janela.

### 07_avaliacao · CRISP-DM: Avaliação
**Objetivo:** responder se o modelo separa Normal de Residual e se a informação ajuda a triagem.
- **Baselines:** limiar fixo p99 sem contexto, z-score global e "mesma janela da semana anterior". Mais as variantes do modelo B **sem contexto**, para medir o ganho de usar o contexto.
- **Detecção:** precisão, recall, F1 e PR-AUC por janela e por episódio (cada episódio conta uma vez), por recurso, por tipo de falha e por intensidade.
- **Consulta pré-incidente simulada:** para cada episódio, um incidente é registrado no instante t, e o modelo olha as 6h anteriores. Medir sensibilidade, especificidade (com consultas de controle em períodos limpos) e o erro no início estimado, em horas.
- **Triagem:** acurácia do lado provável.
- **Falsos alarmes:** taxa em janelas limpas, com análise à parte do feriado de 07/09.
- **Estatística:** média e desvio-padrão nas 10 sementes, intervalo de confiança de 95% por bootstrap e teste de McNemar para comparar métodos por episódio.
- **Saída:** tabelas e figuras de resultado, e confronto com os critérios de sucesso do notebook 00.

### 08_importancia_atributos · CRISP-DM: Avaliação (RQ3)
**Objetivo:** mostrar quais atributos mais distinguem o residual e o tipo e lado da falha.
- **Algoritmos:**
  - **Árvore de decisão rasa** (profundidade 3–4) treinada nos z das janelas residuais, para prever o tipo de falha e o lado;
  - `feature_importances_` e `permutation_importance`;
  - frequência com que cada atributo dispara o residual em cada tipo de falha.
- **Saída:** ranking de atributos e a árvore desenhada, com regras legíveis para o artigo.

### 09_sensibilidade_janela · CRISP-DM: Avaliação (exploratória)
**Objetivo:** verificar se 1h é de fato a janela mais adequada.
- **Processo:** repetir os notebooks 02, 06 e 07 com janelas de 15 min, 30 min, 1h e 4h.
- **Comparação:** F1, erro no início estimado, taxa de falsos alarmes e número de regimes por recurso.
- **Saída:** tabela comparativa e a justificativa para a janela escolhida.

### 10_saida_agente · CRISP-DM: Implantação (protótipo)
**Objetivo:** entregar a informação no formato que o agente ou o operador vai consumir.
- **`consultar(recurso, t_registro, horas_antes)`** devolve um JSON com:
  - o regime esperado;
  - o estado (Normal ou Residual);
  - o início estimado e a duração do residual;
  - as evidências (valor observado versus faixa normal);
  - a abrangência entre clientes;
  - o lado provável.
- **Estudo de caso:** 2 ou 3 episódios mostrados de ponta a ponta.
- **Plano de uso:** retreino mensal, recurso novo sem histórico, atualização do calendário de feriados.

---

## Ligação com as questões de pesquisa e o artigo
| Questão | Notebooks | Seção do artigo |
|---|---|---|
| RQ1: os logs agregados caracterizam os regimes normais e separam o residual? | 03, 04, 06, 07 | Entendimento dos Dados, Resultados |
| RQ2: a caracterização do residual é útil para a triagem? | 07 (início do residual, lado provável), 10 | Resultados, Estudo de caso |
| RQ3: quais atributos são mais relevantes? | 08 | Resultados |
| Qual é a janela de agregação adequada? | 09 | Discussão |

Quer que eu salve este plano como `PLANO.md` no projeto e comece pelos notebooks 00 e 01?