Para estruturar o processamento dos dados e a obtenção dos resultados para a sua pesquisa, dividiremos o trabalho em **cinco cadernos (Jupyter Notebooks) sequenciais**. Essa divisão modular garante aderência estrita às fases do CRISP-DM e facilita a validação do *pipeline* para a construção do oráculo semântico que abastecerá o sistema multiagente.

Abaixo detalho as fases, os notebooks, os algoritmos e os objetivos de cada etapa.

---

### Notebook 1: Preparação de Dados e Engenharia de Atributos

* **Fase CRISP-DM:** Entendimento e Preparação dos Dados.


* **Objetivo:** Transformar o arquivo transacional em um formato de séries temporais estruturadas, criando o vetor de características necessário para a identificação de comportamentos.


* **Algoritmos/Ferramentas:** `pandas`, `numpy`.
* **Processamento:**
1. Carregar o arquivo bruto `APIs-Agr-20260801-20260908_hash.csv`.


2. Filtrar a execução iterativamente por recurso de API (`CD_RCS_CAT`), pois o comportamento de normalidade é individual por integração.


3. Agregar as métricas do nível de minuto (`TS_EVT`) para **janelas de 1 hora**, somando o volume total (`QT_TTL_TRAN`) e calculando a média ponderada de latência (`QT_TMP_MEDI_EXEA`).


4. Extrair os componentes temporais e aplicar **codificação cíclica trigonométrica (seno e cosseno)** para a hora do dia e dia da semana, garantindo a continuidade matemática do tempo.


5. Derivar atributos de proporção de erros (códigos HTTP 2xx, 4xx, 5xx baseados em `CD_RPST`) e calcular as médias e desvios móveis (tendência de variação temporal).


6. Dividir fisicamente os conjuntos de dados: **Treino** (01/08 a 31/08) e **Teste** (01/09 a 08/09).





### Notebook 2: Descoberta de Regimes Normais (Treinamento)

* **Fase CRISP-DM:** Modelagem Não Supervisionada.


* **Objetivo:** Descobrir empiricamente os envelopes autênticos de comportamento normal da API (os regimes) na base limpa de Agosto, definindo a identidade da classe **Normal**.


* **Algoritmos/Ferramentas:** `scikit-learn` (`StandardScaler`, `DBSCAN`, `K-Means`), `matplotlib`/`seaborn` (visualização).
* **Processamento:**
1. Padronizar as variáveis contínuas com `StandardScaler` para equilibrar pesos entre volume e latência.


2. Utilizar **K-Means** como *baseline* exploratório para confirmar a existência de faixas operacionais (ex: separar grosseiramente dia vs. noite).


3. Aplicar o algoritmo **DBSCAN (Density-Based Spatial Clustering of Applications with Noise)** nos dados de Agosto. Por ser baseado em densidade, o DBSCAN agrupará perfeitamente os regimes legítimos independentemente do formato geométrico dos dados (ex: regime de horário comercial, regime de manutenção/batch noturno).


4. Definir que todos os agrupamentos densos formados pelo DBSCAN são submúltiplos do macro-estado **Normal**, enquanto os pontos classificados nativamente como ruído pelo algoritmo formarão a base do que é um comportamento **Residual**.





### Notebook 3: Injeção Sintética de Falhas (Ground Truth)

* **Fase CRISP-DM:** Preparação dos Dados (Geração do Gabarito de Teste).


* **Objetivo:** Manipular a base de Setembro inserindo falhas de integração para testar rigorosamente se o modelo consegue identificar estados residuais.


* **Algoritmos/Ferramentas:** `pandas`, `numpy` (funções de perturbação estatística).
* **Processamento:**
1. Isolar a primeira semana de setembro (01/09 a 08/09).
2. Aplicar funções matemáticas para simular distúrbios realistas de arquitetura/integração em janelas específicas de 1 hora:


* *Cenário A (Gargalo de Infraestrutura):* Multiplicar a média da latência por 3x e reduzir o volume.


* *Cenário B (Falha na Aplicação Provedora):* Injetar aumento severo na proporção da família de erros HTTP 5xx.


* *Cenário C (Queda Abrupta):* Zerar o tráfego fora da janela de manutenção programada.




3. Criar a coluna alvo (*target*). Janelas alteradas recebem o rótulo de **Residual**; as demais seguem como **Normal**.





### Notebook 4: Classificação de Estados e Importância de Atributos

* **Fase CRISP-DM:** Modelagem Supervisionada e Avaliação.


* **Objetivo:** Treinar um classificador para mapear os dados em "Normal" ou "Residual" e isolar os atributos que justificaram a falha, gerando a "explicabilidade" necessária para o LLM.


* **Algoritmos/Ferramentas:** `scikit-learn` (`DecisionTreeClassifier`, `LogisticRegression`, métricas).
* **Processamento:**
1. Treinar uma **Árvore de Decisão** (`DecisionTreeClassifier`) com a base rotulada. A árvore é o algoritmo ideal porque suas regras de partição ("se latência > X e volume < Y") são facilmente traduzíveis em texto semântico.


2. Utilizar **Regressão Logística** como um classificador *baseline* simples para fins de comparação acadêmica de desempenho.


3. Testar a predição na base de setembro submetida à injeção de falhas e extrair métricas de desempenho (`precision`, `recall`, `F1-score`, matriz de confusão) para validar a eficácia do critério operacional.


4. Extrair o atributo `feature_importances_` para rastrear qual variável matemática teve peso decisivo em categorizar uma janela de Setembro como **Residual**.





### Notebook 5: Oráculo Semântico (Integração com Multiagentes)

* **Fase CRISP-DM:** Implantação (Deployment / Prova de Conceito).


* **Objetivo:** Consolidar a esteira analítica em uma simulação da API de contexto que fornecerá os dados formatados diretamente ao agente LLM da sua pesquisa de mestrado.


* **Algoritmos/Ferramentas:** Manipulação de texto em Python e serialização em JSON.
* **Processamento:**
1. Desenvolver uma função (o "Agente de Observabilidade") que recebe como parâmetros: `CD_RCS_CAT` e a janela de data/hora alvo do incidente.


2. A função busca os dados daquela hora, submete ao modelo da árvore (Notebook 4) e verifica o estado.


3. Caso o estado seja "Normal", devolve: *"Comportamento aderente ao perfil histórico."*
4. Caso o estado seja **Residual**, a função percorre a lógica da árvore, identifica a anomalia (ex: taxa 5xx alta) e devolve a saída semântica estruturada:
`{"API_Endpoint": "18917906", "Estado": "Residual", "Motivo_Estatistico": "Taxa de erro 5xx violou o limite do regime normal conhecido para o horário comercial", "Sugestao_Triagem": "Focar análise em indisponibilidade do sistema provedor."}`.


5. Esse JSON torna-se o insumo exato que desonera a carga cognitiva e direciona assertivamente a triagem no seu pré-projeto de mestrado.