# -*- coding: utf-8 -*-
"""
Motor de análise do Raio-X Express.
Camada 1: regras objetivas sobre os dados públicos do anúncio (sempre roda).
Camada 2: análise com IA (opcional, quando ANTHROPIC_API_KEY estiver configurada).
Linguagem: simples e direta, para o proprietário. Sem travessões nos textos.
"""
import os
import re

PALAVRAS_VAZIAS = ["bela", "belo", "linda", "lindo", "espaçosa", "espaçoso",
                   "confortável", "aconchegante", "ótima", "ótimo", "incrível",
                   "maravilhosa", "maravilhoso", "moderna", "moderno", "luxuosa", "luxuoso"]
ABREVIACOES = [r"\bap\.?\b", r"\bapto\.?\b", r"\bc/\b", r"\bp/\b", r"\bres\.?\b",
               r"\bmod\.?\b", r"\bcond\.?\b", r"\bqto\b", r"\bdorm\.?\b"]


def _tem(padrao, texto):
    return re.search(padrao, texto, re.I) is not None


def analisar_titulo(titulo: str) -> dict:
    itens = []
    problemas = []
    t = titulo or ""
    n = len(t)

    if n == 0:
        itens.append(("Título preenchido", "crit")); problemas.append("sem título")
    else:
        itens.append((f"Título preenchido ({n} de 50 caracteres)", "ok" if n <= 50 else "crit"))

    abrevs = [a for a in ABREVIACOES if _tem(a, t)]
    itens.append(("Sem abreviações que o hóspede precisa decifrar",
                  "ok" if not abrevs else "crit"))
    if abrevs:
        problemas.append("abreviações no título")

    vazias = [p for p in PALAVRAS_VAZIAS if _tem(r"\b%s\b" % p, t)]
    itens.append(("Sem palavras genéricas (bela, espaçosa, confortável...)",
                  "ok" if not vazias else "par"))
    if vazias:
        problemas.append("palavras genéricas: " + ", ".join(vazias))

    caps = sum(1 for w in t.split() if len(w) > 2 and w.isupper())
    itens.append(("Sem palavras inteiras em maiúsculas", "ok" if caps == 0 else "par"))

    gatilhos = ["praia", "mar", "piscina", "vista", "pé na areia", "centro", "resort",
                "sauna", "hidro", "jacuzzi", "natureza", "cachoeira", "pôr do sol"]
    tem_gatilho = any(g in t.lower() for g in gatilhos)
    itens.append(("Comunica um ponto forte (praia, piscina, vista...)",
                  "ok" if tem_gatilho else "crit"))
    if not tem_gatilho:
        problemas.append("título não comunica nenhum ponto forte")

    corte = t[:32]
    gatilho_no_corte = any(g in corte.lower() for g in gatilhos)
    itens.append(("Ponto forte aparece nos primeiros 32 caracteres (o celular corta o resto)",
                  "ok" if gatilho_no_corte else "par"))

    criticos = sum(1 for _, s in itens if s == "crit")
    parciais = sum(1 for _, s in itens if s == "par")
    status = "OK" if criticos == 0 and parciais <= 1 else ("CRITICO" if criticos >= 2 else "AJUSTE")
    return dict(itens=itens, status=status, problemas=problemas)


def analisar_fotos(qtd: int) -> dict:
    itens = [
        (f"Quantidade de fotos: {qtd} (o ideal é ter de 20 a 40, e os melhores anúncios têm 30 ou mais)",
         "ok" if qtd >= 30 else ("par" if qtd >= 20 else "crit")),
        ("Qualidade das fotos (luz, arrumação, nitidez)", "pend"),
        ("Legendas nas fotos contando a experiência", "pend"),
    ]
    status = "OK" if qtd >= 30 else ("AJUSTE" if qtd >= 20 else "CRITICO")
    return dict(itens=itens, status=status)


def analisar_prova_social(nota: str, avaliacoes: str, superhost: bool) -> dict:
    itens = []
    try:
        v = float(str(nota).replace(",", "."))
    except (TypeError, ValueError):
        v = None
    try:
        q = int(avaliacoes)
    except (TypeError, ValueError):
        q = 0

    if v is None:
        itens.append(("Nota do anúncio", "pend"))
        status = "PENDENTE"
    else:
        itens.append((f"Nota {nota} de 5", "ok" if v >= 4.8 else ("par" if v >= 4.6 else "crit")))
        itens.append((f"Nota dentro do padrão Superhost (4,8 ou mais)", "ok" if v >= 4.8 else "par"))
        itens.append((f"Nota no nível do selo Preferido dos Hóspedes (4,9 ou mais)",
                      "ok" if v >= 4.9 else "par"))
        status = "OK" if v >= 4.8 else "AJUSTE"

    itens.append((f"Volume de avaliações: {q} (a partir de 15 a confiança fica sólida)",
                  "ok" if q >= 15 else ("par" if q >= 5 else "crit")))
    itens.append(("Anfitrião Superhost", "ok" if superhost else "par"))
    if status == "OK" and q < 15:
        status = "AJUSTE"
    return dict(itens=itens, status=status, nota=v, qtd=q)


def montar_analise(dados: dict) -> dict:
    """Monta a estrutura completa do relatório a partir dos dados coletados."""
    titulo = dados.get("titulo", "")
    fotos_qtd = len(dados.get("fotos", []))

    b_titulo = analisar_titulo(titulo)
    b_fotos = analisar_fotos(fotos_qtd)
    b_social = analisar_prova_social(dados.get("nota"), dados.get("avaliacoes"),
                                     dados.get("superhost", False))

    blocos = [
        dict(cod="1", nome="Título do anúncio", status=b_titulo["status"], itens=b_titulo["itens"],
             leitura=("O título é a primeira coisa que o hóspede lê na busca. Ele precisa dizer, "
                      "em poucas palavras, o melhor motivo para clicar no seu anúncio: a praia perto, "
                      "a piscina, a vista. Evite abreviações e palavras genéricas, porque elas não "
                      "convencem ninguém a clicar.")),
        dict(cod="2", nome="Fotos", status=b_fotos["status"], itens=b_fotos["itens"],
             leitura=("As fotos são o que mais decide a reserva. O ideal é ter de 20 a 40 imagens "
                      "boas, com a melhor delas na capa. A qualidade de cada foto e as legendas só "
                      "conseguimos avaliar em detalhe na análise completa, feita por especialista.")),
        dict(cod="3", nome="Confiança (nota e avaliações)", status=b_social["status"], itens=b_social["itens"],
             leitura=("A nota e as avaliações são a prova de que a experiência é boa. Nota de 4,8 "
                      "para cima mantém o padrão Superhost. A partir de 4,9, o anúncio disputa o selo "
                      "Preferido dos Hóspedes, que dá destaque na busca.")),
        dict(cod="4", nome="Estrutura anunciada", status="OK", itens=[
            (" · ".join(x for x in [dados.get("tipo"), dados.get("quartos"),
                                    dados.get("camas"), dados.get("banheiros")] if x) or "Estrutura não identificada", "ok"),
            (f"Localização: {dados.get('local') or 'não identificada'}", "ok" if dados.get("local") else "par"),
        ],
            leitura=("Confira se o tipo de imóvel, os quartos, as camas e os banheiros estão exatamente "
                     "como o imóvel é de verdade. Informação errada aqui gera avaliação ruim depois.")),
        dict(cod="5", nome="O que só dá para conferir com acesso à conta", status="PENDENTE", itens=[
            ("Descrição completa, legendas das fotos e preenchimento de todos os campos", "pend"),
            ("Preço em relação aos concorrentes da região", "pend"),
            ("Política de cancelamento, regras da casa e horários", "pend"),
            ("Velocidade de resposta, calendário e configurações de reserva", "pend"),
        ],
            leitura=("Uma parte importante do anúncio não aparece na página pública. No Raio-X completo, "
                     "um especialista da 33hosts analisa o anúncio inteiro em 18 blocos, com plano de "
                     "ação pronto para aplicar.")),
    ]

    cont = {"OK": 0, "AJUSTE": 0, "CRITICO": 0, "PEND": 0}
    for b in blocos:
        cont["PEND" if b["status"] in ("PENDENTE", "PARCIAL") else b["status"]] += 1

    resumo = _resumo(dados, b_titulo, b_fotos, b_social, fotos_qtd)
    recomendacoes = _recomendacoes(b_titulo, b_fotos, b_social)

    return dict(dados=dados, blocos=blocos, placar=cont, resumo=resumo,
                recomendacoes=recomendacoes)


def _resumo(dados, b_titulo, b_fotos, b_social, fotos_qtd):
    partes = []
    nome = dados.get("titulo") or "Seu anúncio"
    nota = b_social.get("nota")
    qtd = b_social.get("qtd", 0)

    if nota and nota >= 4.8 and qtd >= 15:
        partes.append(f"Seu anúncio tem uma base muito boa: nota {dados.get('nota')} com "
                      f"{qtd} avaliações. Isso é um patrimônio que poucos concorrentes têm.")
    elif nota:
        partes.append(f"Seu anúncio tem nota {dados.get('nota')} com {qtd} avaliações. "
                      "Há espaço para fortalecer essa base de confiança.")
    else:
        partes.append("Não conseguimos ler a nota do anúncio na página pública.")

    if b_titulo["status"] != "OK":
        partes.append("O ponto que mais segura o seu resultado hoje é o título: ele não está "
                      "vendendo o seu imóvel. A boa notícia é que corrigir isso leva minutos.")
    if fotos_qtd < 20:
        partes.append(f"O anúncio tem só {fotos_qtd} fotos. Anúncios com 30 ou mais fotos boas "
                      "aparecem mais e convertem mais.")
    elif b_titulo["status"] == "OK":
        partes.append("Os pontos verificáveis por fora estão bem encaminhados. Os detalhes finos "
                      "aparecem na análise completa.")

    partes.append("Esta é uma análise automática dos itens visíveis na página pública do seu anúncio. "
                  "O Raio-X completo da 33hosts analisa 18 blocos, incluindo fotos uma a uma, textos, "
                  "preço e configurações, e entrega um plano de ação pronto.")
    return "\n\n".join(partes)


def _recomendacoes(b_titulo, b_fotos, b_social):
    recs = []
    if b_titulo["status"] != "OK":
        recs.append("Reescreva o título colocando o ponto forte primeiro. Exemplo de fórmula: "
                    "ponto forte + localização. Sem abreviações e sem palavras genéricas.")
    if b_fotos["status"] != "OK":
        recs.append("Aumente a galeria para 20 a 40 fotos boas: capa impactante, todos os ambientes, "
                    "a praia ou área externa e os detalhes que geram desejo.")
    if b_social.get("qtd", 0) < 15:
        recs.append("Peça avaliação a cada hóspede depois da estadia. Volume de avaliações protege "
                    "sua nota e aumenta a confiança de quem está escolhendo.")
    recs.append("Preencha todos os campos do anúncio, incluindo legendas das fotos, bairro e como "
                "chegar. Campo vazio faz o anúncio aparecer menos.")
    recs.append("Quer o diagnóstico completo, com as correções já escritas para colar no anúncio? "
                "Fale com a 33hosts e peça o Raio-X completo.")
    return recs


# ------------------------- Camada 2 (opcional, com IA) -------------------------
def enriquecer_com_ia(analise: dict) -> dict:
    """Se houver ANTHROPIC_API_KEY, melhora leituras e sugere título com IA."""
    chave = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not chave:
        return analise
    try:
        import anthropic
        cliente = anthropic.Anthropic(api_key=chave)
        d = analise["dados"]
        prompt = (
            "Você é analista de anúncios de temporada da 33hosts. Linguagem simples e direta, "
            "para o dono do imóvel. Não use travessões. Dados do anúncio:\n"
            f"Título: {d.get('titulo')}\nTipo: {d.get('tipo')}\nLocal: {d.get('local')}\n"
            f"Nota: {d.get('nota')} com {d.get('avaliacoes')} avaliações. "
            f"Superhost: {'sim' if d.get('superhost') else 'não'}. Fotos: {len(d.get('fotos', []))}.\n"
            f"Estrutura: {d.get('quartos')}, {d.get('camas')}, {d.get('banheiros')}.\n\n"
            "Escreva em JSON com as chaves: resumo (2 parágrafos curtos sobre a situação do anúncio) "
            "e titulos (lista com 3 opções de título de até 50 caracteres, ponto forte primeiro, "
            "sem abreviações e sem palavras genéricas)."
        )
        resp = cliente.messages.create(
            model=os.environ.get("MODELO_IA", "claude-sonnet-4-5"),
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        texto = resp.content[0].text
        m = re.search(r"\{.*\}", texto, re.S)
        if m:
            extra = json.loads(m.group(0))
            if extra.get("resumo"):
                analise["resumo"] = extra["resumo"] + ("\n\nEsta análise foi gerada automaticamente. "
                                                       "O Raio-X completo da 33hosts analisa 18 blocos e "
                                                       "entrega plano de ação pronto.")
            if extra.get("titulos"):
                analise["titulos_ia"] = extra["titulos"][:3]
    except Exception:
        pass
    return analise
