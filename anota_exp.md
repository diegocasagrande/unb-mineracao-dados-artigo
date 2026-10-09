Os seis itens são técnicas estatísticas do artigo v10 ([main-v10.tex](v10/artigo/main-v10.tex)). Explico cada uma e como ela é usada no trabalho.

---

### 1. IC de Wilson
É o **intervalo de confiança de uma proporção**, como sensibilidade, especificidade ou acurácia do indicador. Ele dá a faixa onde o valor verdadeiro provavelmente está, com 95% de confiança.

Com p̂ = proporção observada, n = número de casos e z = 1,96:

$$\frac{\hat p + \frac{z^2}{2n} \pm z\sqrt{\frac{\hat p(1-\hat p)}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$

- **Por que Wilson e não o intervalo "comum" (p̂ ± 1,96·√(p̂(1−p̂)/n))?** O comum funciona mal perto de 0% ou 100% e quando há poucos casos. Ele pode até ultrapassar 100%. Vários dos seus números estão nessa região: especificidade de 97% e indicador correto de 96%.
- **Exemplo do artigo:** início na zona estimada = 91,7% [90,5; 92,7], com n = 2.389. Refiz a conta com a fórmula e o resultado bate.

### 2. MAD de volume
O **MAD** (*Median Absolute Deviation*, desvio absoluto mediano) mede a dispersão de forma robusta. O cálculo tem três passos:
1. Calcular a mediana dos valores.
2. Calcular a distância de cada valor até essa mediana.
3. Tirar a mediana dessas distâncias.

Ele é multiplicado por **1,4826** para ficar na mesma escala do desvio-padrão. O desvio de uma janela vira um z robusto:

$$z = \frac{x - \text{mediana}}{1{,}4826 \cdot \text{MAD}}$$

**Exemplo:** volumes às 10h de dias úteis = 1000, 1100, 950, 1050, 5000.
- Mediana = 1050.
- Distâncias até a mediana = 50, 50, 100, 0, 3950. O MAD é 50, e a escala fica ≈ 74.
- O pico de 5000 **não infla a escala**. Com o desvio-padrão, a escala ficaria em torno de 1.800.

É por isso que o MAD serve para montar o "normal" a partir de um histórico que contém incidentes.

Para o **volume** há três particularidades:
- Ele é usado em log.
- Faixas de 15 e 30 min são convertidas para a escala horária: ×4 e ×2.
- Ele é **bilateral**: tanto queda quanto aumento contam como desvio.

Para 4xx, 5xx e latência, só aumento conta. A escala tem um valor mínimo para evitar divisão por quase zero.

### 3. Limite de cada indicador por recurso (z)
Cada indicador tem variabilidade diferente em cada recurso. Por isso não se usa um único limiar fixo, como "z > 3". Cada par recurso × indicador recebe o seu limite:

$$L_{r,a} = \max\{3,\; Q_{0,99}(d_a)\}$$

Ou seja, o limite é o **percentil 99 dos desvios desse indicador no histórico**, com piso 3. Esses desvios são calculados **fora da amostra**, por validação cruzada em 4 blocos de tempo: o perfil é ajustado em 3 blocos e medido no 4º. Isso evita que o limite saia otimista.

- **Decisão:** a janela é Residual se algum indicador tiver d/L > 1. O **indicador responsável** é o que mais ultrapassou o seu limite, em múltiplos dele.
- **Exemplo:** o 4xx do E04 tem limite 86, porque o recurso tem picos de erro de negócio reais e frequentes. Já o 5xx de um recurso estável fica no piso 3. Com um limiar único, o 4xx ruidoso dispararia o tempo todo ou esconderia os demais indicadores.
- O limite é recalculado para cada tamanho de faixa (15, 30 e 60 min), porque faixas curtas oscilam mais.

### 4. Avaliação: Wilson e McNemar
São dois papéis diferentes:
- **Wilson:** a incerteza de *uma* proporção, ou seja, de cada métrica isolada.
- **McNemar (exato):** a comparação de **dois métodos aplicados aos mesmos cenários**, que são dados pareados. Os casos se dividem assim:

|  | Baseline acerta | Baseline erra |
|---|---|---|
| **Perfil acerta** | a | **b** |
| **Perfil erra** | **c** | d |

O teste só usa os casos discordantes, b e c. Se os métodos fossem equivalentes, b e c seriam parecidos; formalmente, b ~ Binomial(b+c; 0,5). Um p pequeno indica diferença real.
- **Por que não comparar as acurácias com um teste comum?** Porque as amostras não são independentes: os incidentes são os mesmos nos dois métodos.
- **No artigo:**
  - Perfil vs z-global em 15 min: p = 0,12, empate.
  - Em 30 min: p = 0,009, o perfil é melhor.
  - Histórico 1m vs 3m: p < 0,001.

### 5. Testes de Kruskal-Wallis
É uma **ANOVA não paramétrica**: verifica se uma variável tem a mesma distribuição em vários grupos. Ela trabalha com os **postos** (a ordem dos valores) e não com os valores em si, então não exige normalidade. Isso é importante aqui, porque volume, taxas de erro e latência têm caudas pesadas.

- **No artigo:** para cada recurso × indicador, o teste verifica se o indicador muda entre as **24 horas dos dias úteis**. Hipótese nula: todas as horas têm a mesma distribuição.
- **Bonferroni:** são 12 recursos × 4 indicadores = 48 testes. Por isso o α é dividido por 48, para não achar significância por acaso.
- **ε² (tamanho de efeito):** mostra *quanto* a hora explica, não só se o efeito existe. Resultado:
  - 96% dos testes foram significativos.
  - Efeito grande em volume (0,40), 4xx (0,28) e latência (0,25).
  - Efeito pequeno em 5xx (0,05).
- **Para que serve:** é a evidência de que existem regimes ligados ao horário. Isso justifica o perfil por contexto (tipo de dia × hora).

### 6. "2 a 8 no k-means"
É a **faixa de valores de k (número de grupos) testada** no k-means de cada recurso. Para cada k de 2 a 8:
1. Rodar o k-means.
2. Calcular o **silhouette médio**. Para cada ponto, s = (b − a)/max(a, b), onde a = distância média ao próprio grupo e b = distância média ao grupo vizinho mais próximo. O valor vai de −1 a 1, e quanto maior, mais separados os grupos.
3. Ficar com o k de maior silhouette.

Os extremos da faixa têm motivos práticos:
- **Por que começar em 2:** o silhouette não existe para k = 1.
- **Por que parar em 8:** acima disso, os grupos viram fragmentos difíceis de nomear como regimes operacionais.

O resultado foi mediana 3 e silhouette médio 0,51. O k-means é **só descritivo**: a decisão Normal/Residual usa o perfil contextual (mediana/MAD).

**Ponto de atenção:** na [tabela de recursos](v10/artigo/main-v10.tex#L289), o **E10 escolheu k = 8**, justamente o teto da faixa, com silhouette baixo (0,29). Um avaliador pode perguntar se o ótimo seria maior que 8. Vale uma frase dizendo que o E10 tem só 2 clientes, que a estrutura dele é fraca (silhouette 0,29) e que, como o k-means é descritivo, isso não afeta a decisão.



O **z-score** mede **quantos "desvios típicos" um valor está afastado do normal**. Ele coloca indicadores com unidades diferentes (ms, %, contagem) na mesma régua.

### Forma clássica

$$z = \frac{x - \mu}{\sigma}$$

- x = valor observado
- μ = média histórica
- σ = desvio-padrão histórico

**Exemplo:** a latência média é 100 ms, com σ = 20 ms. Uma observação de 160 ms dá z = (160 − 100)/20 = **3**: está 3 desvios acima do normal. Se os dados fossem normais (gaussianos), valores com |z| > 3 aconteceriam só em ~0,3% das vezes. Daí a regra tradicional "z > 3 é anomalia".

### O problema da forma clássica nos seus dados
A média e o desvio-padr são **puxados pelos próprios outliers**. Se o histórico tem picos de incidentes, σ fica inflado, e um desvio real passa a parecer pequeno.

**Exemplo:** volumes de 1000, 1100, 950, 1050 e 5000.
- Média ≈ 1820 e σ ≈ 1780.
- O pico de 5000 dá z ≈ 1,8, que parece "normal".

### Forma robusta (a do seu trabalho)
A média é trocada pela **mediana** e o σ pelo **MAD × 1,4826**:

$$z = \frac{x - \text{mediana}}{1{,}4826 \cdot \text{MAD}}$$

No mesmo exemplo:
- Mediana = 1050, MAD = 50, escala ≈ 74.
- z = (5000 − 1050)/74 ≈ **53**, claramente anômalo.

O fator 1,4826 faz a escala robusta coincidir com σ quando os dados são normais. Assim, o z robusto "fala a mesma língua" do clássico.

### Como ele aparece no artigo

1. **Z contextual (o método proposto).** A mediana e o MAD são calculados **por recurso × contexto (tipo de dia × hora) × indicador**. Isso responde à pergunta "esse valor é estranho *para este recurso, às 0h de um dia útil*?". O lote da meia-noite tem volume alto, mas z baixo, porque é comparado com outras meias-noites.

2. **Z-score global (baseline).** É a mesma conta, mas com **uma única mediana/MAD por recurso**, ignorando hora e tipo de dia. O lote da meia-noite pode virar z alto só por ser diferente da média do dia. A comparação com esse baseline testa se o contexto agrega valor.

3. **Sentido do desvio.** Para o volume conta |z|: queda ou aumento. Para 4xx, 5xx e latência, só z positivo: piora.

4. **Limite.** Em vez do "z > 3" fixo, cada indicador do recurso tem um limite L = max{3, percentil 99 do z no histórico}. Os dados reais têm caudas pesadas: o 4xx do E04 chega a z = 86 em dias normais. Por isso o "3" da teoria gaussiana viraria alarme constante.

Em uma frase: o z-score transforma "4,1% de 5xx" em "isso está X escalas de variação acima do que é normal neste recurso, neste horário". É essa régua comum que permite comparar 4xx, 5xx, latência e volume e apontar o indicador responsável.

Segue um resumo curto de cada conceito, com uma ideia central e um exemplo.

| Conceito | O que é, em uma frase | Exemplo no trabalho |
|---|---|---|
| **z-score** | Diz quantas vezes um valor está acima ou abaixo do normal, medido na escala de variação típica. | z = 5 quer dizer "5 vezes a variação normal acima do esperado". |
| **MAD** | Mede a variação típica pela mediana, então um pico isolado não estraga o "normal". | Volumes 1000, 1100, 950, 1050, 5000 → a variação típica fica em ~74, e não ~1.800. |
| **z robusto** | É o z-score calculado com mediana e MAD, em vez de média e desvio-padrão. | Com essa conta, o pico de 5000 dá z ≈ 53 e fica claro que é anômalo. |
| **Limite por indicador** | Cada indicador de cada recurso tem o seu próprio "quanto é demais": o percentil 99 do histórico, nunca abaixo de 3. | O 4xx do E04 só alarma acima de z = 86, porque ele oscila muito. Um 5xx estável alarma acima de 3. |
| **Kruskal-Wallis** | Teste que verifica se um indicador muda conforme a hora do dia. | Em 96% dos casos mudou, o que prova que a referência precisa ser por hora. |
| **k-means (k de 2 a 8)** | Agrupa as horas parecidas em "regimes". Testa de 2 a 8 grupos e fica com o número que separa melhor (silhouette). | No E02 aparecem regimes como horário comercial, madrugada, fim de semana e o lote da meia-noite. |
| **IC de Wilson** | A margem de erro de uma porcentagem. | Especificidade de 97,1%, com o valor real provavelmente entre ~96,6% e ~97,5%. |
| **McNemar** | Compara dois métodos nos mesmos casos, olhando só onde eles discordam. | Perfil contra z-global: p = 0,12, ou seja, empate. |

### Como eles se encaixam
1. O **Kruskal-Wallis** e o **k-means** mostram que o "normal" muda com a hora e o dia.
2. Por isso, o normal é calculado **por recurso × hora × tipo de dia**, usando **mediana e MAD**.
3. Cada nova janela vira um **z robusto**, que é comparado ao **limite próprio** de cada indicador. Se algum indicador passa do limite, a janela é Residual, e o indicador que mais passou é apontado como responsável.
4. Para avaliar o método, o **Wilson** dá a margem de erro dos resultados. O **McNemar** diz se ele é melhor que os métodos de comparação (z-score global e semana anterior).



A divisão segue a tabela de fases do próprio artigo ([main-v10.tex:150-160](v10/artigo/main-v10.tex#L150-L160)).

| Fase CRISP-DM | Notebook | Técnica | Para que serve nessa fase |
|---|---|---|---|
| **1. Entendimento do negócio** | 01 | (nenhuma das técnicas) | Define a pergunta: o recurso está normal no registro do incidente? Se não, qual indicador mudou e desde quando? Também fixa os critérios de sucesso. |
| **2. Entendimento dos dados** | 03 | **Kruskal-Wallis** (+ Bonferroni) | Prova que os indicadores mudam com a hora do dia. |
| | 03 | **k-means (k de 2 a 8) + silhouette** | Descreve os regimes de cada recurso, como lote, horário comercial e fim de semana. É só descritivo. |
| **3. Preparação dos dados** | 02 | (percentil p95) | Monta as janelas e os indicadores: volume, 4xx, 5xx e latência p95. |
| | 05 | (injeção de falhas) | Cria os incidentes simulados e os controles para o teste. |
| **4. Modelagem** | 04 | **Mediana + MAD** | Define o "normal" de cada recurso × tipo de dia × hora. |
| | 04 | **z robusto** | Mede o quanto cada janela se afasta desse normal. |
| | 04 | **Limite por indicador** (p99, mínimo 3, validação cruzada) | Define o "quanto é demais" para cada indicador de cada recurso. A janela é Residual se passar do limite. |
| **5. Avaliação** | 06 | **IC de Wilson** | Dá a margem de erro de cada métrica (sensibilidade, especificidade, indicador correto, início). |
| | 06 | **McNemar** | Compara o método com os métodos de comparação (z-global e semana anterior) e com o histórico de 1 mês contra 3 meses. |
| **6. Implantação** | 07 | (saída estruturada) | Entrega ao agente ou ao operador o estado, o indicador, a faixa normal, o limite e o início estimado. |

### Fluxo resumido
- **Dados:** o Kruskal-Wallis e o k-means mostram que o normal depende do contexto.
- **Modelagem:** com mediana e MAD por contexto, cada janela vira um z robusto, que é comparado ao limite de cada indicador.
- **Avaliação:** o Wilson dá a margem de erro dos resultados, e o McNemar diz se o método é melhor que as alternativas.

O Kruskal-Wallis e o k-means ficam na fronteira entre **dados e modelagem**. No artigo, o notebook 03 aparece como "Dados, Modelagem". Eles não geram o modelo de decisão, mas justificam a escolha de usar contexto (hora × tipo de dia) na modelagem.