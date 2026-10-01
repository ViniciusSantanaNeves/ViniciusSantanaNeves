"""Importa para a aba Vendas o arquivo de ITBI enviado pela prefeitura (resposta LAI).

Uso:
    python scripts/importar_lai.py <arquivo.csv|xlsx> <mapa_colunas.json> [planilha.xlsx] [--simular]

O mapa de colunas (veja mapa_colunas_exemplo.json) diz qual coluna do arquivo
da prefeitura corresponde a cada campo da base. Nada é inferido: linhas que não
passam nas regras vão para o relatório de rejeitadas, com o motivo.

--simular  só gera o relatório, sem gravar na planilha.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openpyxl import load_workbook  # noqa: E402

from esquema import (BAIRROS, CIDADES, FMT_DATA, FMT_M2, FMT_REAIS, FORMAS_PAGAMENTO, PADROES,  # noqa: E402
                     PRIMEIRA_LINHA, TIPOS, ULTIMA_LINHA, escrever_formulas_linha, idx, normalizar, salvar)

PLANILHA_PADRAO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "base_imoveis_vendidos.xlsx")
SIGLA = {"São Sebastião": "SS", "Bertioga": "BE"}
CAMPOS_NUMERICOS = ("valor_venda", "base_itbi", "venal_iptu", "valor_financiado", "valor_leilao",
                    "area_construida", "area_terreno")
CAMPOS_DATA = ("data_escritura", "data_registro")


# ---------------------------------------------------------------------------
# Leitura do arquivo da prefeitura
# ---------------------------------------------------------------------------
def ler_arquivo(caminho: str, cfg: dict) -> list[dict]:
    ext = os.path.splitext(caminho)[1].lower()
    linha_cab = int(cfg.get("linha_cabecalho", 1))
    if ext in (".xlsx", ".xlsm"):
        wb = load_workbook(caminho, read_only=True, data_only=True)
        ws = wb[cfg["aba"]] if cfg.get("aba") else wb.worksheets[0]
        linhas = list(ws.iter_rows(values_only=True))
        cab = [str(c).strip() if c is not None else "" for c in linhas[linha_cab - 1]]
        dados = linhas[linha_cab:]
        inicio = linha_cab + 1
    elif ext in (".csv", ".txt"):
        with open(caminho, encoding=cfg.get("csv_encoding", "utf-8-sig"), newline="") as f:
            linhas = list(csv.reader(f, delimiter=cfg.get("csv_separador", ";")))
        cab = [c.strip() for c in linhas[linha_cab - 1]]
        dados = linhas[linha_cab:]
        inicio = linha_cab + 1
    else:
        sys.exit(f"Formato não suportado: {ext}. Converta para .csv ou .xlsx.")
    registros = []
    for n, valores in enumerate(dados, start=inicio):
        if not any(v not in (None, "") for v in valores):
            continue
        reg = {cab[i]: valores[i] for i in range(min(len(cab), len(valores)))}
        reg["__linha__"] = n
        registros.append(reg)
    return registros, cab


# ---------------------------------------------------------------------------
# Conversões (sem inferência: o que não converte fica vazio e é reportado)
# ---------------------------------------------------------------------------
def para_numero(v, decimal: str):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d,.\-]", "", str(v))
    if not s:
        return None
    if decimal == ",":
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def para_data(v, formatos: list[str]):
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    for fmt in formatos:
        try:
            return datetime.strptime(str(v).strip(), fmt).date()
        except ValueError:
            continue
    return None


def mapear(valor, mapa: dict, permitidos: list[str]):
    """Mapeia texto literal → valor da lista, só por correspondência explícita."""
    if valor is None or str(valor).strip() == "":
        return None
    n = normalizar(valor)
    for chave, destino in mapa.items():
        if normalizar(chave) == n and destino in permitidos:
            return destino
    for p in permitidos:
        if normalizar(p) == n:
            return p
    return None


def mapear_bairro(valor, cidade, apelidos: dict):
    if valor is None or str(valor).strip() == "":
        return None
    n = normalizar(valor)
    oficiais = {normalizar(b[0]): b[0] for b in BAIRROS[cidade]}
    if n in oficiais:
        return oficiais[n]
    for apelido, oficial in apelidos.items():
        if normalizar(apelido) == n and normalizar(oficial) in oficiais:
            return oficiais[normalizar(oficial)]
    return None


def chave_dup(cidade, matricula, inscricao, data_):
    ident = normalizar(matricula) or normalizar(inscricao)
    if not ident or not data_:
        return None
    return (cidade, re.sub(r"\D", "", ident) or ident, data_.isoformat() if hasattr(data_, "isoformat") else str(data_))


# ---------------------------------------------------------------------------
def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    simular = "--simular" in sys.argv
    if len(args) < 2:
        sys.exit(__doc__)
    arquivo, mapa_path = args[0], args[1]
    planilha = args[2] if len(args) > 2 else PLANILHA_PADRAO

    with open(mapa_path, encoding="utf-8") as f:
        cfg = json.load(f)
    cidade = cfg["cidade"]
    if cidade not in CIDADES:
        sys.exit(f"Cidade '{cidade}' inválida. Use: {CIDADES}")
    protocolo = cfg["protocolo"].strip()
    if not protocolo:
        sys.exit("Informe o nº do protocolo LAI em 'protocolo' no mapa de colunas.")
    colunas = cfg["colunas"]
    decimal = cfg.get("separador_decimal", ",")
    formatos_data = cfg.get("formatos_data", ["%d/%m/%Y", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S"])
    naturezas_ok = {normalizar(x) for x in cfg["naturezas_aceitas"]}
    status_inicial = cfg.get("status_inicial", "Validado")

    registros, cabecalho = ler_arquivo(arquivo, cfg)
    faltando = [c for c in colunas.values() if c and c not in cabecalho]
    if faltando:
        sys.exit(f"Colunas do mapa não encontradas no arquivo: {faltando}\nCabeçalho do arquivo: {cabecalho}")

    wb = load_workbook(planilha)
    ws = wb["Vendas"]

    # Estado atual da planilha: duplicidades, IDs e primeira linha livre
    existentes, prox_linha, maior_id = set(), PRIMEIRA_LINHA, 0
    prefixo = f"LAI-{SIGLA[cidade]}-"
    for r in range(PRIMEIRA_LINHA, ws.max_row + 1):
        id_ = ws.cell(row=r, column=idx("id")).value
        if not id_:
            continue
        prox_linha = r + 1
        if str(id_).startswith(prefixo) and str(id_)[len(prefixo):].isdigit():
            maior_id = max(maior_id, int(str(id_)[len(prefixo):]))
        doc = str(ws.cell(row=r, column=idx("documento")).value or "")
        m = re.search(r"[Mm]atr[ií]cula\s*(?:n[ºo°.]*\s*)?([\d.]+)", doc)
        k = chave_dup(ws.cell(row=r, column=idx("cidade")).value,
                      m.group(1) if m else None,
                      ws.cell(row=r, column=idx("inscricao")).value,
                      para_data(ws.cell(row=r, column=idx("data_escritura")).value, formatos_data))
        if k:
            existentes.add(k)

    relatorio, importadas = [], []
    for reg in registros:
        g = lambda campo: reg.get(colunas.get(campo)) if colunas.get(campo) else None
        n = reg["__linha__"]
        motivos = []

        nat = g("natureza")
        if normalizar(nat) not in naturezas_ok:
            relatorio.append((n, "rejeitada", f"natureza fora de compra e venda: {nat!r}"))
            continue
        valor = para_numero(g("valor_venda"), decimal)
        if not valor or valor <= 0:
            relatorio.append((n, "rejeitada", f"valor de venda ausente ou inválido: {g('valor_venda')!r}"))
            continue
        bairro = mapear_bairro(g("bairro"), cidade, cfg.get("apelidos_bairro", {}))
        if not bairro:
            relatorio.append((n, "rejeitada", f"bairro fora da lista oficial: {g('bairro')!r} "
                                               "(se for nome popular, inclua em apelidos_bairro)"))
            continue

        dados = {k: para_numero(g(k), decimal) for k in CAMPOS_NUMERICOS}
        for k in CAMPOS_NUMERICOS:
            if g(k) not in (None, "") and dados[k] is None:
                motivos.append(f"{k} ilegível ({g(k)!r}), deixado vazio")
            if dados[k] is not None and dados[k] <= 0:
                motivos.append(f"{k} ≤ 0 ({g(k)!r}), deixado vazio")
                dados[k] = None
        for k in CAMPOS_DATA:
            dados[k] = para_data(g(k), formatos_data)
            if g(k) not in (None, "") and dados[k] is None:
                motivos.append(f"{k} ilegível ({g(k)!r}), deixado vazio")

        matricula, inscricao = g("matricula"), g("inscricao")
        k = chave_dup(cidade, matricula, inscricao, dados["data_escritura"])
        if k and k in existentes:
            relatorio.append((n, "duplicada", f"mesma matrícula/inscrição e data já na base: {k}"))
            continue
        if not k:
            motivos.append("sem matrícula/inscrição ou data: não foi possível checar duplicidade")

        tipo_raw = g("tipo")
        tipo = mapear(tipo_raw, cfg.get("mapa_tipo", {}), TIPOS)
        if tipo_raw not in (None, "") and not tipo:
            motivos.append(f"tipo sem correspondência no mapa_tipo: {tipo_raw!r}")
        fp_raw = g("forma_pagamento")
        forma = mapear(fp_raw, cfg.get("mapa_forma_pagamento", {}), FORMAS_PAGAMENTO[:-1])
        if fp_raw not in (None, "") and not forma:
            motivos.append(f"forma de pagamento sem correspondência no mapa_forma_pagamento: {fp_raw!r}")
        if not forma and dados["valor_financiado"]:
            forma = "Financiado"  # valor financiado > 0 informado pela prefeitura
        pad_raw = g("padrao_original")
        padrao = mapear(pad_raw, cfg.get("mapa_padrao", {}), PADROES[:-1])

        endereco = " ".join(str(x).strip() for x in (g("endereco"), g("numero")) if x not in (None, ""))
        documento = f"{protocolo} — linha {n}"
        if matricula not in (None, ""):
            documento += f" — Matrícula {matricula}"
        if g("cartorio") not in (None, ""):
            documento += f" ({g('cartorio')})"

        maior_id += 1
        linha = {
            "id": f"{prefixo}{maior_id:06d}", "cidade": cidade, "bairro": bairro,
            "endereco": endereco or None, "complemento": g("complemento"), "inscricao": inscricao,
            "tipo": tipo, "area_construida": dados["area_construida"], "area_terreno": dados["area_terreno"],
            "padrao": padrao or "Não informado",
            "origem_padrao": "Cadastro municipal (ITBI/IPTU)" if padrao else "Não informado",
            "padrao_original": pad_raw, "valor_venda": valor, "base_itbi": dados["base_itbi"],
            "venal_iptu": dados["venal_iptu"], "forma_pagamento": forma or "Não informado",
            "valor_financiado": dados["valor_financiado"], "valor_leilao": dados["valor_leilao"],
            "data_escritura": dados["data_escritura"],
            "data_registro": dados["data_registro"], "natureza": "Compra e venda",
            "fonte": "LAI – ITBI Prefeitura", "documento": documento, "orgao": cfg.get("orgao"),
            "origem_foto": "Sem foto", "status": status_inicial,
            "observacoes": "; ".join(motivos) or None,
        }
        if k:
            existentes.add(k)
        importadas.append(linha)
        relatorio.append((n, "importada", "; ".join(motivos) or "ok"))

    if not simular:
        for linha in importadas:
            r = prox_linha
            for chave, v in linha.items():
                c = ws.cell(row=r, column=idx(chave), value=v)
                if chave in ("valor_venda", "base_itbi", "venal_iptu", "valor_financiado", "valor_leilao"):
                    c.number_format = FMT_REAIS
                elif chave in ("area_construida", "area_terreno"):
                    c.number_format = FMT_M2
                elif chave in CAMPOS_DATA:
                    c.number_format = FMT_DATA
            if r > ULTIMA_LINHA:
                escrever_formulas_linha(ws, r)
            prox_linha += 1
        if prox_linha - 1 > ULTIMA_LINHA:
            print(f"ATENÇÃO: a base passou de {ULTIMA_LINHA} linhas; o Resumo só lê até a linha {ULTIMA_LINHA}. "
                  "Aumente LINHAS_DADOS em esquema.py e gere uma nova planilha.")
        salvar(wb, planilha)

    rel_path = os.path.splitext(arquivo)[0] + "_relatorio_importacao.csv"
    with open(rel_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["linha_arquivo", "resultado", "motivo"])
        w.writerows(relatorio)

    cont = {s: sum(1 for x in relatorio if x[1] == s) for s in ("importada", "rejeitada", "duplicada")}
    print(f"{'SIMULAÇÃO — ' if simular else ''}Linhas lidas: {len(registros)} | importadas: {cont['importada']} | "
          f"rejeitadas: {cont['rejeitada']} | duplicadas: {cont['duplicada']}")
    print(f"Relatório: {rel_path}")


if __name__ == "__main__":
    main()
