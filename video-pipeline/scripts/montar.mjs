#!/usr/bin/env node
/**
 * Etapa 2 — Monta um projeto HyperFrames a partir de:
 *   - o vídeo bruto (já sem silêncios, se usou a etapa 0)
 *   - a transcrição palavra a palavra (etapa 1)
 *   - a PAUTA (pauta.json): estilo de legenda, correções, destaques, cartões e zooms.
 *
 * Uso:
 *   node scripts/montar.mjs --video bruto.mp4 --transcricao t.json --pauta pauta.json --saida projeto/
 *
 * A pauta é escrita pelo Claude Code (skill /editar-video) ou à mão. Veja exemplos/pauta-imovel.json.
 */
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { parseArgs } from "node:util";

const { values: arg } = parseArgs({
  options: {
    video: { type: "string" },
    transcricao: { type: "string" },
    pauta: { type: "string" },
    saida: { type: "string" },
  },
});
for (const k of ["video", "transcricao", "pauta", "saida"]) {
  if (!arg[k]) {
    console.error(`Faltou --${k}`);
    process.exit(1);
  }
}

const W = 1080;
const H = 1920;
const pauta = JSON.parse(fs.readFileSync(arg.pauta, "utf8"));
const palavrasBrutas = JSON.parse(fs.readFileSync(arg.transcricao, "utf8"));

const DUR = Number(
  execFileSync("ffprobe", [
    "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", arg.video,
  ]).toString().trim(),
);
const dur = (x) => Math.round(x * 1000) / 1000;
// Segura o último quadro por alguns segundos para a chamada final ser lida (padrão 1 s).
const SEGURA = pauta.segurarFinal ?? 1.0;
const TOTAL = dur(DUR + SEGURA);

// ---------- Marca e estilo ----------
const marca = {
  cor: "#FFD400", // cor de destaque
  texto: "#FFFFFF",
  fundo: "rgba(12,12,16,.78)",
  fonte: "Montserrat",
  ...(pauta.marca || {}),
};
const estilo = pauta.legenda?.estilo || "dinamico"; // dinamico | limpo | nenhuma
const maxPalavras = pauta.legenda?.palavrasPorBloco || (estilo === "limpo" ? 5 : 3);
const baseLegenda = pauta.legenda?.baseY ?? 1220; // borda de baixo da legenda (px do topo); 1248 é o limite seguro do Reels/TikTok/Shorts

// ---------- Palavras: correções + destaques ----------
const correcoes = pauta.correcoes || {};
const norm = (s) =>
  s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^\p{L}\p{N}]/gu, "");
const destaques = new Set((pauta.destaques || []).map(norm));

const palavras = palavrasBrutas.map((w) => {
  let text = w.text;
  const semPont = text.replace(/[.,!?;:]+$/u, "");
  const pont = text.slice(semPont.length);
  if (correcoes[semPont] !== undefined) text = correcoes[semPont] + pont;
  else if (correcoes[text] !== undefined) text = correcoes[text];
  return { ...w, text, destaque: destaques.has(norm(text)) || /\d/.test(text) && pauta.destacarNumeros !== false };
});

// ---------- Agrupamento das legendas ----------
function agrupar(ws) {
  const grupos = [];
  let atual = [];
  for (let i = 0; i < ws.length; i++) {
    const w = ws[i];
    atual.push(w);
    const prox = ws[i + 1];
    const fimFrase = /[.!?…]$/.test(w.text);
    const virgula = /[,;:]$/.test(w.text);
    const pausa = prox ? prox.start - w.end >= 0.15 : true;
    if (!prox || fimFrase || pausa || atual.length >= maxPalavras || (virgula && atual.length >= 2)) {
      grupos.push(atual);
      atual = [];
    }
  }
  return grupos.map((g, i) => {
    const ini = Math.max(0.1, g[0].start - 0.05);
    return { i, palavras: g, ini, fim: g[g.length - 1].end + 0.12 };
  }).map((g, i, arr) => {
    const prox = arr[i + 1];
    const fim = Math.min(prox ? prox.ini : DUR - 0.05, Math.max(g.fim, g.ini + 0.35));
    return { ...g, fim };
  });
}

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const fmtLegenda = (t) => (estilo === "dinamico" ? t.replace(/[.,;:]+$/u, "") : t);

// ---------- Projeto ----------
const out = path.resolve(arg.saida);
fs.mkdirSync(path.join(out, "assets"), { recursive: true });
fs.mkdirSync(path.join(out, "compositions"), { recursive: true });
// Copia o vídeo já preparado para o HyperFrames: keyframe a cada 1 s (evita
// travar na busca) e o último quadro congelado pelo tempo de SEGURA.
execFileSync("ffmpeg", [
  "-v", "error", "-y", "-i", arg.video,
  "-vf", `tpad=stop_mode=clone:stop_duration=${SEGURA}`, "-af", `apad=pad_dur=${SEGURA}`,
  "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-g", "30",
  "-c:a", "aac", "-b:a", "192k", "-t", String(TOTAL),
  path.join(out, "assets", "bruto.mp4"),
]);
fs.writeFileSync(path.join(out, "assets", "transcript.json"), JSON.stringify(palavras, null, 1));

const GSAP = '<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>';
const hosts = [];

// ---------- Legendas ----------
if (estilo !== "nenhuma") {
  const grupos = agrupar(palavras);
  const css = estilo === "dinamico"
    ? `
    .cap { position:absolute; left:0; right:0; text-align:center; padding:0 90px; opacity:0;
           font-family:'${marca.fonte}', sans-serif; font-weight:900; text-transform:uppercase;
           line-height:1.05; letter-spacing:-0.01em; color:${marca.texto};
           text-shadow: 0 6px 0 rgba(0,0,0,.85), 0 0 24px rgba(0,0,0,.55);
           -webkit-text-stroke: 3px #000; paint-order: stroke fill; }
    .cap .w { display:inline-block; margin:0 .2em; }
    .cap .w.d { margin:0 .3em; transform-origin:50% 90%; }
    .cap .w.d { color:${marca.cor}; }`
    : `
    .cap { position:absolute; left:0; right:0; text-align:center; padding:0 110px; opacity:0;
           font-family:'${marca.fonte}', sans-serif; font-weight:700; line-height:1.18; color:#fff; }
    .cap .box { display:inline; background:rgba(0,0,0,.42); padding:.08em .32em; border-radius:14px;
           box-decoration-break:clone; -webkit-box-decoration-break:clone; }
    .cap .w { display:inline-block; margin:0 .08em; }
    .cap .w.d { color:${marca.cor}; }`;

  const html = grupos.map((g) => {
    const ws = g.palavras.map((w) =>
      `<span class="w${w.destaque ? " d" : ""}" id="cw-${w.id}">${esc(fmtLegenda(w.text))}</span>`).join(" ");
    const inner = estilo === "limpo" ? `<span class="box">${ws}</span>` : ws;
    return `    <div class="cap" id="cg-${g.i}">${inner}</div>`;
  }).join("\n");

  const tl = grupos.map((g) => {
    const linhas = [];
    const pop = estilo === "dinamico";
    linhas.push(`tl.set("#cg-${g.i}", { visibility: "visible" }, ${dur(g.ini)});`);
    linhas.push(pop
      ? `tl.fromTo("#cg-${g.i}", { opacity: 0, scale: 0.86, y: 18 }, { opacity: 1, scale: 1, y: 0, duration: 0.14, ease: "back.out(2.2)" }, ${dur(g.ini)});`
      : `tl.fromTo("#cg-${g.i}", { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.18, ease: "power2.out" }, ${dur(g.ini)});`);
    if (pop) {
      for (const w of g.palavras) {
        if (w.destaque) {
          linhas.push(`tl.fromTo("#cw-${w.id}", { scale: 1 }, { scale: 1.16, duration: 0.12, ease: "power2.out" }, ${dur(w.start)});`);
        }
      }
    }
    linhas.push(`tl.to("#cg-${g.i}", { opacity: 0, duration: 0.1, ease: "power2.in" }, ${dur(g.fim - 0.1)});`);
    linhas.push(`tl.set("#cg-${g.i}", { opacity: 0, visibility: "hidden" }, ${dur(g.fim)});`);
    return "    " + linhas.join("\n    ");
  }).join("\n");

  fs.writeFileSync(path.join(out, "compositions", "legendas.html"), `<template>
  <style>
    #root { position:absolute; inset:0; background:transparent; }
${css}
  </style>
  <div id="root" data-composition-id="legendas" data-width="${W}" data-height="${H}">
${html}
  </div>
  <script>
    // Ajusta cada bloco à largura (mesma regra do HyperFrames: base 84, mínimo 48).
    const hf = window.__hyperframes;
    document.querySelectorAll("#root .cap").forEach((el) => {
      const texto = el.textContent.trim();
      let size = ${estilo === "dinamico" ? 84 : 58};
      if (hf && hf.fitTextFontSize) {
        size = hf.fitTextFontSize(texto, { fontFamily: "${marca.fonte}", fontWeight: ${estilo === "dinamico" ? 900 : 700}, maxWidth: ${estilo === "dinamico" ? 780 : 820}, baseFontSize: ${estilo === "dinamico" ? 84 : 58}, minFontSize: 44 }).fontSize;
      }
      el.style.fontSize = size + "px";
      el.style.bottom = "${H - baseLegenda}px";
      el.style.visibility = "hidden";
    });
    const tl = gsap.timeline({ paused: true });
${tl}
    window.__timelines["legendas"] = tl;
  </script>
</template>
`);
  hosts.push(`      <div id="legendas" data-composition-id="legendas" data-composition-src="compositions/legendas.html"
        data-start="0" data-duration="${TOTAL}" data-track-index="2" data-track-kind="captions"
        data-width="${W}" data-height="${H}" style="z-index:20"></div>`);
}

// ---------- Cartões ----------
const CARD_CSS = `
    #root { position:absolute; inset:0; background:transparent; font-family:'${marca.fonte}', sans-serif; }
    .glass { position:absolute; left:110px; right:110px; top:300px; padding:30px 40px; border-radius:36px;
             background:${marca.fundo}; box-shadow:0 20px 60px rgba(0,0,0,.35); color:#fff; overflow:visible; }
    .rot { font-size:34px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; opacity:.8; }
    .acc { color:${marca.cor}; }`;

function cartao(c, idx) {
  const id = `c${idx}`;
  const len = dur(c.fim - c.inicio);
  const saida = dur(Math.max(0.5, len - 0.4));
  let corpo = "";
  let anim = "";
  switch (c.tipo) {
    case "numero": // número grande: "120 m²"
      corpo = `
    <div class="glass" id="${id}-box" style="text-align:center">
      <div id="${id}-val" style="font-size:150px;font-weight:900;line-height:1;letter-spacing:-.03em" class="acc">${esc(c.valor)}</div>
      <div id="${id}-rot" class="rot" style="margin-top:14px">${esc(c.rotulo || "")}</div>
    </div>`;
      anim = `
    tl.fromTo("#${id}-box", { opacity: 0, y: -40 }, { opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }, 0);
    tl.fromTo("#${id}-val", { scale: 0.6 }, { scale: 1, duration: 0.5, ease: "back.out(2)" }, 0.08);
    tl.fromTo("#${id}-rot", { opacity: 0, y: 14 }, { opacity: 0.8, y: 0, duration: 0.3, ease: "power2.out" }, 0.3);`;
      break;
    case "ficha": // ficha do imóvel: título + itens (número, rótulo)
      corpo = `
    <div class="glass" id="${id}-box">
      <div id="${id}-tit" style="font-size:58px;font-weight:900;line-height:1.05">${esc(c.titulo || "")}</div>
      ${c.subtitulo ? `<div class="rot" id="${id}-sub" style="margin-top:6px">${esc(c.subtitulo)}</div>` : ""}
      <div style="display:flex;gap:18px;margin-top:24px">
        ${(c.itens || []).map(([n, r], k) => `<div id="${id}-i${k}" style="flex:1;background:rgba(255,255,255,.08);border-radius:22px;padding:16px 10px;text-align:center">
          <div class="acc" style="font-size:66px;font-weight:900;line-height:1">${esc(n)}</div>
          <div style="font-size:28px;font-weight:700;margin-top:6px;opacity:.85">${esc(r)}</div></div>`).join("\n        ")}
      </div>
    </div>`;
      anim = `
    tl.fromTo("#${id}-box", { opacity: 0, y: -40 }, { opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }, 0);
    ${(c.itens || []).map((_, k) => `tl.fromTo("#${id}-i${k}", { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.3, ease: "power2.out" }, ${dur(0.25 + k * 0.12)});`).join("\n    ")}`;
      break;
    case "preco":
      corpo = `
    <div class="glass" id="${id}-box" style="text-align:center;background:${marca.cor};color:#111">
      <div class="rot" id="${id}-rot" style="opacity:.75">${esc(c.rotulo || "Valor")}</div>
      <div id="${id}-val" style="font-size:132px;font-weight:900;line-height:1.05;letter-spacing:-.03em">${esc(c.valor)}</div>
    </div>`;
      anim = `
    tl.fromTo("#${id}-box", { opacity: 0, scale: 0.8, rotation: -3 }, { opacity: 1, scale: 1, rotation: 0, duration: 0.45, ease: "back.out(2.4)" }, 0);
    tl.fromTo("#${id}-val", { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.35, ease: "power3.out" }, 0.15);`;
      break;
    case "titulo": // capítulo / explicador
      corpo = `
    <div class="glass" id="${id}-box">
      ${c.rotulo ? `<div class="rot acc" id="${id}-rot">${esc(c.rotulo)}</div>` : ""}
      <div id="${id}-tit" style="font-size:72px;font-weight:900;line-height:1.05;margin-top:6px">${esc(c.titulo)}</div>
    </div>`;
      anim = `
    tl.fromTo("#${id}-box", { opacity: 0, x: -60 }, { opacity: 1, x: 0, duration: 0.4, ease: "power3.out" }, 0);
    tl.fromTo("#${id}-tit", { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.35, ease: "power2.out" }, 0.12);`;
      break;
    case "cta":
      corpo = `
    <div class="glass" id="${id}-box" style="text-align:center">
      <div id="${id}-pre" style="font-size:52px;font-weight:700">${esc(c.texto || "Comenta")}</div>
      <div id="${id}-pal" class="acc" style="font-size:130px;font-weight:900;line-height:1.05;letter-spacing:-.02em">“${esc(c.palavra)}”</div>
      ${c.rodape ? `<div class="rot" id="${id}-rod" style="margin-top:8px">${esc(c.rodape)}</div>` : ""}
    </div>`;
      anim = `
    tl.fromTo("#${id}-box", { opacity: 0, y: -40 }, { opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }, 0);
    tl.fromTo("#${id}-pal", { scale: 0.5 }, { scale: 1, duration: 0.5, ease: "back.out(2.6)" }, 0.12);
    tl.to("#${id}-pal", { scale: 1.08, duration: 0.35, ease: "sine.inOut", yoyo: true, repeat: 3 }, 0.8);`;
      break;
    default:
      throw new Error(`Tipo de cartão desconhecido: ${c.tipo}`);
  }
  anim += `
    tl.to("#${id}-box", { opacity: 0, y: -24, duration: 0.3, ease: "power2.in" }, ${saida});`;

  fs.writeFileSync(path.join(out, "compositions", `${id}.html`), `<template>
  <style>${CARD_CSS}
  </style>
  <div id="root" data-composition-id="${id}" data-width="${W}" data-height="${H}">${corpo}
  </div>
  <script>
    const tl = gsap.timeline({ paused: true });${anim}
    window.__timelines["${id}"] = tl;
  </script>
</template>
`);
  hosts.push(`      <div id="${id}" data-composition-id="${id}" data-composition-src="compositions/${id}.html"
        data-start="${dur(c.inicio)}" data-duration="${len}" data-track-index="1" data-track-kind="graphics"
        data-width="${W}" data-height="${H}" style="z-index:10"></div>`);
}

const cartoes = (pauta.cartoes || []).map((c) => ({
  ...c,
  inicio: Math.max(0, Math.min(c.inicio, DUR - 0.5)),
  fim: Math.min(c.fim, TOTAL),
}));
cartoes.forEach((c, i) => cartao(c, i + 1));

// ---------- Zooms (punch-in) na câmera ----------
const zooms = (pauta.zooms || []).map((z) =>
  `      tl.to("#camera", { scale: ${z.escala || 1.12}, duration: ${z.suave ? 0.6 : 0.12}, ease: "power2.out" }, ${dur(z.inicio)});
      tl.to("#camera", { scale: 1, duration: ${z.suave ? 0.6 : 0.12}, ease: "power2.inOut" }, ${dur(Math.min(z.fim, DUR) - (z.suave ? 0.6 : 0.12))});`,
).join("\n");

fs.writeFileSync(path.join(out, "index.html"), `<!doctype html>
<html lang="pt-BR" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=${W}, height=${H}" />
    ${GSAP}
    <style>
      * { margin:0; padding:0; box-sizing:border-box; }
      html, body { width:${W}px; height:${H}px; overflow:hidden; background:#000; }
      #camera { position:absolute; left:0; top:0; width:${W}px; height:${H}px; transform-origin:50% 42%; }
      #bruto { position:absolute; left:0; top:0; width:${W}px; height:${H}px; object-fit:cover; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="${TOTAL}" data-width="${W}" data-height="${H}">
      <div id="camera">
        <video id="bruto" class="clip" src="assets/bruto.mp4" data-start="0" data-duration="${TOTAL}"
          data-track-index="0" data-has-audio="true" playsinline></video>
      </div>
${hosts.join("\n")}
    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
${zooms}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
`);

fs.writeFileSync(path.join(out, "package.json"), JSON.stringify({
  name: "video-editado", private: true, type: "module",
  scripts: { dev: "hyperframes preview", check: "hyperframes check", render: "hyperframes render" },
}, null, 2));

console.log(JSON.stringify({
  ok: true, projeto: out, duracao: DUR, legendas: estilo, cartoes: cartoes.length, zooms: (pauta.zooms || []).length,
}));
