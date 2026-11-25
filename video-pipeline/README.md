# Pipeline de edição de vídeo com IA

Vídeo bruto entra → vídeo editado sai: sem silêncios, com legendas animadas, cartões
(metragem, ficha do imóvel, preço, CTA) e zooms. O Claude Code faz o papel de editor e
decide o que entra na tela. Os scripts executam.

## 1. Engenharia reversa do Reel

O Reel ("A Skill do Claude mais insana…") não mostra uma skill só. Mostra **quatro peças**
que, juntas, fazem a edição sem trabalho manual:

| No Reel | O que é | Papel no sistema | Aqui |
|---|---|---|---|
| **HyperFrames Studio** — "Make videos with your AI agent" | Framework open source da HeyGen (Apache 2.0): o vídeo é escrito em HTML/CSS/GSAP e renderizado em MP4, quadro a quadro, com Chrome + FFmpeg | **Motor de render**: legendas, cartões e animações viram código | `scripts/montar.mjs` gera o projeto e `hyperframes render` exporta |
| **Whisper** (GitHub) | Reconhecimento de fala da OpenAI | **Transcrição com o tempo de cada palavra**, para as legendas e para saber quando cada cartão entra | `scripts/transcrever.py` (faster-whisper, português) |
| **"The missing design vocabulary for agents"** (Impeccable) e **taste-skill** | Skills que ensinam o agente a evitar o "visual de IA" (Inter, gradiente roxo, cartões genéricos) | **Gosto e consistência visual** | Regras de estilo fixas no montador + skill `/editar-video` |
| **Página de venda dele** ("nove estilos… você escolhe, a máquina faz") | Estilos prontos aplicados por cima do vídeo do cliente | **Templates**: o mesmo vídeo, vários estilos | `legenda.estilo` + tipos de cartão na pauta |

A ideia central que vale copiar: **separar decisão de execução**. A IA lê a fala e escreve uma
*pauta*. Um motor determinístico transforma a pauta em vídeo, e o resultado é sempre igual
para a mesma pauta. Ajustar vira editar um JSON, e não refazer a timeline no CapCut.

## 2. Arquitetura

```
vídeo bruto (celular)
   │
   ▼  0. cortar_silencios.py ── jump cut automático (ffmpeg silencedetect)
bruto.mp4
   │
   ▼  1. transcrever.py ─────── Whisper → transcricao.json (palavra + início + fim)
   │
   ▼  2. Claude Code (/editar-video) lê a fala e escreve pauta.json:
   │       correções · estilo de legenda · destaques · cartões · zooms
   │
   ▼  3. montar.mjs ─────────── gera projeto HyperFrames (index.html + compositions/)
   │
   ▼  4. hyperframes check ──── área segura do Reels, texto cortado, tempo de leitura
   │     hyperframes preview ── ajuste visual no navegador (opcional)
   ▼  5. hyperframes render ─── editado.mp4 (1080×1920, 30 fps)
```

## 3. Instalação (uma vez)

Requisitos: Node 22+, Python 3.10+, FFmpeg, Google Chrome.

```bash
# macOS
brew install node ffmpeg python

cd video-pipeline
npm install                       # instala o HyperFrames
pip install -r requirements.txt   # instala o Whisper (faster-whisper)
npx hyperframes doctor            # confere Chrome/FFmpeg

# Opcional: skills oficiais do HyperFrames no Claude Code
npx hyperframes skills update
```

Na primeira transcrição, o modelo do Whisper (cerca de 500 MB no `small`) é baixado automaticamente.

## 4. Uso no dia a dia

**Com o Claude Code** (recomendado):

```
/editar-video  — edita o vídeo ~/Downloads/IMG_1234.mov, é o ap do Jardim Botânico, CTA "IMÓVEL"
```

O Claude roda o pipeline, lê a transcrição, escreve a pauta, confere os quadros e renderiza.

**Manual:**

```bash
./editar.sh ~/Downloads/IMG_1234.mov ap-jardim     # corta silêncios + transcreve, depois para
# escreva trabalhos/ap-jardim/pauta.json (modelo: exemplos/pauta-imovel.json)
SO_PREVIEW=1 ./editar.sh ~/Downloads/IMG_1234.mov ap-jardim   # olhar no navegador
./editar.sh ~/Downloads/IMG_1234.mov ap-jardim     # renderiza trabalhos/ap-jardim/editado.mp4
```

Variáveis: `CORTAR_SILENCIOS=0`, `SILENCIO_MIN=0.35` (mais rápido) ou `0.6` (mais natural),
`MODELO=medium` (fala com música ou sotaque forte).

## 5. A pauta (`pauta.json`)

Veja `exemplos/pauta-imovel.json`. Campos:

| Campo | O que faz |
|---|---|
| `marca.cor`, `marca.fonte` | Cor de destaque e fonte (fontes prontas: Montserrat, Inter, Poppins, Oswald, Archivo Black…) |
| `legenda.estilo` | `dinamico` (2–3 palavras, maiúsculas, pop), `limpo` (4–5 palavras, fundo translúcido) ou `nenhuma` |
| `legenda.baseY` | Altura da legenda (padrão 1220, logo acima do limite seguro do Reels (1248)) |
| `correcoes` | Conserta palavras que o Whisper errou |
| `destaques` | Palavras pintadas na cor da marca (números já entram automaticamente) |
| `cartoes[]` | `numero`, `ficha`, `titulo`, `preco`, `cta`, cada um com `inicio` e `fim` em segundos |
| `zooms[]` | Punch-in na câmera: `inicio`, `fim`, `escala`, `suave` |
| `segurarFinal` | Segundos congelando o último quadro para o CTA ser lido (padrão 1) |

## 6. Como encaixa no processo atual (CapCut)

| Etapa | Antes (CapCut, manual) | Agora |
|---|---|---|
| Cortar pausas e erros | Manual, corte a corte | Automático (etapa 0) |
| Legendas | Auto-legenda + revisão + estilo à mão | Whisper + correções na pauta + estilo da marca |
| Cartões e preço | Montados um a um em cada vídeo | Tipos prontos; o Claude escolhe pela fala |
| Padrão visual por cliente | Depende de quem edita | Cor e fonte fixas na pauta, sempre iguais |
| Ajustes | Refazer na timeline | Mudar uma linha da pauta e renderizar de novo |
| Acabamento fino (trilha, B-roll especial, color) | CapCut | Continua no CapCut: importe o `editado.mp4` |

O CapCut continua no fluxo, só que no fim e para acabamento, não para o trabalho repetitivo.

## 7. Testado

Teste com uma fala de 18 s de corretor: transcrição correta em português (52 palavras), 5 cartões,
2 zooms, nos dois estilos de legenda, `check` sem erros e sem avisos na área segura do Reels.
O render de 19,6 s em 1080×1920 levou cerca de 1min40 numa máquina sem GPU. Em um Mac costuma ser mais rápido.

## 8. Próximos passos sugeridos

1. **Vídeo só com voz + animação**: aceitar um áudio no lugar do vídeo e preencher a tela com cartões em sequência (explicador).
2. **Fotos do imóvel como B-roll**: `fotos/` → cortes em tela cheia com Ken Burns nos trechos em que o corretor descreve o ambiente.
3. **Presets por cliente**: `marcas/<cliente>.json` com cor, fonte, logo e estilo, e a pauta só aponta para o preset.
4. **Lote**: uma pasta com vários vídeos → um MP4 de cada, com o mesmo preset.
5. **Trilha e efeitos sonoros** com a skill `media-use` do HyperFrames.
