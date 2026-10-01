"""Gera a planilha vazia base_imoveis_vendidos.xlsx com toda a estrutura.

Uso:
    python scripts/gerar_planilha.py [caminho_saida.xlsx]

Não sobrescreve um arquivo existente (para não apagar dados já lançados);
use --forcar para isso.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from esquema import criar_planilha, salvar  # noqa: E402

PADRAO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "base_imoveis_vendidos.xlsx")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    destino = args[0] if args else PADRAO
    if os.path.exists(destino) and "--forcar" not in sys.argv:
        sys.exit(f"{destino} já existe. Use --forcar para sobrescrever (os dados lançados serão perdidos).")
    salvar(criar_planilha(), destino)
    print(f"Planilha criada: {destino}")


if __name__ == "__main__":
    main()
