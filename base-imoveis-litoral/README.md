# Base de imóveis vendidos: São Sebastião e Bertioga

Planilha Excel com vendas **efetivas** de imóveis em São Sebastião e Bertioga, sempre com o **valor real de venda** e nunca com o valor anunciado. Os dados ficam separados por cidade, bairro, valor, padrão e metragem, e cada venda pode ter foto da fachada.

## Por que a planilha começa vazia

São Sebastião e Bertioga não publicam dados de vendas de imóveis. No estado de SP, só a capital divulga as transações de ITBI. Portais como ZAP, VivaReal e FipeZap mostram apenas preço anunciado. Para não inventar nem estimar nada, cada linha só entra com documento oficial:

1. **Resposta a pedido LAI** às prefeituras: transações de ITBI sem nomes nem CPF. Os textos prontos estão em [docs/](docs/).
2. **Certidão de matrícula** do Registro de Imóveis: o valor do ato de compra e venda. O passo a passo está em [docs/guia_certidoes_cartorio.md](docs/guia_certidoes_cartorio.md).

## Conteúdo

| Arquivo | O que é |
|---|---|
| `base_imoveis_vendidos.xlsx` | A base. Abas: Instruções, Vendas, Bairros, Listas, Resumo, Análise ITBI, Padrão, Fontes, Regras, Referências e Galeria |
| `docs/pedido_LAI_sao_sebastiao.md` / `docs/pedido_LAI_bertioga.md` | Pedidos LAI prontos para protocolar |
| `docs/recurso_LAI.md` | Modelo de recurso para negativa ou resposta parcial |
| `docs/guia_certidoes_cartorio.md` | Qual cartório procurar, como pedir a certidão, como ler e lançar os dados, fotos |
| `docs/analise_subdeclaracao_ITBI.md` | Análise de mercado sobre subdeclaração no ITBI: o que já foi publicado, contexto legal e método |
| `scripts/analisar_subdeclaracao.py` | Gera `relatorio_subdeclaracao.md` com os indicadores calculados das vendas validadas |
| `scripts/importar_lai.py` | Importa o arquivo de ITBI da prefeitura aplicando as regras |
| `scripts/vincular_fotos.py` | Liga as fotos de `fotos/` às vendas e monta a Galeria |
| `scripts/gerar_planilha.py` | Recria a planilha vazia |
| `mapa_colunas_exemplo.json` | Modelo de mapeamento das colunas do arquivo da prefeitura |

## Fluxo de uso

```bash
pip install -r requirements.txt

# 1. Quando a prefeitura responder a LAI:
cp mapa_colunas_exemplo.json mapa_colunas_bertioga.json   # ajuste nomes das colunas, protocolo, cidade
python scripts/importar_lai.py resposta_bertioga.xlsx mapa_colunas_bertioga.json --simular   # confere antes
python scripts/importar_lai.py resposta_bertioga.xlsx mapa_colunas_bertioga.json

# 2. Certidões: lançar à mão na aba Vendas (ver guia)

# 3. Análise de subdeclaração no ITBI (depois que houver vendas validadas)
python scripts/analisar_subdeclaracao.py

# 4. Fotos: salvar como fotos/<ID>.jpg (ou <ID>_2.jpg ...) e rodar
python scripts/vincular_fotos.py
```

Com a planilha aberta no Excel, os scripts não conseguem gravar. Feche o arquivo antes de rodar.

## Regras de validação (resumo)

- **Valor real** = preço da escritura registrada ou valor da transação declarado no ITBI. A base de cálculo do ITBI e o valor venal ficam em colunas próprias.
- Só entra **compra e venda onerosa**. Doação, herança, permuta, leilão etc. aparecem no relatório como rejeitados.
- **Alerta** quando o valor de venda é menor ou igual ao valor venal do IPTU, um possível sinal de subdeclaração. O valor não é alterado.
- **Duplicidade:** cidade + matrícula (ou inscrição) + data.
- **Bairro** só da lista oficial. Para Bertioga vale a LC 99/2013. São Sebastião não tem lei de bairros localizada, então vale a malha de bairros do IBGE/Censo 2022. Nomes populares são convertidos só pelos apelidos que você declarar no JSON.
- Sem metragem no documento, a área e o R$/m² ficam **vazios**.
- **Padrão** vem do cadastro municipal, de documento ou de vistoria (NBR 12721). Fora disso, fica "Não informado".
- **Foto** só do próprio imóvel: tirada no local, Street View nas coordenadas ou imagem de documento.
- O **Resumo** considera só as linhas com Status "Validado".

## Limitações

- O valor da escritura também pode estar subdeclarado. A planilha sinaliza esses casos, mas não tem como provar o valor "de fato".
- A prefeitura pode negar o pedido ou mandar dados agregados. Nesse caso, use o recurso.
- As certidões são pagas e pedidas uma a uma, por imóvel.
- Em Bertioga, matrículas anteriores a abril de 2025 podem estar no 1º RI de Santos.
