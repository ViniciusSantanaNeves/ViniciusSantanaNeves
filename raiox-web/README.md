# Raio-X Express · 33hosts

Site em que o proprietário cola o link do anúncio do Airbnb e baixa um **PDF com a análise automática**, no design da 33hosts.

## Como funciona

1. A pessoa cola o link do anúncio (aceita link normal `/rooms/...` e links de compartilhar `/l/...` e `/h/...`).
2. O sistema lê a página pública do anúncio: título, nota, número de avaliações, Superhost, quartos, camas, banheiros e fotos.
3. Um motor de regras avalia os itens visíveis (título, volume de fotos, prova social, estrutura) e monta o relatório com símbolos e legenda.
4. O PDF é gerado no design system 33hosts (Linear Grotesk, preto e dourado, capa inteira) e fica disponível para download.
5. O relatório termina com o convite para o **Raio-X completo** (o produto pago, feito por especialista). O site é uma ferramenta de captação de leads.

## Análise com IA (opcional)

Sem configurar nada, o site já funciona com o motor de regras.
Se você definir a variável `ANTHROPIC_API_KEY`, o relatório passa a incluir um resumo personalizado e **3 sugestões de título** geradas por IA.

```
ANTHROPIC_API_KEY=sk-ant-...      # opcional
MODELO_IA=claude-sonnet-4-5       # opcional, este é o padrão
GHL_WEBHOOK_URL=https://...       # opcional, envia cada lead para o GoHighLevel
CHROME_PATH=/usr/bin/chromium     # caminho do Chromium (o Docker já configura)
```

## Captação de leads no GHL (GoHighLevel)

O formulário pede **nome e WhatsApp** antes de liberar a análise. Se você configurar a variável `GHL_WEBHOOK_URL`, cada análise envia o lead automaticamente para o seu GHL, já com a tag `avaliacao-nova`.

**Como configurar no GHL:**

1. No GHL, vá em **Automation > Workflows > Create Workflow** (comece do zero).
2. Adicione o gatilho **Inbound Webhook** e copie a URL que o GHL mostrar.
3. No Render (ou onde o site estiver publicado), crie a variável de ambiente `GHL_WEBHOOK_URL` com essa URL.
4. De volta ao workflow, faça uma análise de teste no site para o GHL receber um exemplo e mapear os campos.
5. Adicione as ações: **Create/Update Contact** (nome = `nome`, telefone = `whatsapp`) e **Add Tag** com `avaliacao-nova`. Se quiser, adicione uma notificação interna para o time comercial.
6. Publique o workflow.

**Campos enviados em cada lead:**

| Campo | Conteúdo |
|---|---|
| `nome`, `whatsapp` | dados digitados pelo proprietário |
| `origem` | sempre `raiox-express` |
| `tag` | sempre `avaliacao-nova` |
| `link_anuncio`, `titulo_anuncio`, `local` | dados do anúncio analisado |
| `nota`, `avaliacoes`, `superhost`, `fotos` | prova social e volume de fotos |
| `blocos_ok`, `blocos_melhorar`, `blocos_corrigir` | placar da análise |

Sem a variável configurada, o site funciona normalmente e apenas não envia o lead. O envio nunca trava a análise: se o GHL estiver fora do ar, o PDF sai do mesmo jeito.

## Rodar localmente

```bash
cd raiox-web
pip install -r requirements.txt
# instale o Chromium (Linux: apt install chromium | Mac: brew install chromium)
CHROME_PATH=$(which chromium) uvicorn app:app --port 8000
```

Abra http://localhost:8000, cole um link do Airbnb e baixe o PDF.

## Publicar na internet (Render, Railway ou Fly.io)

O projeto tem `Dockerfile`, então qualquer serviço que rode Docker funciona:

**Render (gratuito para começar):**
1. Suba este repositório no GitHub (já está).
2. Em render.com: New > Web Service > conecte o repositório.
3. Root Directory: `raiox-web`. Runtime: Docker.
4. (Opcional) Adicione a variável `ANTHROPIC_API_KEY` em Environment.
5. Deploy. O Render entrega uma URL pública (ex.: `raiox-express.onrender.com`).

**Railway:** New Project > Deploy from GitHub repo > aponte para a pasta `raiox-web`.

## Avisos importantes

- A análise usa somente a **página pública** do anúncio. Nenhuma senha é pedida.
- O Airbnb pode limitar acessos vindos de alguns servidores. Se a coleta falhar com frequência no seu provedor de hospedagem, teste outro provedor ou região.
- Os PDFs gerados são apagados automaticamente depois de 2 horas.

## Estrutura

```
raiox-web/
├── app.py          # site (FastAPI): página inicial, análise e download
├── scraper.py      # leitura dos dados públicos do anúncio
├── analise.py      # motor de regras + camada opcional de IA
├── relatorio.py    # relatório HTML no design system + geração do PDF
├── static/fonts/   # Linear Grotesk (fonte da marca)
├── requirements.txt
├── Dockerfile
└── README.md
```
