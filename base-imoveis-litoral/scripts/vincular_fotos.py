"""Vincula as fotos de fachada da pasta fotos/ às vendas da planilha.

Uso:
    python scripts/vincular_fotos.py [planilha.xlsx]

Convenção de nomes: fotos/<ID>.jpg, e para mais de uma foto fotos/<ID>_2.jpg,
fotos/<ID>_3.jpg ... (jpg, jpeg ou png). O <ID> é o da coluna ID da aba Vendas.

O script:
  * coloca na coluna "Foto da fachada" um link para a primeira foto;
  * preenche "Data da foto" e "Coordenadas" a partir do EXIF da foto, somente
    se essas células estiverem vazias e o EXIF existir (nada é estimado);
  * recria a aba Galeria com as miniaturas;
  * avisa sobre fotos sem venda correspondente e vendas com foto sem origem.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openpyxl import load_workbook  # noqa: E402
from PIL import Image  # noqa: E402

from esquema import (EXT_FOTO, FMT_DATA, PASTA_FOTOS, PRIMEIRA_LINHA, fonte_link, fotos_do_id,  # noqa: E402
                     idx, salvar)

PLANILHA_PADRAO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "base_imoveis_vendidos.xlsx")


def ler_exif(caminho: str):
    """Retorna (data, 'lat,long') do EXIF, ou None para o que não existir."""
    try:
        with Image.open(caminho) as im:
            exif = im.getexif()
            data = None
            bruto = exif.get_ifd(0x8769).get(0x9003) or exif.get(0x0132)  # DateTimeOriginal / DateTime
            if bruto:
                try:
                    data = datetime.strptime(str(bruto).strip(), "%Y:%m:%d %H:%M:%S").date()
                except ValueError:
                    data = None
            gps = exif.get_ifd(0x8825)
            coord = None
            if gps and 2 in gps and 4 in gps:
                def graus(v):
                    d, m, s = (float(x) for x in v)
                    return d + m / 60 + s / 3600
                lat, lon = graus(gps[2]), graus(gps[4])
                if gps.get(1) == "S":
                    lat = -lat
                if gps.get(3) == "W":
                    lon = -lon
                coord = f"{lat:.6f},{lon:.6f}"
            return data, coord
    except Exception:
        return None, None


def main():
    planilha = sys.argv[1] if len(sys.argv) > 1 else PLANILHA_PADRAO
    base = os.path.dirname(os.path.abspath(planilha))
    wb = load_workbook(planilha)
    ws = wb["Vendas"]

    ids_base, vinculadas, sem_origem = set(), 0, []
    for r in range(PRIMEIRA_LINHA, ws.max_row + 1):
        id_ = ws.cell(row=r, column=idx("id")).value
        if not id_:
            continue
        ids_base.add(str(id_))
        fotos = fotos_do_id(base, str(id_))
        cel = ws.cell(row=r, column=idx("foto"))
        if not fotos:
            if cel.hyperlink and str(cel.hyperlink.target or "").startswith(PASTA_FOTOS):
                cel.value, cel.hyperlink = None, None  # foto removida da pasta
            continue
        rotulo = "Ver foto" if len(fotos) == 1 else f"Ver foto (1 de {len(fotos)})"
        cel.value = rotulo
        cel.hyperlink = fotos[0].replace(os.sep, "/")
        cel.font = fonte_link
        vinculadas += 1

        data, coord = ler_exif(os.path.join(base, fotos[0]))
        c_data = ws.cell(row=r, column=idx("data_foto"))
        if c_data.value in (None, "") and data:
            c_data.value = data
            c_data.number_format = FMT_DATA
        c_coord = ws.cell(row=r, column=idx("coordenadas"))
        if c_coord.value in (None, "") and coord:
            c_coord.value = coord
        origem = ws.cell(row=r, column=idx("origem_foto")).value
        if origem in (None, "", "Sem foto"):
            sem_origem.append(str(id_))

    orfas = []
    pasta = os.path.join(base, PASTA_FOTOS)
    if os.path.isdir(pasta):
        for nome in sorted(os.listdir(pasta)):
            raiz, ext = os.path.splitext(nome)
            if ext.lower() in EXT_FOTO and raiz not in ids_base and raiz.rsplit("_", 1)[0] not in ids_base:
                orfas.append(nome)

    salvar(wb, planilha)
    print(f"Vendas com foto vinculada: {vinculadas}")
    if sem_origem:
        print("Preencha 'Origem da foto' nestas vendas:", ", ".join(sem_origem))
    if orfas:
        print("Fotos sem ID correspondente na base (verifique o nome do arquivo):", ", ".join(orfas))


if __name__ == "__main__":
    main()
