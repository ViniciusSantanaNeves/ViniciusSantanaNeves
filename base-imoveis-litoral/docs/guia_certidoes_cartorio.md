# Guia: certidões de matrícula com o valor real de venda

A certidão de matrícula (inteiro teor) mostra o histórico de cada imóvel. Toda compra e venda registrada vira um ato **R-n** ("Registro"), com a data, o título (escritura pública ou contrato com força de escritura, como o financiamento do SFH/SFI) e o **valor da transação**. Esse valor é o dado que vai para a coluna "Valor de venda".

## 1. Qual cartório

| Cidade | Cartório | Site |
|---|---|---|
| São Sebastião | Oficial de Registro de Imóveis e Anexos de São Sebastião, Rua Anjolino Viola, 465, Centro, (12) 3892-4700 | https://www.risaosebastiao.com.br |
| Bertioga (matrículas abertas a partir de 01/04/2025) | Oficial de Registro de Imóveis, Títulos e Documentos e Civil de Pessoa Jurídica de Bertioga, criado pela Lei Estadual 18.075/2024, Rua Antônio Rodrigues de Almeida, 321, Centro, (13) 3150-1175 | https://registrobertioga.com.br/ |
| Bertioga (histórico anterior) | 1º Oficial de Registro de Imóveis de Santos, que atendia Bertioga até a instalação do cartório local | https://www.1risantos.com.br/ |

> **Bertioga, atenção:** pela Lei 6.015/1973, art. 169, a matrícula só passa para o cartório novo quando houver um novo ato. Imóveis vendidos antes de abril de 2025 e sem movimentação depois disso podem ter a matrícula ainda em Santos. Na dúvida, pergunte ao cartório de Bertioga onde está a matrícula. Não encontrei uma regra publicada que defina isso para todos os casos.

## 2. Pedido online (RI Digital / SAEC, do ONR)

O portal oficial é **https://ridigital.org.br/** (o antigo registradores.onr.org.br redireciona para ele).

1. Crie a conta e entre no portal.
2. Escolha **Certidão Digital** e selecione o cartório da tabela acima.
3. Informe o **número da matrícula**. Se não souber o número:
   - use o **número da matrícula que vier na resposta da LAI** (o pedido LAI pede esse campo);
   - ou peça ao cartório uma **pesquisa pelo endereço ou pela inscrição do IPTU**. A pesquisa costuma ser cobrada à parte.
4. Escolha "inteiro teor" e pague. A tabela de valores fica em ridigital.org.br › Consulta de taxas. Os emolumentos são fixados por lei estadual e mudam todo ano, então confira o valor no portal.
5. A certidão chega em PDF assinado digitalmente.

Os cartórios também atendem pedidos pelo próprio site ou no balcão.

## 3. Como ler a certidão

1. Procure o **último ato "R-n" de compra e venda** ou, para um histórico completo, cada um deles. A frase costuma ser: *"Nos termos da escritura de venda e compra lavrada em ..., o proprietário ... transmitiu por venda feita a ..., pelo preço de R$ ..."*.
2. Anote:
   - o **valor** (preço declarado);
   - a **data da escritura** (a data do título, que aparece no texto);
   - a **data do registro** (a data do ato R-n);
   - o número do ato (ex.: **R-7**).
3. Se a matrícula informar, anote a **área** (privativa/construída e do terreno) que aparece na descrição do imóvel ou numa averbação de construção (**Av-n**).
4. Se houver averbação do **valor venal** ou da guia de ITBI, anote o valor em "Base de cálculo ITBI" ou "Valor venal IPTU", conforme o caso.
5. **Fica fora da base:** registros de doação, partilha/inventário, permuta, integralização de capital, arrematação, adjudicação e consolidação da propriedade fiduciária. Também fica fora a alienação fiduciária, que é uma garantia e não uma venda.

## 4. Lançar na planilha (aba Vendas)

| Coluna | O que colocar |
|---|---|
| ID | `CRI-SS-<matrícula>-<ato>` ou `CRI-BE-<matrícula>-<ato>`, ex.: `CRI-SS-12345-R7` |
| Fonte | Certidão de matrícula (CRI) |
| Documento comprobatório | `Matrícula 12.345 — R-7` (o importador de LAI usa esse formato para achar duplicidades) |
| CRI / Órgão | nome do cartório |
| Natureza | Compra e venda |
| Valor de venda | preço do ato R-n |
| Áreas | só o que estiver escrito na matrícula |
| Padrão | conforme a aba Padrão. Se a matrícula não disser, use "Não informado" |
| Status | "Validado" depois de conferir e arquivar o PDF |

Registre cada certidão na aba **Fontes**, com o caminho do PDF e o custo.

## 5. Foto da fachada

- Tire a foto no local e salve como `fotos/<ID>.jpg`. Se houver mais de uma, use `fotos/<ID>_2.jpg`, e assim por diante.
- Rode `python scripts/vincular_fotos.py`. Se a foto tiver data e GPS no EXIF, o script preenche a "Data da foto" e as "Coordenadas".
- Sem foto própria: cole as coordenadas do imóvel e a coluna Street View gera o link. Em "Origem da foto", marque "Google Street View (link)".
- Nunca use foto de anúncio, a não ser que você confirme que é o mesmo imóvel.
