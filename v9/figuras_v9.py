"""Gera, a partir dos resultados salvos da v9, as figuras do artigo v9 (versão final: perfil tipo de dia × hora, percentil 97).
Não reexecuta o pipeline: lê só os CSV/parquet de v9/resultados e grava em v9/artigo/figuras."""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from statsmodels.stats.proportion import proportion_confint

RAIZ = Path("/home/wsl/gh/mestrado/claude9")
RES = RAIZ / "v9/resultados"
FIG = RAIZ / "v9/artigo/figuras"

# Estilo idêntico ao de v3/notebooks/00_funcoes.ipynb
CORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
TXT1, TXT2, TXT3, GRADE, CINZA = "#0b0b0b", "#52514e", "#8a8983", "#e4e3df", "#b8b7b1"
CMAP_SEQ = LinearSegmentedColormap.from_list("azul", ["#f7f9fc"] + AZUL)
mpl.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 8.5, "axes.titleweight": "bold",
    "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.edgecolor": CINZA, "axes.labelcolor": TXT2, "xtick.color": TXT2, "ytick.color": TXT2,
    "text.color": TXT1, "axes.titlecolor": TXT1, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "lines.linewidth": 1.5, "figure.dpi": 110, "savefig.bbox": "tight", "savefig.dpi": 220,
    "pdf.fonttype": 42, "legend.frameon": False, "figure.facecolor": "white", "axes.facecolor": "white",
})
METODOS = ["Perfil contextual (proposto)", "z-score global", "Semana anterior"]
MOTIVOS = ["4xx generalizado", "4xx de 1 consumidor", "5xx generalizado", "5xx de 1 consumidor", "latência"]


def salvar(fig, nome):
    fig.savefig(FIG / f"{nome}.pdf")
    fig.savefig(FIG / f"{nome}.png")
    plt.close(fig)


def wilson(k, n):
    return proportion_confint(k, n, alpha=0.05, method="wilson")


def heatmap(ax, v, fmt="{:.0%}", vmax=1, limiar_branco=0.6):
    ax.imshow(v.to_numpy(dtype=float), cmap=CMAP_SEQ, vmin=0, vmax=vmax, aspect="auto")
    for i in range(v.shape[0]):
        for j in range(v.shape[1]):
            x = v.iat[i, j]
            if pd.notna(x):
                ax.text(j, i, fmt.format(x), ha="center", va="center", fontsize=6.8,
                        color="white" if x / vmax > limiar_branco else TXT1)
    ax.set_xticks(range(v.shape[1]))
    ax.set_xticklabels(v.columns)
    ax.set_yticks(range(v.shape[0]))
    ax.set_yticklabels(v.index)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)


dec = pd.read_parquet(RES / "06_decisoes.parquet")


def decisoes(metodo, hist="3m"):
    return dec.loc[f"{metodo} | 60 | {hist}"]


# 1. Métodos: sensibilidade (média/alta) e especificidade, um ponto por método
fig, axes = plt.subplots(1, 2, figsize=(7.0, 1.7), sharey=True)
for ax, (col, titulo) in zip(axes, [("sens_ma", "Sensibilidade (intensidade média/alta)"), ("espec", "Especificidade (controles)")]):
    for i, n in enumerate(METODOS):
        t = decisoes(n)
        if col == "sens_ma":
            base = t[(t["tipo"] == "incidente") & t["intensidade"].isin(["media", "alta"])]
            k = int(base["residual"].sum())
        else:
            base = t[t["tipo"] == "controle"]
            k = int((~base["residual"].astype(bool)).sum())
        p = k / len(base)
        lo, hi = wilson(k, len(base))
        ax.errorbar(p, i, xerr=[[p - lo], [hi - p]], fmt="o", ms=4.5, color=CORES[0], ecolor=CORES[0], lw=1, capsize=2)
        ax.annotate(f"{p:.1%}", (p, i), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=6.5, color=TXT2)
    ax.set_yticks(range(len(METODOS)))
    ax.set_yticklabels(METODOS)
    ax.set_ylim(len(METODOS) - 0.5, -0.7)
    ax.set_title(titulo, loc="left")
    ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0 if col == "sens_ma" else 1))
    ax.grid(axis="y", visible=False)
fig.tight_layout()
salvar(fig, "fig_metodos")

# 2. Sensibilidade por motivo e intensidade
sm = pd.read_csv(RES / "06_sens_motivo.csv", index_col=0).loc[MOTIVOS]
fig, ax = plt.subplots(figsize=(3.6, 2.2))
heatmap(ax, sm)
ax.set_title("Sensibilidade no registro por motivo e intensidade", loc="left")
salvar(fig, "fig_sens_motivo")

# 3. Pontos de operação
curva = pd.read_csv(RES / "06_curva_operacao.csv")
fig, ax = plt.subplots(figsize=(3.4, 2.4))
for i, nome in enumerate(METODOS):
    c_ = curva[curva["metodo"] == nome]
    ax.plot(1 - c_["especificidade"], c_["sensibilidade"], marker="o", ms=3.5, color=CORES[i], label=nome)
    if i == 0:
        for _, r_ in c_.iterrows():
            ax.annotate(f"meta {r_['meta']:.0%}", (1 - r_["especificidade"], r_["sensibilidade"]), fontsize=6,
                        xytext=(3, -9), textcoords="offset points", color=TXT2)
ax.set_xlabel("controles marcados como Residual")
ax.set_ylabel("sensibilidade")
ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=1))
ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0))
ax.legend(loc="lower right", fontsize=6.3)
ax.set_title("Pontos de operação", loc="left")
salvar(fig, "fig_curva_operacao")

# 4. Motivo injetado x indicador apontado
conf = pd.read_csv(RES / "06_confusao_indicador.csv", index_col=0).loc[MOTIVOS]
fig, ax = plt.subplots(figsize=(3.4, 2.2))
heatmap(ax, conf)
ax.set_xticklabels(conf.columns, rotation=15, ha="right")
ax.set_title("Motivo injetado × indicador apontado", loc="left")
salvar(fig, "fig_confusao_indicador")

# 5. Histórico de 3 meses x 1 mês, por mês de teste
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.3))
for ax, (tipo, titulo) in zip(axes, [("incidente", "Sensibilidade"), ("controle", "Especificidade")]):
    for j, h in enumerate(["3m", "1m"]):
        t_ = decisoes(METODOS[0], h)
        for i, mes in enumerate(["ago", "set"]):
            g = t_[(t_["mes"] == mes) & (t_["tipo"] == tipo)]
            k, n = int(g["acerto_estado"].sum()), len(g)
            p_ = k / n
            lo, hi = wilson(k, n)
            x = i + (j - 0.5) * 0.36
            ax.bar(x, p_, width=0.34, color=[AZUL[4], CORES[1]][j], label=("3 meses" if h == "3m" else "1 mês") if i == 0 else None)
            ax.errorbar(x, p_, yerr=[[p_ - lo], [hi - p_]], color=TXT3, capsize=2, lw=0.8)
            ax.text(x, hi + (0.01 if tipo == "incidente" else 0.002), f"{p_:.1%}", ha="center", fontsize=6.3, color=TXT2)
    ax.set_xticks(range(2))
    ax.set_xticklabels(["agosto (7 recursos)", "setembro (12 recursos)"])
    ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(1, decimals=0))
    ax.set_title(titulo, loc="left")
    ax.grid(axis="x", visible=False)
    ax.set_ylim((0.85, 1.0) if tipo == "controle" else (0, 0.75))
axes[0].legend(title="histórico", loc="upper right", fontsize=6.5, title_fontsize=6.5)
fig.tight_layout()
salvar(fig, "fig_historico")

# 6. Limites por indicador, janelas de 1 h (perfil horário)
lim = pd.read_csv(RES / "04_limites.csv", header=[0, 1], index_col=0)["60"]
fig, ax = plt.subplots(figsize=(3.4, 3.1))
ax.imshow(np.log10(lim.to_numpy()), cmap=CMAP_SEQ, vmin=np.log10(3), vmax=2, aspect="auto")
for i in range(lim.shape[0]):
    for j in range(lim.shape[1]):
        ax.text(j, i, f"{lim.iat[i, j]:.0f}", ha="center", va="center", fontsize=6.3,
                color="white" if np.log10(lim.iat[i, j]) > 1.45 else TXT1)
ax.set_xticks(range(lim.shape[1]))
ax.set_xticklabels(lim.columns, rotation=20, ha="right")
ax.set_yticks(range(lim.shape[0]))
ax.set_yticklabels(lim.index)
ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title("Limite por indicador e recurso (z)", loc="left")
salvar(fig, "fig_limites")

print("ok:", sorted(p.name for p in FIG.glob("*.pdf")))
