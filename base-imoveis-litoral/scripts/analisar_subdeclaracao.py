"""Gera o relatório de mercado sobre subdeclaração do valor de venda no ITBI.

Uso:
    python scripts/analisar_subdeclaracao.py [planilha.xlsx] [--amostra-min N]

Lê só as vendas com Status = Validado e calcula os mesmos indicadores da aba
"Análise ITBI" direto dos valores lançados (não depende de recálculo do Excel).
Saída: relatorio_subdeclaracao.md, ao lado da planilha.

Nenhum número é estimado: recortes com menos vendas que a amostra mínima
aparecem como "amostra insuficiente".
"""
from __future__ import annotations

import os
import statistics as st
import sys
from collections import defaultdict
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openpyxl import load_workbook  # noqa: E402

from esquema import AMOSTRA_MIN_PADRAO, CIDADES, PRIMEIRA_LINHA, idx  # noqa: E402

PLANILHA_PADRAO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "base_imoveis_vendidos.xlsx")


def num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def razao(a, b):
    return a / b if a is not None and b else None


def ler_vendas(caminho):
    ws = load_workbook(caminho)["Vendas"]
    vendas = []
    for r in range(PRIMEIRA_LINHA, ws.max_row + 1):
        g = lambda k: ws.cell(row=r, column=idx(k)).value
        if not g("id") or g("status") != "Validado" or g("natureza") != "Compra e venda":
            continue
        valor = num(g("valor_venda"))
        if not valor:
            continue
        area = num(g("area_terreno")) if g("tipo") == "Terreno" else num(g("area_construida"))
        d = g("data_escritura")
        vendas.append({
            "cidade": g("cidade"), "bairro": g("bairro"), "padrao": g("padrao") or "Não informado",
            "forma": g("forma_pagamento") or "Não informado",
            "ano": d.year if isinstance(d, (date, datetime)) else None,
            "valor": valor, "m2": razao(valor, area) if area and area > 0 else None,
            "r_base": razao(valor, num(g("base_itbi"))), "r_venal": razao(valor, num(g("venal_iptu"))),
            "r_leilao": razao(valor, num(g("valor_leilao"))),
            "r_fin": razao(num(g("valor_financiado")), valor),
        })
    return vendas


def indicadores(vs, minimo):
    def med(xs):
        return st.median(xs) if len(xs) >= minimo else None

    def frac(xs, cond):
        return sum(1 for x in xs if cond(x)) / len(xs) if xs else None

    rb = [v["r_base"] for v in vs if v["r_base"] is not None]
    rv = [v["r_venal"] for v in vs if v["r_venal"] is not None]
    rl = [v["r_leilao"] for v in vs if v["r_leilao"] is not None]
    rf = [v["r_fin"] for v in vs if v["r_fin"] is not None]
    mf = [v["m2"] for v in vs if v["forma"] == "Financiado" and v["m2"]]
    mv = [v["m2"] for v in vs if v["forma"] == "À vista" and v["m2"]]
    mrb = med(rb)
    return {
        "n": len(vs), "n_base": len(rb), "med_base": mrb, "pct_base_maior": frac(rb, lambda x: x < 1),
        "cod_base": (100 * st.mean(abs(x - mrb) for x in rb) / mrb) if mrb else None,
        "n_venal": len(rv), "med_venal": med(rv), "pct_abaixo_venal": frac(rv, lambda x: x <= 1),
        "n_fin": len(mf), "n_vista": len(mv), "m2_fin": med(mf), "m2_vista": med(mv),
        "dif_vista": (med(mv) / med(mf) - 1) if med(mf) and med(mv) else None,
        "n_leilao": len(rl), "med_leilao": med(rl), "pct_abaixo_leilao": frac(rl, lambda x: x < 1),
        "n_financ": len(rf), "pct_fin_maior": frac(rf, lambda x: x >= 1),
    }


def f_pct(x):
    return "amostra insuficiente" if x is None else f"{x * 100:.1f}%".replace(".", ",")


def f_raz(x):
    return "amostra insuficiente" if x is None else f"{x:.3f}".replace(".", ",")


def f_rs(x):
    if x is None:
        return "amostra insuficiente"
    return "R$ " + f"{x:,.0f}".replace(",", ".")


def f_cod(x):
    return "amostra insuficiente" if x is None else f"{x:.1f}".replace(".", ",")


def tabela(titulo, grupos, minimo):
    linhas = [f"### {titulo}", "",
              "| Recorte | n | Decl.÷Base ITBI (mediana) | % base > declarado | COD | Decl.÷Venal (mediana) "
              "| % ≤ venal | R$/m² financ. | R$/m² à vista | Dif. à vista | Decl.÷Leilão | % financ. ≥ decl. |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for nome, vs in grupos:
        i = indicadores(vs, minimo)
        linhas.append(
            f"| {nome} | {i['n']} | {f_raz(i['med_base'])} (n={i['n_base']}) | {f_pct(i['pct_base_maior'])} "
            f"| {f_cod(i['cod_base'])} "
            f"| {f_raz(i['med_venal'])} (n={i['n_venal']}) | {f_pct(i['pct_abaixo_venal'])} "
            f"| {f_rs(i['m2_fin'])} (n={i['n_fin']}) | {f_rs(i['m2_vista'])} (n={i['n_vista']}) "
            f"| {f_pct(i['dif_vista'])} | {f_raz(i['med_leilao'])} (n={i['n_leilao']}) "
            f"| {f_pct(i['pct_fin_maior'])} (n={i['n_financ']}) |")
    return "\n".join(linhas) + "\n"


def leitura(cidade, i):
    """Frases objetivas, só a partir dos números calculados."""
    out = []
    if i["med_base"] is not None:
        out.append(f"- Em {i['n_base']} vendas com base de cálculo informada, a prefeitura adotou base maior que o "
                   f"valor declarado em {f_pct(i['pct_base_maior'])} dos casos; a mediana Declarado ÷ Base é "
                   f"{f_raz(i['med_base'])}.")
    if i["med_venal"] is not None:
        out.append(f"- O preço declarado ficou igual ou abaixo do valor venal do IPTU em "
                   f"{f_pct(i['pct_abaixo_venal'])} das {i['n_venal']} vendas com venal informado.")
    if i["dif_vista"] is not None:
        sinal = "abaixo" if i["dif_vista"] < 0 else "acima"
        out.append(f"- O R$/m² mediano declarado nas vendas à vista ficou {f_pct(abs(i['dif_vista']))} {sinal} do "
                   f"das vendas financiadas ({i['n_vista']} à vista × {i['n_fin']} financiadas). Diferenças de "
                   "imóvel e de perfil de comprador também compõem esse número; compare nos recortes por bairro e "
                   "padrão.")
    if i["med_leilao"] is not None:
        out.append(f"- Nas {i['n_leilao']} vendas com alienação fiduciária, o preço declarado ficou abaixo do valor "
                   f"do imóvel fixado no contrato em {f_pct(i['pct_abaixo_leilao'])} dos casos (mediana "
                   f"Declarado ÷ Leilão = {f_raz(i['med_leilao'])}).")
    if not out:
        out.append("- Ainda não há vendas validadas suficientes para nenhum indicador.")
    return f"**{cidade}**\n\n" + "\n".join(out) + "\n"


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("planilha", nargs="?", default=PLANILHA_PADRAO)
    ap.add_argument("--amostra-min", type=int, default=AMOSTRA_MIN_PADRAO)
    a = ap.parse_args()
    planilha, minimo = a.planilha, a.amostra_min

    vendas = ler_vendas(planilha)
    hoje = datetime.now().strftime("%d/%m/%Y")
    md = ["# Subdeclaração do valor de venda no ITBI: São Sebastião e Bertioga", "",
          f"Gerado em {hoje} a partir de `{os.path.basename(planilha)}`. Vendas validadas: **{len(vendas)}**. "
          f"Amostra mínima por indicador: **{minimo}**.", "",
          "Método, definições e contexto: `docs/analise_subdeclaracao_ITBI.md`. Todos os números abaixo saem "
          "das vendas documentadas na base; nada é estimado fora delas.", "", "## Leitura por cidade", ""]
    for cidade in CIDADES:
        md.append(leitura(cidade, indicadores([v for v in vendas if v["cidade"] == cidade], minimo)))
    md += ["## Tabelas", ""]
    md.append(tabela("Por cidade", [(c, [v for v in vendas if v["cidade"] == c]) for c in CIDADES], minimo))
    for chave, titulo in (("ano", "Por cidade e ano"), ("padrao", "Por cidade e padrão"),
                          ("bairro", "Por cidade e bairro")):
        grupos = defaultdict(list)
        for v in vendas:
            grupos[(v["cidade"], v[chave])].append(v)
        itens = sorted(((f"{c} — {k if k is not None else 'sem data'}", vs) for (c, k), vs in grupos.items()),
                       key=lambda x: x[0])
        if itens:
            md.append(tabela(titulo, itens, minimo))
    destino = os.path.join(os.path.dirname(os.path.abspath(planilha)), "relatorio_subdeclaracao.md")
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Vendas validadas: {len(vendas)} | relatório: {destino}")


if __name__ == "__main__":
    main()
