"""Gera as figuras do artigo v10 com rótulos em inglês (versão main-v10-en.tex).
Não reexecuta o pipeline: carrega as funções de v10/notebooks/00_funcoes.ipynb, lê os resultados salvos em
v10/resultados e grava em v10/artigo/figuras_en. As figuras originais (v10/artigo/figuras) não são alteradas.
O desenho de cada figura é o mesmo dos notebooks 03, 04 e 06 da v10; só os textos foram traduzidos."""
import json
import os
import pickle
from pathlib import Path

V10 = Path(__file__).resolve().parent
os.chdir(V10 / "notebooks")  # 00_funcoes resolve os caminhos a partir da pasta notebooks

for celula in json.loads((V10 / "notebooks/00_funcoes.ipynb").read_text())["cells"]:
    if celula["cell_type"] == "code":
        codigo = "".join(l for l in celula["source"] if not l.lstrip().startswith(("%", "!")))
        exec(codigo.replace("print(", "(lambda *a, **k: None)("), globals())

from matplotlib.patches import Patch  # noqa: E402

FIG_EN = V10 / "artigo/figuras_en"
FIG_EN.mkdir(parents=True, exist_ok=True)


def salvar(fig, nome):
    fig.savefig(FIG_EN / f"{nome}.pdf")
    fig.savefig(FIG_EN / f"{nome}.png")
    plt.close(fig)


DIA_EN = {"util": "business day", "nao_util": "non-business day"}
IND_EN = {"volume": "volume", "erros 4xx": "4xx errors", "erros 5xx": "5xx errors", "latência p95": "p95 latency"}
MOT_EN = {"4xx generalizado": "widespread 4xx", "4xx de 1 consumidor": "4xx from 1 consumer",
          "5xx generalizado": "widespread 5xx", "5xx de 1 consumidor": "5xx from 1 consumer", "latência": "latency"}
INT_EN = {"baixa": "low", "média": "medium", "alta": "high", "muito alta": "very high"}
MET_EN = {"Perfil contextual (proposto)": "Contextual profile (proposed)", "z-score global": "Global z-score",
          "Semana anterior": "Previous week"}
REGIME_EN = [("volume baixo", "low volume"), ("volume médio", "medium volume"), ("volume alto", "high volume"),
             ("4xx alto", "high 4xx"), ("5xx alto", "high 5xx"), ("latência alta", "high latency"),
             ("todos os dias", "all days"), ("dia útil", "business day"), ("não útil", "non-business day"),
             ("esporádico", "sporadic")]


def regime_en(nome):
    for pt, en in REGIME_EN:
        nome = nome.replace(pt, en)
    return nome


# ---- notebook 03: perfis, mapa de calor e regimes (maio a agosto) ----
jan = pd.read_parquet(RESULTADOS / "02_janelas_60min.parquet")
tr = recortar(jan, TREINO)
recursos = sorted(tr["recurso"].unique(), key=rot)
REPRESENTATIVOS = sorted([r for r in recursos if rot(r) in ("E01", "E05", "E12", "E02")], key=rot)

fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.2), sharex=True)
for ax, r in zip(axes.flat, REPRESENTATIVOS):
    g = tr[tr["recurso"] == r].groupby(["tipo_dia", "hora"])["vol"].median().unstack(0) / 1000
    for td in ["util", "nao_util"]:
        ax.plot(g.index, g[td], color=COR_DIA[td], lw=1.6, label=DIA_EN[td])
    ax.set_title(f"Resource {rot(r)}", loc="left")
    ax.set_xticks(range(0, 24, 3))
    ax.set_ylim(bottom=0)
    ax.set_ylabel("thousand transactions/h")
    ax.grid(axis="x", visible=False)
for ax in axes[1]:
    ax.set_xlabel("hour (Brasília time)")
axes[0, 0].legend(loc="upper right")
fig.suptitle("Median volume by hour and day type (May to August)", x=0.01, ha="left", fontsize=9, fontweight="bold")
fig.tight_layout()
salvar(fig, "fig_perfis_volume")

fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)
for ax, (titulo, col) in zip(axes, [("Volume (business days)", "vol"), ("p95 latency (business days)", "lat_p95")]):
    m = tr[tr["tipo_dia"] == "util"].groupby(["recurso", "hora"])[col].median().unstack().loc[recursos]
    m = m.div(m.max(axis=1), axis=0)
    im = ax.imshow(m.to_numpy(), aspect="auto", cmap=CMAP_SEQ, vmin=0, vmax=1)
    ax.set_title(titulo, loc="left")
    ax.set_xticks(range(0, 24, 3))
    ax.set_xlabel("hour (Brasília time)")
    ax.set_yticks(range(len(m)))
    ax.set_yticklabels([rot(r) for r in m.index], fontsize=6.5)
    ax.grid(False)
cb = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02)
cb.set_label("value / resource maximum", color=TXT2)
cb.outline.set_visible(False)
salvar(fig, "fig_mapa_calor")

slots = pd.read_csv(RESULTADOS / "03_regime_por_contexto.csv")
nomes_todos = json.loads((RESULTADOS / "03_resumo.json").read_text())["nomes"]
regimes = pd.read_csv(RESULTADOS / "03_regimes.csv", index_col=0)
EXEMPLO = [r for r in recursos if rot(r) == "E02"][0]
d = slots[slots["recurso"] == EXEMPLO].pivot(index="tipo_dia", columns="hora", values="regime").loc[["util", "nao_util"]]
k = int(regimes.loc[rot(EXEMPLO), "k"])
fig, ax = plt.subplots(figsize=(7.0, 1.55))
ax.imshow(d.to_numpy(), aspect="auto", cmap=ListedColormap(CORES[:k]), vmin=-0.5, vmax=k - 0.5)
ax.set_yticks(range(2))
ax.set_yticklabels([DIA_EN[t] for t in d.index])
ax.set_xticks(range(24))
ax.set_xticklabels(range(24), fontsize=6.5)
ax.set_xlabel("hour (Brasília time)")
ax.grid(False)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.set_xticks(np.arange(-0.5, 24, 1), minor=True)
ax.set_yticks(np.arange(-0.5, 2, 1), minor=True)
ax.grid(which="minor", color="white", linewidth=1.5)
ax.tick_params(which="minor", length=0)
ax.legend(handles=[Patch(color=CORES[c], label=regime_en(nomes_todos[rot(EXEMPLO)][str(c)])) for c in range(k)],
          loc="upper left", bbox_to_anchor=(0, -0.55), ncol=2, fontsize=6.5)
ax.set_title(f"Predominant regime by context · resource {rot(EXEMPLO)}", loc="left")
salvar(fig, "fig_regimes_contexto")

# ---- notebook 04: limites por indicador ----
lim_csv = pd.read_csv(RESULTADOS / "04_limites.csv", header=[0, 1], index_col=0)
fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.1), sharey=True)
for ax, L in zip(axes, (15, 60)):
    v = lim_csv[str(L)]
    ax.imshow(np.log10(v.to_numpy()), cmap=CMAP_SEQ, vmin=np.log10(3), vmax=2, aspect="auto")
    for i in range(v.shape[0]):
        for j in range(v.shape[1]):
            ax.text(j, i, f"{v.iat[i, j]:.0f}", ha="center", va="center", fontsize=6.3,
                    color="white" if np.log10(v.iat[i, j]) > 1.45 else TXT1)
    ax.set_xticks(range(v.shape[1]))
    ax.set_xticklabels([IND_EN[c] for c in v.columns], rotation=20, ha="right")
    ax.set_yticks(range(v.shape[0]))
    ax.set_yticklabels(v.index)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(f"{L}-min band", loc="left")
fig.suptitle("Limit of each indicator by resource (z) · June–August history", x=0.01, ha="left", fontsize=9,
             fontweight="bold")
fig.tight_layout()
salvar(fig, "fig_limites")

# ---- notebook 06: avaliação ----
dec = pd.read_parquet(RESULTADOS / "06_decisoes.parquet")
T_all = {(n, L, h): dec.loc[f"{n} | {L} | {h}"] for n in METODOS for L in FAIXAS_L for h in HISTORICOS}
T = {(n, L): T_all[(n, L, HIST_PRINCIPAL)] for n in METODOS for L in FAIXAS_L}
inc = lambda t: t[t["tipo"] == "incidente"]
ctl = lambda t: t[t["tipo"] == "controle"]

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.2), sharey=True)
metodos = list(METODOS)
for ax, (col, titulo) in zip(axes, [("sens_ma", "Sensitivity (medium/high intensity)"), ("espec", "Specificity (controls)")]):
    for j, L in enumerate(FAIXAS_L):
        for i, n in enumerate(metodos):
            t = T[(n, L)]
            base = inc(t)[inc(t)["intensidade"].isin(["media", "alta"])] if col == "sens_ma" else ctl(t)
            k = int(base["residual"].sum()) if col == "sens_ma" else int((~base["residual"].astype(bool)).sum())
            p = k / len(base)
            lo, hi = wilson(k, len(base))
            y = i + (j - 1) * 0.22
            ax.errorbar(p, y, xerr=[[p - lo], [hi - p]], fmt="o", ms=4, color=CORES[j], ecolor=CORES[j], lw=1,
                        capsize=1.5, label=f"{L} min" if i == 0 else None)
    ax.set_yticks(range(len(metodos)))
    ax.set_yticklabels([MET_EN[m] for m in metodos])
    ax.invert_yaxis()
    ax.set_title(titulo, loc="left")
    ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0 if col == "sens_ma" else 1))
    ax.grid(axis="y", visible=False)
axes[0].legend(title="band", loc="lower left", fontsize=6.5, title_fontsize=6.5)
fig.tight_layout()
salvar(fig, "fig_metodos")

sm = pd.read_csv(RESULTADOS / "06_sens_motivo.csv", index_col=0)
sm.index = sm.index.map(MOT_EN)
sm.columns = sm.columns.map(INT_EN)
fig, ax = plt.subplots(figsize=(3.6, 2.2))
heatmap(ax, sm)
ax.set_title("Sensitivity at registration · 15-min band", loc="left")
salvar(fig, "fig_sens_motivo")

curva = pd.read_csv(RESULTADOS / "06_curva_operacao.csv")
fig, ax = plt.subplots(figsize=(3.4, 2.4))
for i, nome in enumerate(METODOS):
    c_ = curva[curva["metodo"] == nome]
    ax.plot(1 - c_["especificidade"], c_["sensibilidade"], marker="o", ms=3.5, color=CORES[i], label=MET_EN[nome])
    if nome == PROPOSTO:
        for _, r_ in c_.iterrows():
            ax.annotate(f"target {r_['meta']:.0%}", (1 - r_["especificidade"], r_["sensibilidade"]), fontsize=6,
                        xytext=(3, -9), textcoords="offset points", color=TXT2)
ax.set_xlabel("controls flagged as Residual")
ax.set_ylabel("sensitivity (15 min)")
ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=1))
ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0))
ax.legend(loc="lower right", fontsize=6.3)
ax.set_title("Operating points", loc="left")
salvar(fig, "fig_curva_operacao")

sa_ma = pd.read_csv(RESULTADOS / "06_sens_atraso_media_alta.csv", index_col=0)
fig, ax = plt.subplots(figsize=(3.4, 2.4))
for j, L in enumerate(FAIXAS_L):
    ax.plot(sa_ma.index, sa_ma[str(L)], marker="o", ms=3.5, color=CORES[j], label=f"{L}-min band")
ax.set_xticks(ATRASOS)
ax.set_xlabel("delay between degradation onset and registration (min)")
ax.set_ylabel("sensitivity")
ax.set_ylim(0, 1)
ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0))
ax.legend(loc="lower right")
ax.set_title("Medium/high intensity · contextual profile", loc="left")
salvar(fig, "fig_sens_atraso")

conf = pd.read_csv(RESULTADOS / "06_confusao_indicador.csv", index_col=0)
conf.index = conf.index.map(MOT_EN)
conf.columns = conf.columns.map(IND_EN)
fig, ax = plt.subplots(figsize=(3.4, 2.2))
heatmap(ax, conf)
ax.set_xticklabels(conf.columns, rotation=15, ha="right")
ax.set_title("Injected cause × flagged indicator (15 min)", loc="left")
salvar(fig, "fig_confusao_indicador")

acerto_inicio = pd.read_csv(RESULTADOS / "06_inicio.csv", index_col=0)
fig, ax = plt.subplots(figsize=(3.3, 2.1))
ax.bar(range(len(ATRASOS)), acerto_inicio["mean"], color=AZUL[4], width=0.6)
for i, (m, n) in enumerate(acerto_inicio[["mean", "size"]].to_numpy()):
    lo, hi = wilson(int(round(m * n)), n)
    ax.errorbar(i, m, yerr=[[m - lo], [hi - m]], color=TXT3, capsize=2, lw=0.8)
    ax.text(i, hi + 0.03, f"{m:.0%}", ha="center", fontsize=6.8, color=TXT2)
ax.set_xticks(range(len(ATRASOS)))
ax.set_xticklabels([f"{a} min" for a in ATRASOS])
ax.set_xlabel("actual onset (before registration)")
ax.set_ylim(0, 1.1)
ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0))
ax.set_title("Actual onset within the estimated zone", loc="left")
ax.grid(axis="x", visible=False)
salvar(fig, "fig_inicio")

# expansão retroativa: mesmo cenário do notebook 06 (06_resumo.json), decidido com a calibração salva
with open(RESULTADOS / "04_calibracao.pkl", "rb") as f:
    calib = pickle.load(f)
cenarios = pd.read_csv(RESULTADOS / "05_cenarios.csv", parse_dates=["t_registro"]).set_index("cenario")
c_ex = json.loads((RESULTADOS / "06_resumo.json").read_text())["cenario_exemplo"]
P = pd.read_parquet(RESULTADOS / "06_periodos.parquet")
b_ex = P[(P["periodo"] == "banda") & (P["cenario"] == c_ex)].sort_values("id_periodo").copy()
b_ex["L"] = b_ex["hi"] - b_ex["lo"]
res_ex, vezes_ex = [], []
for _, linha in b_ex.iterrows():
    res, _, vz = decidir(linha.to_frame().T.infer_objects(), calib[(PROPOSTO, int(linha["L"]), cenarios.loc[c_ex, "mes"], HIST_PRINCIPAL)])
    res_ex.append(bool(res[0]))
    vezes_ex.append(float(vz.max(axis=1).iloc[0]))
fig, ax = plt.subplots(figsize=(7.0, 1.55))
nb = len(BANDAS)
atraso_ex = int(cenarios.loc[c_ex, "atraso"])
for k, ((lo, hi), res_b, v) in enumerate(zip(BANDAS, res_ex, vezes_ex)):
    x = nb - 1 - k  # mais antiga à esquerda, registro à direita
    ax.barh(0, 0.96, left=x + 0.02, height=0.6, color=CORES[7] if res_b else AZUL[1])
    ax.text(x + 0.5, 0, f"{'Residual' if res_b else 'Normal'}\n{v:.1f}× limit", ha="center", va="center", fontsize=6.5,
            color="white" if res_b else TXT1)
    if lo < atraso_ex <= hi:
        xr = x + 1 - (atraso_ex - lo) / (hi - lo)
        ax.plot([xr, xr], [-0.38, 0.38], color=TXT1, lw=1.2, ls="--")
        ax.text(xr, 0.42, "actual onset", fontsize=6.5, ha="center", va="bottom")
ax.set_xlim(0, nb)
ax.set_ylim(-0.4, 0.62)
ax.set_xticks([nb - 0.5 - k for k in range(nb)])
ax.set_xticklabels([f"{lo}–{hi}" for lo, hi in BANDAS])
ax.set_xlabel("band (minutes before incident registration)")
ax.set_yticks([])
ax.grid(False)
ax.spines["left"].set_visible(False)
ax.set_title(f"Backward expansion · widespread 5xx (medium intensity) starting {atraso_ex} min before · resource "
             f"{rot(cenarios.loc[c_ex, 'recurso'])}", loc="left")
salvar(fig, "fig_expansao_exemplo")

fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.3))
for ax, (tipo, titulo) in zip(axes, [("incidente", "Sensitivity (15 min)"), ("controle", "Specificity (15 min)")]):
    for j, h in enumerate(HISTORICOS):
        t_ = T_all[(PROPOSTO, 15, h)]
        for i, mes in enumerate(MESES_TESTE):
            g = t_[(t_["mes"] == mes) & (t_["tipo"] == tipo)]
            k, n = int(g["acerto_estado"].sum()), len(g)
            p_ = k / n
            lo, hi = wilson(k, n)
            x = i + (j - 0.5) * 0.36
            ax.bar(x, p_, width=0.34, color=[AZUL[4], CORES[1]][j], label=("3 months" if h == "3m" else "1 month") if i == 0 else None)
            ax.errorbar(x, p_, yerr=[[p_ - lo], [hi - p_]], color=TXT3, capsize=2, lw=0.8)
            ax.text(x, hi + (0.01 if tipo == "incidente" else 0.002), f"{p_:.1%}", ha="center", fontsize=6.3, color=TXT2)
    ax.set_xticks(range(len(MESES_TESTE)))
    ax.set_xticklabels(["August (7 resources)", "September (12 resources)"])
    ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0))
    ax.set_title(titulo, loc="left")
    ax.grid(axis="x", visible=False)
    ax.set_ylim((0.9, 1.0) if tipo == "controle" else (0, 0.65))
axes[0].legend(title="history", loc="upper right", fontsize=6.5, title_fontsize=6.5)
fig.tight_layout()
salvar(fig, "fig_historico")

print("ok:", sorted(p.name for p in FIG_EN.glob("*.pdf")))
