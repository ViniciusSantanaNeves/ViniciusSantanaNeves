# Transcritor de vídeos do Vimeo

Ferramenta para baixar o áudio de vídeos do Vimeo (curso / área de membros, usando **o seu acesso**) e transcrever tudo em português. Para cada vídeo gera:

- um **`.txt`** — texto corrido, pronto pra ler/copiar;
- um **`.srt`** — legenda com tempos (útil pra revisar ou legendar).

Os 39 vídeos da sua lista já estão em [`videos.json`](./videos.json), com número, título e seção. O item 11 (eBook) não tem vídeo e foi omitido.

> **Por que preciso rodar isso no meu computador?**
> Os vídeos são **privados** no Vimeo (retornam erro 403 pra quem não tem acesso). Só a sua máquina, com você logado no curso, consegue baixá-los. O script usa esse seu acesso — nada de senha fica salvo em lugar nenhum.

---

## 1. Pré-requisitos

### a) Python 3.9+
Confira com `python --version`. Se não tiver, baixe em [python.org](https://www.python.org/downloads/).

### b) ffmpeg (obrigatório — é o que extrai o áudio)
- **Windows:** `winget install Gyan.FFmpeg` (ou baixe em [ffmpeg.org](https://ffmpeg.org/download.html))
- **Mac:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

### c) Dependências Python
Dentro da pasta `transcricao-vimeo`:

```bash
pip install -r requirements.txt
```

---

## 2. Configurar o seu acesso

Os vídeos são privados, então o `yt-dlp` precisa se autenticar como **você**. A forma mais simples pra aluno é usar os **cookies do navegador** onde você assiste ao curso (fique logado no site antes de rodar).

Defina **uma** variável de ambiente (ou combine mais de uma):

| Variável | Quando usar | Exemplo |
|---|---|---|
| `COOKIES_FROM_BROWSER` | Você assiste logado num navegador | `chrome`, `firefox`, `edge`, `brave`, `safari` |
| `COURSE_REFERER` | O vídeo é "restrito por domínio" (só toca no site do curso) | `https://site-do-curso.com.br` |
| `VIMEO_PASSWORD` | O vídeo é protegido por senha | `a-senha-do-video` |

**Comece só com os cookies.** Se der 403, adicione o `COURSE_REFERER` com o endereço do site onde os vídeos aparecem.

---

## 3. Rodar

**Windows (PowerShell):**
```powershell
$env:COOKIES_FROM_BROWSER="chrome"
python transcrever.py
```

**Mac / Linux:**
```bash
COOKIES_FROM_BROWSER=chrome python transcrever.py
```

Pronto. Ele vai baixar, transcrever e salvar tudo na pasta `transcricoes/`. Pode parar quando quiser (`Ctrl+C`) e rodar de novo depois — **vídeos já transcritos são pulados automaticamente**.

---

## 4. Qualidade x velocidade (motor de transcrição)

Por padrão usa o **faster-whisper**, que roda **no seu PC, de graça**. O modelo `small` é o padrão (bom equilíbrio). Pra mais precisão, use um modelo maior:

```bash
WHISPER_MODEL=medium COOKIES_FROM_BROWSER=chrome python transcrever.py
```

Opções: `tiny` < `base` < `small` < `medium` < `large-v3` (maior = mais preciso, porém mais lento; sem placa de vídeo, `medium` já fica lento).

### Alternativa: API da OpenAI (paga, rápida, não pesa no PC)
```bash
pip install openai
MOTOR=openai OPENAI_API_KEY=sk-xxxx COOKIES_FROM_BROWSER=chrome python transcrever.py
```

---

## 5. Outras opções

| Variável | Padrão | O que faz |
|---|---|---|
| `IDIOMA` | `pt` | Idioma da transcrição |
| `MANTER_AUDIO` | (desligado) | `1` mantém os `.mp3` baixados em `audios/` |
| `WHISPER_MODEL` | `small` | Tamanho do modelo local |
| `MOTOR` | `faster-whisper` | `openai` usa a API paga |

---

## 6. Deu erro?

- **`HTTP Error 403` / "Sorry"** → é acesso. Confirme que está **logado** no navegador certo e que passou `COOKIES_FROM_BROWSER`. Se persistir, adicione `COURSE_REFERER` com o domínio do curso.
- **`ffmpeg not found`** → instale o ffmpeg (passo 1b).
- **`yt-dlp: command not found`** → rode `pip install -r requirements.txt` e use o mesmo Python.
- **Um vídeo específico falha** → o resumo no final lista quais falharam e em qual etapa. Corrija o acesso e rode de novo; só os que faltam serão refeitos.

---

## Estrutura

```
transcricao-vimeo/
├── videos.json        # lista dos vídeos (número, título, seção, ID)
├── transcrever.py     # o script
├── requirements.txt   # dependências
├── README.md          # este guia
├── audios/            # áudios baixados (temporários; ignorados pelo git)
└── transcricoes/      # RESULTADO: .txt e .srt por vídeo (ignorado pelo git)
```
