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

## Raio-X completo para a equipe (novo)

Além do Raio-X Express (gratuito, motor de regras), o site tem uma **área interna da equipe** em `/equipe` que roda o **Raio-X do Anúncio completo**: 18 blocos em 6 fases, análise visual das fotos pela IA, radar de mudanças do algoritmo do Airbnb (com busca na web e cache de 7 dias), auditoria de completude, aplicações prontas e plano 30/60/90, tudo no PDF oficial do design system 33hosts. Não depende do Claude Code: qualquer pessoa da equipe com a senha roda direto do navegador.

**Como ativar:**

1. Defina `ANTHROPIC_API_KEY` (obrigatória para o completo).
2. Defina `RAIOX_EQUIPE_SENHA` com a senha que a equipe vai usar (sem ela, a área fica desativada).
3. Acesse `https://seu-site/equipe`, informe a senha e cole o link do anúncio. A análise leva de 3 a 6 minutos e o PDF sai na própria página.

```
ANTHROPIC_API_KEY=sk-ant-...        # obrigatória para o Raio-X completo
RAIOX_EQUIPE_SENHA=uma-senha-forte  # libera a área /equipe
MODELO_RAIOX=claude-opus-5-5        # opcional, este é o padrão
```

Custo aproximado por análise completa (modelo padrão): US$ 0,25 a 0,45, dominado pelas fotos enviadas para a análise visual e pelo tamanho do relatório. O radar com busca na web roda no máximo 1 vez por semana e custa centavos. A metodologia (regras de escrita, benchmarks, blocos e radar-base) fica em `metodologia.py`; para ajustar o comportamento do relatório é lá que se edita.

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
├── app.py                 # site (FastAPI): página pública, área da equipe, downloads
├── scraper.py             # leitura dos dados públicos do anúncio
├── analise.py             # motor de regras do Express + camada opcional de IA
├── relatorio.py           # PDF do Raio-X Express
├── metodologia.py         # metodologia oficial do Raio-X completo (prompt + esquema + radar-base)
├── raiox_completo.py      # orquestrador do Raio-X completo (coleta, radar, análise com IA)
├── relatorio_completo.py  # PDF completo no design system (capa full-bleed, 18 blocos)
├── static/fonts/          # Linear Grotesk (fonte da marca)
├── requirements.txt
├── Dockerfile
└── README.md
```
