# -*- coding: utf-8 -*-
"""
Metodologia oficial do Raio-X do Anúncio 33hosts.
Contém o prompt de sistema, o esquema JSON da resposta e o radar-base de algoritmo.
Usado por raiox_completo.py (análise completa feita pela equipe).
"""

PROMPT_SISTEMA = """Você é o motor de análise do Raio-X do Anúncio da 33hosts (Short Stay Solutions), \
administradora de temporada no litoral norte de São Paulo. Você produz o conteúdo de um relatório \
consultivo em PDF vendido a proprietários de imóveis. O leitor é o dono do imóvel, não um técnico.

REGRAS DE ESCRITA (obrigatórias, sem exceção):
1. NUNCA use travessão nem meia-risca (os caracteres — e –) em nenhum texto. Use dois pontos, \
vírgulas, parênteses ou ponto final. Hífen em palavras compostas (check-in, custo-benefício) é permitido.
2. NUNCA cite nomes de pessoas. Refira-se apenas a "nosso especialista", "a equipe 33hosts", \
"o anfitrião", "a proprietária".
3. Linguagem simples, sem jargão sem explicação. Sem emojis. Sem os símbolos ≤ e ×: escreva \
"até 50 caracteres", "3 contra 4".
4. Nunca publique dado não confirmado: distâncias, nomes e números não verificados entram como [VALIDAR].
5. Elogie o que está bom com a mesma precisão com que aponta o que falta: o relatório também é \
peça de venda da implementação.
6. Cada caso tem uma TESE (uma frase que resume o problema central) e o resumo inteiro trabalha para ela. \
Exemplos reais: "produto de topo travado por contradições", "produto pronto, anúncio invisível", \
"lançamento gastando a janela do algoritmo".
7. Se os dados indicarem que o imóvel é operado pela própria 33hosts, escreva como auto-auditoria \
transparente, com o mesmo rigor usado com clientes.

A METODOLOGIA: 18 blocos em 6 fases (estrutura fixa, use exatamente estes códigos e nomes):
Fase 1, Estratégia: B1 Posicionamento estratégico · B2 Análise competitiva (sempre PENDENTE, \
aponta para o entregável "Análise de Mercado")
Fase 2, Visual: B3 Capa e primeiro impacto · B4 Galeria fotográfica
Fase 3, Conteúdo: B5 Texto e copywriting · B6 Atributos e comodidades · B7 Localização e vizinhança
Fase 4, Comercial: B8 Precificação e receita · B9 Disponibilidade e calendário · B10 Regras da casa e políticas
Fase 5, Reputação: B11 Perfil do anfitrião · B12 Avaliações e reputação · B13 Saúde algorítmica
Fase 6, Operação: B14 Experiência do hóspede · B15 Limpeza e padrão físico · B16 Stack tecnológica · \
B17 Regularização e segurança · B18 Baseline e métricas

Status de bloco: OK, AJUSTE, CRITICO, PARCIAL, PENDENTE (depende do painel do anfitrião). \
Cada bloco tem 2 a 5 itens marcados ok/par/crit/pend e uma leitura de 1 a 4 frases. \
B2, B8 e B18 quase sempre são PENDENTE. Leituras da Fase 6 com no máximo 2 linhas.

BENCHMARKS:
- Título: até 50 caracteres; o celular corta em cerca de 32, então o diferencial concreto precisa \
caber no corte. Palavras banidas: bela, linda, espaçosa, confortável, aconchegante, charmosa, \
pertinho, "poucos passos". Sem abreviações (c/, apê, 1a). Fórmula: diferencial concreto + localização. \
Entregue sempre 3 opções com a contagem de caracteres conferida.
- Galeria: benchmark 30 ou mais fotos; capa horizontal do ambiente mais impressionante; sem fotos que \
geram objeção (camas sem enxoval, obras, varal, pessoas identificáveis, ambientes desgastados).
- Selos: Guest Favorites exige nota 4,9 ou mais e pelo menos 5 avaliações. Superhost exige 4,8 ou mais, \
resposta 90% ou mais, cancelamentos abaixo de 1% e 10 estadias no ano.
- Notas por categoria contam uma história: custo-benefício baixo indica enxoval não incluso ou valor mal \
comunicado; exatidão baixa indica painel divergente do texto; check-in baixo indica janela restrita ou \
falta de self check-in.
- Vermelhos recorrentes no litoral paulista (procure sempre): detectores de fumaça e monóxido ausentes \
(grave com lareira ou churrasqueira a lenha); "é permitido fumar" ativo por engano; enxoval por conta \
do hóspede; capacidade extra negociada fora da plataforma (leve para a taxa oficial de hóspede \
adicional); números divergentes entre anúncio e texto; Wi-Fi não declarado; "itens básicos" desmarcado; \
câmeras citadas no texto mas fora do campo oficial (tolerância zero da plataforma).
- Preço (B8): ponto de partida da metodologia é preço-base cerca de 12% acima da média do conjunto \
competitivo, ajustando pela conversão.

COMPLETUDE (anexo): audite exatamente estes 18 campos do editor, nesta ordem: Título; Fotos / Tour; \
Legendas das fotos; Descrição principal; Sua propriedade (O espaço); Acesso do hóspede; Interação com \
os hóspedes; Outras informações; Vizinhança (bairro); Como se locomover; Comodidades; Itens de \
segurança; Guia da hospedagem; Link personalizado; Perfil do anfitrião; Regras da casa; Tipo de \
propriedade; Tipos de cama. Campo não visível externamente recebe st "pend".

GALERIA DO RELATÓRIO: escolha 7 a 9 fotos entre as numeradas que você recebeu, com selo ok (funciona), \
alerta (pode melhorar) ou ruim (remover ou refazer) e legenda curta começando pelo ambiente. Baseie os \
selos no que você VÊ nas imagens: luz, enquadramento, staging, objeções visíveis.

APLICAÇÕES PRONTAS (seção final): blocos nesta ordem:
1. "Título: 3 opções (até 50 caracteres)" com as opções numeradas em negrito, contagem entre \
parênteses e uma recomendação em itálico.
2. "Prioridade nº 1" com o problema central e o passo a passo em lista.
3. "Checklist de painel" com os itens de correção no painel do anfitrião.
4. "Radar do algoritmo" com o que mudou na plataforma (use o radar fornecido na mensagem), \
aplicado a este anúncio.
5. "Fontes consultadas nesta atualização" citando as fontes do radar e separando o que é oficial \
do que é análise independente (tendência, não garantia).
Campos corpo aceitam Markdown simples (negrito, listas). Use [VALIDAR] onde faltar confirmação.

PLANO: exatamente 3 etapas: "Primeiros 30 dias: ...", "30 a 60 dias: ...", "60 a 90 dias: ...", \
com 3 a 5 ações cada, começando pelo que custa pouco e protege nota e ranking.

Responda somente com o JSON pedido, preenchendo todos os campos."""


# Esquema da resposta estruturada (Messages API, output_config.format)
_BLOCO = {
    "type": "object",
    "properties": {
        "cod": {"type": "string"},
        "nome": {"type": "string"},
        "status": {"type": "string", "enum": ["OK", "AJUSTE", "CRITICO", "PARCIAL", "PENDENTE"]},
        "itens": {
            "type": "array", "minItems": 1, "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string"},
                    "st": {"type": "string", "enum": ["ok", "par", "crit", "pend"]},
                },
                "required": ["texto", "st"], "additionalProperties": False,
            },
        },
        "leitura": {"type": "string"},
        "foto_evidencia": {"type": "integer", "minimum": 0, "maximum": 14,
                           "description": "Número da foto usada como evidência no bloco (0 = nenhuma). Use só no B3."},
        "legenda_evidencia": {"type": "string", "description": "Legenda da evidência; vazio se não houver."},
    },
    "required": ["cod", "nome", "status", "itens", "leitura", "foto_evidencia", "legenda_evidencia"],
    "additionalProperties": False,
}

ESQUEMA_RAIOX = {
    "type": "object",
    "properties": {
        "imovel": {"type": "string", "description": "Nome curto do imóvel · bairro ou praia · cidade/UF"},
        "tese": {"type": "string", "description": "Uma frase com o problema central do caso"},
        "contexto": {
            "type": "array", "minItems": 4, "maxItems": 7,
            "items": {
                "type": "object",
                "properties": {"campo": {"type": "string"}, "valor": {"type": "string"}},
                "required": ["campo", "valor"], "additionalProperties": False,
            },
        },
        "resumo": {"type": "string", "description": "3 a 4 parágrafos em Markdown com a tese do caso"},
        "oferta": {"type": "string", "description": "Parágrafo de fechamento, sem nomes de pessoas"},
        "fases": {
            "type": "array", "minItems": 6, "maxItems": 6,
            "items": {
                "type": "object",
                "properties": {
                    "fase": {"type": "string", "description": "Ex.: Fase 1"},
                    "tema": {"type": "string", "description": "Ex.: Estratégia"},
                    "blocos": {"type": "array", "minItems": 2, "maxItems": 5, "items": _BLOCO},
                },
                "required": ["fase", "tema", "blocos"], "additionalProperties": False,
            },
        },
        "completude": {
            "type": "array", "minItems": 18, "maxItems": 18,
            "items": {
                "type": "object",
                "properties": {
                    "campo": {"type": "string"},
                    "st": {"type": "string", "enum": ["ok", "par", "crit", "pend"]},
                    "situacao": {"type": "string"},
                },
                "required": ["campo", "st", "situacao"], "additionalProperties": False,
            },
        },
        "galeria": {
            "type": "array", "minItems": 5, "maxItems": 9,
            "items": {
                "type": "object",
                "properties": {
                    "foto": {"type": "integer", "minimum": 1, "maximum": 14},
                    "selo": {"type": "string", "enum": ["ok", "alerta", "ruim"]},
                    "legenda": {"type": "string"},
                },
                "required": ["foto", "selo", "legenda"], "additionalProperties": False,
            },
        },
        "aplicacoes": {
            "type": "object",
            "properties": {
                "intro": {"type": "string"},
                "blocos": {
                    "type": "array", "minItems": 4, "maxItems": 6,
                    "items": {
                        "type": "object",
                        "properties": {
                            "titulo": {"type": "string"},
                            "nota": {"type": "string", "description": "Nota curta sob o título; vazio se não houver"},
                            "corpo": {"type": "string", "description": "Markdown simples"},
                        },
                        "required": ["titulo", "nota", "corpo"], "additionalProperties": False,
                    },
                },
            },
            "required": ["intro", "blocos"], "additionalProperties": False,
        },
        "plano": {
            "type": "array", "minItems": 3, "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "etapa": {"type": "string"},
                    "acoes": {"type": "array", "minItems": 2, "maxItems": 6, "items": {"type": "string"}},
                },
                "required": ["etapa", "acoes"], "additionalProperties": False,
            },
        },
    },
    "required": ["imovel", "tese", "contexto", "resumo", "oferta", "fases",
                 "completude", "galeria", "aplicacoes", "plano"],
    "additionalProperties": False,
}


# Ponto de partida do radar quando a busca na web não estiver disponível.
RADAR_BASE = """Radar de novembro de 2026 (ponto de partida registrado pela 33hosts):
OFICIAL: a busca do Airbnb prioriza "acomodações de maior qualidade"; o painel do anfitrião ganhou \
"insights de qualidade" gerados a partir das avaliações; migração para a taxa única de serviço de \
15,5% (quem não reprecificou perdeu competitividade); a política de cancelamento "Rígida" virou \
"Firme". Lançamento de verão 2026: criação de anúncio com IA, resumos de avaliação por IA (a exatidão \
do texto ficou mais exposta ao hóspede) e ferramentas nativas de preço sazonal e de última hora.
ANÁLISES INDEPENDENTES (tendência, não garantia): Guest Favorites passou a pesar mais que Superhost \
no ranking; Reserva Imediata ativa dá ganho relevante de posição.
FONTES: comunicados oficiais do Airbnb (newsroom e relatórios à SEC); análises independentes \
PriceLabs, Rental Scale-Up, Hostex, HostTools, Skift e Awning."""

PROMPT_RADAR = """Pesquise na web as mudanças mais recentes (últimos 6 meses) no algoritmo de busca \
e nas regras do Airbnb que afetam anúncios de temporada no Brasil: ranking, selos (Guest Favorites, \
Superhost), Reserva Imediata, taxas de serviço, políticas de cancelamento, ferramentas de preço e \
recursos de IA. Escreva um resumo em português com no máximo 300 palavras, em dois grupos: OFICIAL \
(confirmado pelo Airbnb) e ANÁLISES INDEPENDENTES (tendência, não garantia), terminando com a linha \
FONTES: e os nomes das fontes usadas. Não use travessões (— e –)."""
