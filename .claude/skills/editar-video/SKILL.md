---
name: editar-video
description: Edita um vídeo falado (Reel de imóvel, anúncio de cliente, talking head) com o pipeline video-pipeline/ — corta silêncios, transcreve, escreve a pauta de edição (legendas, cartões, zooms) e renderiza com HyperFrames. Use para "edita esse vídeo", "faz o reel desse imóvel", "/editar-video <nome>".
---

# Editar vídeo (pipeline da equipe)

O pipeline fica em `video-pipeline/`. Você (Claude) faz o papel do editor: lê a transcrição e decide **o que** entra na tela. Os scripts fazem o **como**.

## Passo a passo

1. **Preparar e transcrever** — com o vídeo e um nome curto (ex.: `ap-jardim-botanico`):
   ```bash
   cd video-pipeline && ./editar.sh <video.mp4> <nome>
   ```
   Sem pauta, ele corta os silêncios, transcreve e para. Leia `trabalhos/<nome>/transcricao.json`
   (lista de palavras com `start`/`end` em segundos — os tempos já são do vídeo cortado).

2. **Perguntar só o que falta** (uma vez, tudo junto): tipo do vídeo, dados que não estão na fala
   (preço, metragem, bairro, nome do cliente), palavra do CTA e cor da marca. Se a fala já tem tudo, não pergunte.

3. **Escrever `trabalhos/<nome>/pauta.json`** seguindo `video-pipeline/exemplos/pauta-imovel.json`.

4. **Montar, conferir e olhar antes de renderizar:**
   ```bash
   SO_PREVIEW=1 ./editar.sh <video.mp4> <nome>          # abre o preview para a pessoa ajustar
   cd trabalhos/<nome>/projeto && ../../../node_modules/.bin/hyperframes snapshot --frames 8
   ```
   Leia o `contact-sheet.jpg`. Corrija: cartão cobrindo o rosto, legenda sobre texto já gravado no vídeo,
   palavra cortada, cartão sobreposto a outro. Repita até ficar limpo.

5. **Renderizar:** `./editar.sh <video.mp4> <nome>` → `trabalhos/<nome>/editado.mp4`.

## Regras da pauta

**Correções (`correcoes`)** — conserte o que o Whisper errou: nomes de bairros, ruas, marcas e termos
("Gormet" → "gourmet", "há 5 minutos" → "a 5 minutos"). A chave é a palavra exatamente como veio (sem pontuação final).

**Legenda (`legenda.estilo`)**
- `dinamico` (Reels, anúncios, ganchos): 2–3 palavras por bloco, maiúsculas, destaque na cor da marca.
- `limpo` (institucional, clientes sóbrios, alto padrão): 4–5 palavras, caixa baixa, fundo translúcido.
- `nenhuma` quando o vídeo já tem legenda gravada.
- `baseY` padrão 1220 (o limite seguro do Reels é 1248). Se o rosto estiver baixo no quadro, suba (ex.: 1100).

**Destaques (`destaques`)** — 3 a 6 palavras-chave que vendem (bairro, diferencial, “suíte”, “gourmet”, a palavra do CTA). Números já são destacados sozinhos (`"destacarNumeros": false` desliga).

**Cartões (`cartoes`)** — aparecem na faixa de cima (y 300–700), longe da legenda.
- Um cartão por ideia, **sem sobreposição de tempo**, entre 1,5 s e 4 s cada. Um novo a cada 2–4 s em Reels.
- Entram quando a palavra correspondente começa (use o `start` da palavra) e saem antes do próximo.
- Tipos:
  - `numero` — `valor`, `rotulo`. Metragem, anos de mercado, "70 franquias".
  - `ficha` — `titulo`, `subtitulo`, `itens: [[valor, rótulo], …]` (até 3). Quartos/suítes/vagas.
  - `titulo` — `rotulo`, `titulo`. Bairro, capítulo de explicador, nome do cliente.
  - `preco` — `rotulo`, `valor` (fundo na cor da marca). Preço, condição, desconto.
  - `cta` — `texto`, `palavra`, `rodape`. Sempre o último, com pelo menos 2 s na tela (o vídeo segura o último quadro por `segurarFinal`, padrão 1 s).
- Não invente dado. Valor que não foi falado nem informado pela pessoa não entra.

**Zooms (`zooms`)** — punch-in de 1,08–1,15 na frase de impacto (preço, diferencial), 1 a cada 4–6 s, nunca durante um cartão `ficha`. `"suave": true` para aproximação lenta.

## Ao terminar

Diga onde está o MP4, quanto tempo de silêncio foi cortado, e liste em uma linha o que a pessoa pode
ajustar no preview (texto dos cartões, cores, tempos). Se ela pedir mudança, edite só a pauta e rode de novo —
a transcrição é reaproveitada.
