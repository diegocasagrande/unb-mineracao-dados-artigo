# Normalidade Contextual em APIs — versões

Os dados ficam em `DADOS/` e são compartilhados pelas versões. Cada versão tem seus próprios notebooks, resultados e artigo, e roda de forma independente (executar os notebooks em ordem, de `01` a `07`; `00_funcoes` é carregado pelos demais).

## v1 — monitoração da semana de teste (arquivada)
- Pergunta: cada janela de 1 h da semana de 01–07/09 é Normal ou Residual? De que lado está o erro (provedor/consumidor)?
- Falhas injetadas em episódios ao longo da semana (5 tipos, incluindo volume).
- Artigo: `v1/artigo/main.pdf` · Overleaf: `v1/artigo_overleaf.zip`.

## v2 — estado no instante do registro do incidente
- Pergunta: no instante em que o incidente é registrado, o recurso está em regime normal? Se não, qual indicador (erros 4xx, erros 5xx, latência p95) e desde quando?
- Decisão sobre os 15 min anteriores ao registro, comparada ao perfil de 1 h; início por expansão retroativa (0–15, 15–30, 30–60 min, depois 1 h a 1 h até 4 h); abrangência (consumidor específico × generalizado) como complemento.
- Latência p95 ponderada das médias por minuto × cliente (substitui a média).
- Recursos identificados como E01–E12 (mapa em `v2/resultados/01_codigos.json`, não publicar).
- 3.600 incidentes simulados + 3.600 controles; limite de cada indicador = percentil 99 fora da amostra em agosto (ponto de operação escolhido após a primeira avaliação; a meta de 1% também é relatada).
- Artigo: `v2/artigo/main.pdf` · Overleaf: `v2/artigo_overleaf.zip`.

## v3 — mesma pergunta da v2, com a base de maio a setembro de 2026
- Dados: `DADOS/novoCj/APIs-CjAnterior-20260501-20260920-mes_hash.csv` (outra semente de anonimização de cliente; mesmos volumes da base de agosto no período comum).
- Teste em agosto (7 recursos) e 01–20/09 (12 recursos); cada mês é ajustado só com dados anteriores, com histórico de **3 meses** (principal) e de **1 mês** (comparação).
- Latência ×10 como 4º nível de intensidade; k-means mantido, com indicadores limitados aos percentis 1 e 99 (descritivo).
- 6.077 incidentes simulados + 6.080 controles.
- Artigo: `v3/artigo/main.pdf` · Overleaf: `v3/artigo_overleaf.zip`.

## v4 — novo conjunto de recursos de alto volume (atual)
- Dados: `DADOS/novoCj/APIs-NovoCj-20260501-20260920-mes_hash.csv` (13 GB, 118 milhões de linhas, 18 recursos), lido em blocos no notebook 01; o extrato fica em `v4/resultados/01_extrato.parquet`.
- Só recursos com dados em todos os dias de 01/06 a 20/09: 14 recursos (A01–A14, mapa em `v4/resultados/01_codigos.json`, não publicar); 4 descartados (21% do volume). O A10 é o E01 das versões anteriores.
- Histórico junho–agosto (3 meses, principal) e agosto (1 mês); teste em 01–20/09; 4.411 incidentes simulados + 4.480 controles.
- Artigo: `v4/artigo/main.pdf` · Overleaf: `v4/artigo_overleaf.zip`.

## v5 — reescrita do texto da versão final (sem nova execução)
- Base: `v2/artigo/versaoFinal.tex` (texto da v3 com as edições do autor); números e dados da **v3** (`v3/resultados`), nada foi reexecutado.
- Resultados e discussão no formato da v1 (Exp. 1–4 → critérios; discussão por RQ). Sem comparação entre faixas de 15/30/60 min: elas aparecem só como a estratégia de expansão retroativa para estimar o início do residual. RQ de tamanho da faixa removida (RQ4 → RQ3).
- Figuras com rótulo de 15 min regeradas a partir dos CSV/parquet da v3 por `v5/figuras_v5.py`; limites mostrados para as janelas de 1 h; volume por recurso em transações/h.
- Artigo: `v5/artigo/main-v5.pdf` · Overleaf: `v5/artigo_overleaf.zip`.

## v6 — teste do ponto de operação: percentil 85 no lugar do 99
- Cópia da v3 com `Q_LIMITE = 0.85` e `c = 1` fixo (`META_ALARMES = None` em `00_funcoes`); com a meta de 5% o `c` subiria e anularia a mudança. Piso de z = 3 mantido.
- Reaproveita as saídas 01–03 e 05 da v3 (mesmos dados e cenários); reexecutados só os notebooks 04, 06 e 07.
- Resultado (registro, 3 meses): sensibilidade 70,3% (média/alta 74,6%), especificidade 79,1%, indicador 89,1%, início 83,7%; perde para os baselines (McNemar p < 0,001). A maioria dos limites cai no piso de z = 3.

## v7 — regimes normais admissíveis por contexto (percentil 95)
- Cópia da v3 (mesmos dados e cenários; reexecutados 04, 06 e 07). Método proposto novo: classe `Regimes` em `00_funcoes` — k-means por recurso e por histórico (k 2–8 por silhouette, regime com ≥ 1% das janelas), mediana/MAD/p5–p95 por regime, regime **admissível** no contexto se ocorre em ≥ 5% das janelas do tipo de dia × hora (± 1 h). Normal = cabe nos limites de algum regime admissível.
- Limite = percentil 95 com `c = 1` fixo. Comparações: perfil por contexto (método da v5), regimes sem contexto, z-score global e semana anterior; curva com metas de 1%, 2%, 5% e 10%.
- Resultado (registro, 3 meses): sensibilidade 53,9%, especificidade 92,5%, indicador 90,4%, início 89,0%; sem contexto 44,0% (p < 0,001); com a mesma meta de alarmes, empata com os baselines.
- Artigo no estilo da v5: `v7/artigo/main-v7.pdf` · Overleaf: `v7/artigo_overleaf.zip`; figuras do artigo por `v7/figuras_v7.py`.

## v8 — perfil tipo de dia × hora (como na v5), decisão na hora anterior ao registro
- Cópia da v3 (mesmos dados, cenários e perfil; limite no percentil 99). Muda a decisão: o estado é decidido na **hora anterior ao registro** [t − 60 min, t), comparada ao perfil do contexto (tipo de dia × hora). Faixas menores que 1 h (15 e 30 min) entram **só** na expansão retroativa, para estimar o início (a partir da faixa residual mais recente). Em `00_funcoes`: `FAIXAS_L = [60]`, `L_PRINCIPAL = 60`, `TAMANHOS_FAIXA = [15, 30, 60]`.
- Resultado (3 meses): sensibilidade 36,3%, especificidade 97,1%, indicador 96,8%, início 90,4%, abrangência 85,4%; supera o z-score global (p = 0,032) e empata com a semana anterior.
- Variante com percentil 95 (sem meta de alarmes, c = 1): resultados em `v8/resultados/variante_p95/` (sensibilidade 55,6%, especificidade 88,5%).
- Artigo: `v8/artigo/main-v8.pdf` · Overleaf: `v8/artigo_overleaf.zip`; figuras do artigo por `v8/figuras_v8.py`.

## v9 — versão final
- Perfil por contexto: 48 regimes normais por recurso (dia útil e não útil × 24 horas), cada um com mediana, MAD e faixa p5–p95. Decisão na **hora anterior ao registro**; faixas de 15/30/60 min só na expansão retroativa (início). Limite de cada indicador no **percentil 97**, com `c = 1`.
- Cópia da v8 com `Q_LIMITE = 0.97` e `META_ALARMES = None`; reexecutados os notebooks 04, 06 e 07.
- Resultado (3 meses): sensibilidade 48,7%, especificidade 92,5%, indicador 93,5%, início 89,4%, abrangência 84,2%; supera o z-score global (p = 0,020) e empata com a semana anterior.
- Artigo: `v9/artigo/main-v9.pdf` · Overleaf: `v9/artigo_overleaf.zip`; figuras do artigo por `v9/figuras_v9.py`.

## v10 — processamento do texto do autor (`v2/artigo/versaoFinal22.tex`)
- Método da v3: decisão na faixa de 15 min, comparação de faixas 15/30/60 (RQ3), limite no percentil 99, históricos de 3 meses × 1 mês, baselines z-score global e semana anterior, expansão retroativa para o início.
- Dados limitados a **01/05/2026 0h – 19/09/2026 23h59** (Brasília), teste de setembro em 1–19/09 (`PERIODO_DADOS` em `00_funcoes`); notebooks 01–07 reexecutados.
- Artigo: texto do autor sem alterações além dos números corrigidos, da tabela de correlatos e da chave `siffer2017spot` no `.bib`; seções finais (Resultados, Discussão, Ameaças, Considerações finais) reescritas. `v10/artigo/main-v10.pdf` · Overleaf: `v10/artigo_overleaf.zip`.
- Versão em inglês (tradução fiel, sem mudança de conteúdo): `v10/artigo/main-v10-en.tex` / `.pdf`, com `referencias_en.bib` e figuras em `v10/artigo/figuras_en/` regeradas por `v10/figuras_v10_en.py` a partir de `v10/resultados` (sem reprocessar). Overleaf: `v10/artigo_overleaf_en.zip`. O `main-v10.tex` em português segue intocado.

## Seis técnicas usadas nas versões 2 a 4
1. Kruskal-Wallis com Bonferroni (o comportamento muda com a hora?)
2. k-means + silhouette (regimes normais, descritivo)
3. Mediana e MAD por recurso × tipo de dia × hora (perfil normal)
4. Limite por indicador calibrado por validação cruzada no histórico (decisão e indicador)
5. Expansão retroativa (início do desvio)
6. IC de Wilson + McNemar (confiabilidade e comparação com baselines)
