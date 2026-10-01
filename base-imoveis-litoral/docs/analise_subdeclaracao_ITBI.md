# Análise de mercado: subdeclaração do valor de venda no ITBI

**Objetivo:** medir quanto o preço declarado nas compras e vendas de São Sebastião e Bertioga fica abaixo do valor de mercado.

**Situação em 01/10/2026:** a base ainda não tem vendas validadas, então **ainda não há resultado para estas cidades**. Este documento traz:
1. o que já foi publicado sobre o tema, com fontes;
2. o método que a planilha e o script aplicam quando os dados chegarem.

Os números das cidades vão sair de `python scripts/analisar_subdeclaracao.py` e da aba **Análise ITBI**.

---

## 1. O que já se sabe (com fontes)

**Não existe estimativa publicada do percentual de subdeclaração no ITBI para São Sebastião, Bertioga ou o Litoral Norte.** Também não há estimativa nacional. A pesquisa cobriu:
- IPEA;
- Lincoln Institute;
- CNM e FNP;
- TCE-SP;
- notícias.

Os estudos do IPEA (Carvalho Jr., 2020) e do Lincoln Institute (Afonso, Araujo e Nóbrega, 2012) reconhecem que a subdeclaração existe, mas não a medem.

Os dados mais próximos são da **cidade de São Paulo** e **não podem ser transpostos** para o litoral:

| Indicador | Valor | Fonte e ressalva |
|---|---|---|
| Parcela das guias de ITBI em que a base foi o valor de referência da prefeitura (VVR), por ser maior que o declarado | cerca de 20% | Prefeitura de São Paulo, nota de 2014 sobre o VVR. Anterior ao Tema 1.113. [link](https://prefeitura.sp.gov.br/w/noticia/nota-explicacao-sobre-atualizacao-de-vvr-no) |
| Diferença entre preço anunciado e preço da guia de ITBI | 17,88% na média da cidade (dez/2023), indo de −2,8% no Jardim Europa a 34,24% na Mooca | Loft, Índice de Preço Real. **Mistura desconto de negociação com subdeclaração.** [link](https://portal.loft.com.br/ipr-dezembro-sp/) |
| Guias de compra e venda com valor declarado abaixo do VVR | 15,8% nas financiadas contra 27,3% nas à vista (2025) | Benvenho, repositório público, sem revisão por pares. [link](https://github.com/abenvenho/tabpfn-itbi-sp) |

O padrão de São Paulo, em que as **compras à vista ficam abaixo da referência com mais frequência do que as financiadas**, é a hipótese que este método testa no litoral. Ele não serve como resultado para o litoral.

## 2. Contexto legal

- **STJ, Tema 1.113 (REsp 1.937.821/SP, 2022):** a base do ITBI é o valor de mercado. Presume-se que o valor declarado corresponde a ele, e o município só pode recusá-lo por processo próprio (CTN, art. 148). O município não pode impor antes um valor de referência unilateral. [STJ](https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/09032022-Base-de-calculo-do-ITBI-e-o-valor-do-imovel-transmitido-em-condicoes-normais-de-mercado--define-Primeira-Secao.aspx)
- **LC 227/2026:** mudou o art. 38 do CTN.
  - Valor venal passa a ser o valor de negociação "à vista, em condições normais de mercado".
  - O município pode estimá-lo com critérios técnicos, inclusive com dados de cartórios e de agentes financeiros.
  - O contribuinte pode contestar por avaliação contraditória.
  - Na prática, isso reabre a estimativa prévia pelo município. [Migalhas](https://www.migalhas.com.br/depeso/460596/itbi-a-lei-complementar-227-26-e-o-tema-repetitivo-1-113) · [Conjur](https://www.conjur.com.br/2026-mai-16/o-impacto-da-lc-227-2026-na-definicao-da-base-de-calculo-do-itbi/)
- **CTN, art. 148:** o fisco pode arbitrar o valor quando a declaração "não mereça fé".
- **Lei 8.137/90, arts. 1º e 2º:** declaração falsa para reduzir tributo é crime contra a ordem tributária.
- **Lei 9.514/97, art. 24, VI:** o contrato de alienação fiduciária precisa indicar o valor do imóvel para leilão. Esse valor fica registrado na matrícula e é uma **segunda referência documentada de valor** para o mesmo imóvel.

Consequência para a análise: daqui em diante, a coluna "Base de cálculo ITBI" pode refletir a estimativa técnica do município. A razão Declarado ÷ Base passa a medir diretamente a distância entre o que as partes declararam e o que a prefeitura considera mercado.

## 3. Método

Entram só as compras e vendas com Status = Validado. Cada indicador é calculado por cidade, por ano, por padrão e por bairro.

| # | Indicador | O que mede | Como interpretar |
|---|---|---|---|
| 1 | **Declarado ÷ Base ITBI** (mediana, % abaixo de 1, COD) | Distância entre o preço declarado e o valor que a prefeitura usou | % abaixo de 1 = vendas em que a prefeitura considerou o preço baixo e adotou base maior. O COD mostra se a relação é uniforme ou dispersa |
| 2 | **Declarado ÷ Venal IPTU** (mediana, % ≤ 1) | Quanto o preço supera o venal do IPTU | Vendas com preço declarado ≤ venal são sinal forte de subdeclaração, porque o venal do IPTU costuma ficar abaixo do mercado |
| 3 | **R$/m² à vista vs. financiado** | Diferença entre o R$/m² mediano declarado nas vendas à vista e nas financiadas | Na venda financiada, o banco avalia o imóvel e financia uma parte do preço declarado, o que limita a subdeclaração. Uma diferença negativa e persistente **no mesmo bairro e padrão** é indício de subdeclaração nas vendas à vista |
| 4 | **Declarado ÷ Valor para leilão** (alienação fiduciária) | Preço declarado contra o valor do imóvel fixado no contrato de financiamento | Abaixo de 1 = as partes declararam menos do que o valor que elas mesmas fixaram no contrato |
| 5 | **Financiado ÷ Declarado** (% ≥ 1) | Financiamento igual ou maior que o preço | Situação atípica, a investigar caso a caso |

**Regras do método:**
- **Amostra mínima:** com menos de *n* vendas (padrão 5, ajustável na célula B4 da aba e em `--amostra-min`), mediana, COD e comparações aparecem como "amostra insuficiente". Esse limite é uma escolha de método, não um número tirado da literatura.
- **COD:** coeficiente de dispersão do [IAAO Standard on Ratio Studies](https://www.iaao.org/wp-content/uploads/Standard_on_Ratio_Studies.pdf), padrão internacional para estudos de razão entre avaliação e venda. No padrão, as faixas de referência valem para avaliação fiscal, não para subdeclaração. Aqui o COD só descreve a dispersão.

**Limites da análise:**
- O indicador 3 compara grupos de compradores diferentes, e imóveis financiados podem ter outro perfil. Por isso, use os recortes por bairro e padrão, não só a média da cidade.
- Nenhum indicador prova o valor "de fato" de uma venda isolada. Eles mostram padrões no conjunto.
- A base de cálculo e o valor venal dependem das regras de cada prefeitura e de cada ano. Compare anos com cuidado, sobretudo antes e depois da LC 227/2026.
- Os resultados valem só para as vendas que entraram na base. Se a prefeitura mandar dados parciais, registre isso no relatório.

## 4. Dados necessários

Os indicadores dependem de campos que o pedido LAI agora pede expressamente:
- base de cálculo;
- valor venal;
- forma de pagamento / tipo de financiamento;
- valor financiado.

O **valor para leilão** vem da certidão de matrícula, no registro da alienação fiduciária (ver `guia_certidoes_cartorio.md`).

## 5. Como gerar o relatório

```bash
python scripts/analisar_subdeclaracao.py                   # usa a amostra mínima padrão (5)
python scripts/analisar_subdeclaracao.py --amostra-min 10  # mais conservador
```

A saída é o arquivo `relatorio_subdeclaracao.md`, com uma leitura por cidade e as tabelas por cidade, ano, padrão e bairro.
