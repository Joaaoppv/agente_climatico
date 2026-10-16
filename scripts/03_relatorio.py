import argparse
import base64
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import markdown
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

# Caminhos e configurações do ambiente
AGY = Path.home() / "AppData/Local/agy/bin/agy.exe"
MODELO = "gemini-3.8-flash-low"

PASTA_ATUAL = Path(__file__).resolve().parent
PASTA_RAIZ = PASTA_ATUAL.parent if PASTA_ATUAL.name in ("runs", "scripts") else PASTA_ATUAL

ARQUIVO_DADOS_CSV = PASTA_RAIZ / "output" / "01_coleta" / "dados_clima.csv"
ARQUIVO_ESTATISTICAS = PASTA_RAIZ / "output" / "02_analise" / "analise_estatistica.json"
ARQUIVO_PROMPT = PASTA_RAIZ / "prompts" / "03_prompt_relatorio.md"

PASTA_OUTPUT   = PASTA_RAIZ / "output" / "03_relatorio"
PASTA_GRAFICOS = PASTA_OUTPUT / "graficos"
PASTA_WORD     = PASTA_OUTPUT / "word"
PASTA_HTML     = PASTA_OUTPUT / "html"
PASTA_MD       = PASTA_OUTPUT / "markdown"
PASTA_PLANOS   = PASTA_OUTPUT / "planos"
PASTA_RUNS     = PASTA_RAIZ / "runs"

ARQUIVO_SAIDA_PLANO = PASTA_PLANOS / "plano_editorial.json"
ARQUIVO_SAIDA_MD    = PASTA_MD     / "relatorio_climatico.md"
ARQUIVO_SAIDA_HTML  = PASTA_HTML   / "relatorio_climatico.html"
ARQUIVO_SAIDA_DOCX  = PASTA_WORD   / "relatorio_climatico.docx"

PASTA_OUTPUT.mkdir(parents=True, exist_ok=True)
PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)
PASTA_WORD.mkdir(parents=True, exist_ok=True)
PASTA_HTML.mkdir(parents=True, exist_ok=True)
PASTA_MD.mkdir(parents=True, exist_ok=True)
PASTA_PLANOS.mkdir(parents=True, exist_ok=True)
PASTA_RUNS.mkdir(parents=True, exist_ok=True)


def consultar_modelo(texto_prompt):
    """Consulta o modelo Gemini via Antigravity CLI."""
    if not AGY.exists():
        raise FileNotFoundError(f"Executável Antigravity CLI não encontrado em: {AGY}")

    resposta = subprocess.run(
        [str(AGY), "-p", texto_prompt, "--model", MODELO],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=240
    )

    if resposta.returncode != 0:
        erro = resposta.stderr.strip() or f"Código de saída: {resposta.returncode}"
        raise RuntimeError(f"Erro na execução da CLI do modelo: {erro}")

    return resposta.stdout.strip()


def sanitizar_texto_latex(texto):
    """Substitui resíduos de LaTeX por tipografia Unicode limpa para o Word e texto puro."""
    if not texto:
        return ""
    t = texto

    # Substituições de notações meteorológicas e matemáticas frequentes
    substituicoes = [
        (r"\\,?\^\\circ\\text\{C\}", "°C"),
        (r"\\circ\\text\{C\}", "°C"),
        (r"\\circ C", "°C"),
        (r"\\bar\{x\}", "x̄"),
        (r"\\tilde\{x\}", "Mediana"),
        (r"\\mu", "μ"),
        (r"\\sigma\^2", "s²"),
        (r"\\sigma", "s"),
        (r"\\rho_s", "rho"),
        (r"\\rho", "r"),
        (r"\\beta_1", "β"),
        (r"\\beta_0", "α"),
        (r"\\beta", "β"),
        (r"\\alpha", "α"),
        (r"\\times", "×"),
        (r"\\le", "≤"),
        (r"\\ge", "≥"),
        (r"\\ne", "≠"),
        (r"\\approx", "≈"),
        (r"\\pm", "±"),
        (r"\\sim", "~"),
        (r"\\in", "∈"),
        (r"\\sum", "Soma"),
        (r"\\mathcal\{N\}", "Normal"),
        (r"\\text\{([^}]*)\}", r"\1"),
        (r"\\frac\{([^}]*)\}\{([^}]*)\}", r"(\1) / (\2)")
    ]

    for padrao, subst in substituicoes:
        t = re.sub(padrao, subst, t)

    # Remove cifrões de delimitador LaTeX ($ ... $ ou $$ ... $$)
    t = re.sub(r"\$\$([^\$]+)\$\$", r"\1", t)
    t = re.sub(r"\$([^\$]+)\$", r"\1", t)

    # Limpeza de barras invertidas residuais órfãs
    t = t.replace("\\", "")
    return t


def extrair_resposta_dupla(resposta_modelo):
    """Extrai o JSON do plano editorial e o Markdown do relatório."""
    plano_editorial = None
    match_json = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", resposta_modelo)
    if match_json:
        try:
            plano_editorial = json.loads(match_json.group(1))
        except json.JSONDecodeError:
            pass

    if not plano_editorial:
        matches = re.findall(r"\{[\s\S]*?\}", resposta_modelo)
        for cand in reversed(matches):
            try:
                dados = json.loads(cand)
                if "figuras_encomendadas" in dados:
                    plano_editorial = dados
                    break
            except json.JSONDecodeError:
                continue

    if not plano_editorial:
        plano_editorial = {
            "titulo_relatorio": "Relatório Técnico-Científico de Estatística Aplicada ao Clima",
            "figuras_encomendadas": []
        }

    match_md = re.search(r"```(?:markdown|md)\s*([\s\S]*?)\s*```", resposta_modelo)
    if match_md:
        texto_md = match_md.group(1).strip()
    else:
        texto_limpo = re.sub(r"```(?:json)?\s*\{[\s\S]*?\}\s*```", "", resposta_modelo).strip()
        texto_md = texto_limpo

    return plano_editorial, texto_md


# ==============================================================================
# TOOLBOX DE FERRAMENTAS GRÁFICAS DISPONÍVEIS PARA O AGENTE
# ==============================================================================

def configurar_estilo():
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
    plt.rcParams["axes.edgecolor"] = "#cbd5e1"
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["grid.color"] = "#e2e8f0"
    plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["grid.alpha"] = 0.7


def render_distribuicao(df, params, titulo, caminho_saida):
    """Ferramenta Gráfica: Histograma e Boxplot acoplados de 1 ou 2 variáveis."""
    configurar_estilo()
    var1 = params.get("variavel_1") or params.get("variavel")
    var2 = params.get("variavel_2")

    cols = [c for c in [var1, var2] if c and c in df.columns]
    if not cols:
        return None

    n_cols = len(cols)
    fig, axes = plt.subplots(2, n_cols, figsize=(6 * n_cols, 7), dpi=200, gridspec_kw={"height_ratios": [2.5, 1]})

    if n_cols == 1:
        axes = np.array([[axes[0]], [axes[1]]])

    cores = ["#3b82f6", "#0ea5e9"]

    for idx, col in enumerate(cols):
        serie = df[col].dropna()
        media, med = serie.mean(), serie.median()

        ax_hist = axes[0, idx]
        ax_hist.hist(serie, bins=7, color=cores[idx % len(cores)], alpha=0.65, edgecolor="#1e3a8a", density=True)
        ax_hist.axvline(media, color="#dc2626", linewidth=2, label=f"Média: {media:.2f}")
        ax_hist.axvline(med, color="#16a34a", linewidth=2, linestyle="--", label=f"Mediana: {med:.2f}")
        ax_hist.set_title(f"Distribuição: {col}", fontsize=11, fontweight="bold")
        ax_hist.set_ylabel("Densidade")
        ax_hist.legend(frameon=True, facecolor="#f8fafc", fontsize=9)
        ax_hist.grid(True)

        ax_box = axes[1, idx]
        ax_box.boxplot(serie, vert=False, patch_artist=True,
                       boxprops=dict(facecolor="#93c5fd", color="#1e3a8a"),
                       medianprops=dict(color="#16a34a", linewidth=2), widths=0.55)
        ax_box.set_xlabel(col)
        ax_box.set_yticks([])
        ax_box.grid(True)

    plt.suptitle(titulo or "Análise Comparativa de Distribuição", fontsize=12, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(caminho_saida, bbox_inches="tight")
    plt.close()
    return caminho_saida


def render_dispersao(df, params, titulo, caminho_saida):
    """Ferramenta Gráfica: Scatter Plot com reta de regressão linear OLS."""
    configurar_estilo()
    vx = params.get("var_x")
    vy = params.get("var_y")

    if not (vx in df.columns and vy in df.columns):
        return None

    sub = df[[vx, vy]].dropna()
    x = sub[vx].to_numpy()
    y = sub[vy].to_numpy()

    r, p = stats.pearsonr(x, y)
    slope, intercept = np.polyfit(x, y, 1)

    fig, ax = plt.subplots(figsize=(7.5, 5.5), dpi=200)
    ax.scatter(x, y, color="#ea580c", s=70, edgecolor="#7c2d12", alpha=0.85, zorder=3)
    x_grid = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_grid, slope * x_grid + intercept, color="#c2410c", linewidth=2, linestyle="--",
            label=f"Reta OLS (r = {r:.4f}, p = {p:.4f})")

    ax.set_title(titulo or f"Diagrama de Dispersão: {vx} vs. {vy}", fontsize=11, fontweight="bold")
    ax.set_xlabel(vx)
    ax.set_ylabel(vy)
    ax.legend(frameon=True, facecolor="#f8fafc")
    ax.grid(True)

    plt.tight_layout()
    plt.savefig(caminho_saida, bbox_inches="tight")
    plt.close()
    return caminho_saida


def render_matriz_correlacao(df, params, titulo, caminho_saida):
    """Ferramenta Gráfica: Heatmap de correlação de Pearson."""
    configurar_estilo()
    lista_vars = params.get("lista_variaveis", [])
    cols = [c for c in lista_vars if c in df.columns]

    if len(cols) < 2:
        cols = df.select_dtypes(include=[np.number]).columns[:6].tolist()

    sub = df[cols].dropna()
    matriz = sub.corr(method="pearson").to_numpy()

    fig, ax = plt.subplots(figsize=(8, 6.5), dpi=200)
    cax = ax.imshow(matriz, cmap="coolwarm", vmin=-1, vmax=1)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=35, ha="right", fontsize=9)
    ax.set_yticklabels(cols, fontsize=9)

    for i in range(len(cols)):
        for j in range(len(cols)):
            val = matriz[i, j]
            cor = "white" if abs(val) > 0.55 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=cor, fontsize=9, fontweight="bold")

    ax.set_title(titulo or "Matriz de Correlação Linear de Pearson", fontsize=11, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(caminho_saida, bbox_inches="tight")
    plt.close()
    return caminho_saida


def render_serie_temporal(df, params, titulo, caminho_saida):
    """Ferramenta Gráfica: Série temporal com teste de tendência OLS."""
    configurar_estilo()
    var = params.get("variavel") or params.get("var_y")
    if not (var and var in df.columns):
        return None

    sub = df[["data", var]].dropna().copy()
    dias = np.arange(len(sub))
    y = sub[var].to_numpy()

    reg = stats.linregress(dias, y)

    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=200)
    ax.plot(dias, y, marker="o", color="#2563eb", linewidth=1.8, label=f"Série {var}")
    ax.plot(dias, reg.slope * dias + reg.intercept, color="#dc2626", linestyle="--", linewidth=2,
            label=f"Reta de Tendência (β = {reg.slope:.4f}/dia, R² = {reg.rvalue**2:.4f}, p = {reg.pvalue:.4f})")

    datas = pd.to_datetime(sub["data"]).dt.strftime("%d/%m") if "data" in sub.columns else [f"D{i+1}" for i in dias]
    ax.set_xticks(dias[::2])
    ax.set_xticklabels(datas[::2], rotation=30)
    ax.set_title(titulo or f"Série Temporal de {var}", fontsize=11, fontweight="bold")
    ax.set_ylabel(var)
    ax.legend(frameon=True, facecolor="#f8fafc")
    ax.grid(True)

    plt.tight_layout()
    plt.savefig(caminho_saida, bbox_inches="tight")
    plt.close()
    return caminho_saida


def despachar_geracao_figura(df, config_figura, indice, pasta_graficos):
    """Despacha a ferramenta gráfica Python com base na decisão do agente."""
    tipo = config_figura.get("tipo_ferramenta", "").lower()
    params = config_figura.get("parametros", {})
    titulo = config_figura.get("titulo_grafico", "")
    nome_arquivo = f"figura_{indice}_{tipo}.png"
    caminho = pasta_graficos / nome_arquivo

    if tipo == "distribuicao":
        return render_distribuicao(df, params, titulo, caminho)
    elif tipo == "dispersao":
        return render_dispersao(df, params, titulo, caminho)
    elif tipo == "matriz_correlacao":
        return render_matriz_correlacao(df, params, titulo, caminho)
    elif tipo == "serie_temporal":
        return render_serie_temporal(df, params, titulo, caminho)
    else:
        return None


# ==============================================================================
# EXPORTAÇÃO PARA HTML EXECUTIVO E WORD (ABNT)
# ==============================================================================

def converter_imagem_base64(caminho_imagem):
    bytes_img = Path(caminho_imagem).read_bytes()
    b64_str = base64.b64encode(bytes_img).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


def gerar_relatorio_html(texto_markdown, figuras_geradas, caminho_html_saida, titulo_relatorio):
    """Gera um arquivo HTML executivo com as figuras decididas pela IA embutidas."""
    texto_limpo = sanitizar_texto_latex(texto_markdown)
    conteudo_html_corpo = markdown.markdown(texto_limpo, extensions=["tables", "fenced_code"])

    cards_figuras = []
    for fig in figuras_geradas:
        if Path(fig["caminho"]).exists():
            legenda_limpa = sanitizar_texto_latex(fig.get("legenda", ""))
            cards_figuras.append(f"""
            <div class="card-figure">
              <img src="{converter_imagem_base64(fig['caminho'])}" alt="{legenda_limpa}" />
              <p class="figure-caption"><strong>{fig['id'].capitalize()}:</strong> {legenda_limpa}</p>
            </div>
            """)

    galeria_html = "".join(cards_figuras)

    template_completo = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titulo_relatorio}</title>
  <style>
    :root {{
      --primary: #0f172a;
      --secondary: #1e3a8a;
      --accent: #2563eb;
      --text: #1e293b;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.65;
      margin: 0;
      padding: 30px 15px;
    }}
    .container {{
      max-width: 920px;
      margin: 0 auto;
      background: var(--card-bg);
      padding: 45px 55px;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
      border: 1px solid var(--border);
    }}
    h1 {{
      color: var(--primary);
      font-size: 26px;
      border-bottom: 3px solid var(--accent);
      padding-bottom: 12px;
      margin-top: 0;
    }}
    h2 {{
      color: var(--secondary);
      font-size: 20px;
      margin-top: 32px;
      border-left: 4px solid var(--accent);
      padding-left: 10px;
    }}
    h3 {{
      color: var(--primary);
      font-size: 16px;
      margin-top: 22px;
    }}
    p, li {{
      font-size: 15px;
      color: #334155;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
      font-size: 14px;
    }}
    th, td {{
      padding: 10px 14px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}
    th {{
      background-color: #f1f5f9;
      color: var(--primary);
      font-weight: 600;
    }}
    tr:hover {{
      background-color: #f8fafc;
    }}
    blockquote {{
      background: #eff6ff;
      border-left: 4px solid var(--accent);
      margin: 15px 0;
      padding: 12px 18px;
      border-radius: 0 6px 6px 0;
    }}
    .gallery-section {{
      margin-top: 45px;
      padding-top: 25px;
      border-top: 2px dashed var(--border);
    }}
    .gallery-title {{
      text-align: center;
      color: var(--primary);
      font-size: 21px;
      margin-bottom: 25px;
      border: none;
      padding: 0;
    }}
    .card-figure {{
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 15px;
      margin-bottom: 30px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.03);
      text-align: center;
      page-break-inside: avoid;
    }}
    .card-figure img {{
      max-width: 100%;
      height: auto;
      border-radius: 4px;
    }}
    .figure-caption {{
      font-size: 13.5px;
      color: #475569;
      margin-top: 10px;
      text-align: center;
    }}
    @media print {{
      body {{ background: #fff; padding: 0; }}
      .container {{ box-shadow: none; border: none; padding: 15px; max-width: 100%; }}
      .card-figure {{ page-break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    {conteudo_html_corpo}
    <section class="gallery-section">
      <h2 class="gallery-title">Painel de Evidências Gráficas Científicas</h2>
      {galeria_html}
    </section>
  </div>
</body>
</html>
"""
    caminho_html_saida.write_text(template_completo, encoding="utf-8")


def aplicar_borda_tabela(tabela):
    """Aplica bordas suaves e sombreamento no cabeçalho da tabela Word."""
    shading_xml = parse_xml(r'<w:shd {} w:fill="F1F5F9"/>'.format(nsdecls("w")))
    for cell in tabela.rows[0].cells:
        cell._tc.get_or_add_tcPr().append(shading_xml)


def gerar_relatorio_docx(texto_markdown, figuras_geradas, caminho_docx_saida, metadados, titulo_relatorio):
    """Gera um arquivo Word formatado segundo as normas ABNT com gráficos e tabelas."""
    doc = Document()

    # Configuração estrita de margens ABNT: Superior 3cm, Esquerda 3cm, Inferior 2cm, Direita 2cm
    for section in doc.sections:
        section.top_margin = Cm(3.0)
        section.left_margin = Cm(3.0)
        section.bottom_margin = Cm(2.0)
        section.right_margin = Cm(2.0)

    # Estilo Normal Padrão ABNT (Arial 12 pt, espaçamento 1.5, Justificado)
    estilo_normal = doc.styles["Normal"]
    estilo_normal.font.name = "Arial"
    estilo_normal.font.size = Pt(12)
    estilo_normal.font.color.rgb = RGBColor(0, 0, 0)
    estilo_normal.paragraph_format.line_spacing = 1.5
    estilo_normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Título do Documento
    p_titulo = doc.add_paragraph()
    p_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_titulo.paragraph_format.space_before = Pt(0)
    p_titulo.paragraph_format.space_after = Pt(12)
    run_tit = p_titulo.add_run(f"{sanitizar_texto_latex(titulo_relatorio).upper()}\n")
    run_tit.bold = True
    run_tit.font.size = Pt(14)

    run_sub = p_titulo.add_run(
        f"Estudo de Caso: {metadados.get('cidade')} | Período: {metadados.get('periodo', {}).get('inicio')} a {metadados.get('periodo', {}).get('fim')}\n"
    )
    run_sub.font.size = Pt(11)
    run_sub.italic = True

    linhas = texto_markdown.splitlines()
    i = 0
    while i < len(linhas):
        linha_bruta = linhas[i].strip()
        linha = sanitizar_texto_latex(linha_bruta)

        if not linha:
            i += 1
            continue

        if linha.startswith("# "):
            i += 1
            continue
        elif linha.startswith("## "):
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(18)
            h.paragraph_format.space_after = Pt(6)
            run = h.add_run(linha.replace("## ", "").upper())
            run.bold = True
            run.font.size = Pt(12)
        elif linha.startswith("### "):
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(4)
            run = h.add_run(linha.replace("### ", ""))
            run.bold = True
            run.font.size = Pt(12)
        elif linha.startswith("|") and "|" in linha[1:]:
            linhas_tabela = []
            while i < len(linhas) and linhas[i].strip().startswith("|"):
                linhas_tabela.append(sanitizar_texto_latex(linhas[i].strip()))
                i += 1
            if len(linhas_tabela) >= 2:
                cabecalho = [col.strip() for col in linhas_tabela[0].split("|")[1:-1]]
                linhas_dados = [
                    [col.strip() for col in l.split("|")[1:-1]]
                    for l in linhas_tabela[2:]
                ]
                tabela_doc = doc.add_table(rows=1 + len(linhas_dados), cols=len(cabecalho))
                tabela_doc.alignment = WD_TABLE_ALIGNMENT.CENTER
                aplicar_borda_tabela(tabela_doc)

                for col_idx, nome_col in enumerate(cabecalho):
                    cell = tabela_doc.cell(0, col_idx)
                    cell.text = nome_col
                    p_cell = cell.paragraphs[0]
                    p_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    if p_cell.runs:
                        p_cell.runs[0].bold = True
                        p_cell.runs[0].font.size = Pt(10)

                for row_idx, linha_dado in enumerate(linhas_dados):
                    for col_idx, valor_col in enumerate(linha_dado):
                        cell = tabela_doc.cell(1 + row_idx, col_idx)
                        cell.text = valor_col
                        p_cell = cell.paragraphs[0]
                        if p_cell.runs:
                            p_cell.runs[0].font.size = Pt(9.5)
            continue
        elif linha.startswith("- ") or linha.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(3)
            texto_limpo = re.sub(r"^[-*]\s+", "", linha)
            partes = re.split(r"(\*\*.*?\*\*)", texto_limpo)
            for parte in partes:
                if parte.startswith("**") and parte.endswith("**"):
                    p.add_run(parte[2:-2]).bold = True
                else:
                    p.add_run(parte)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.first_line_indent = Cm(1.25)
            p.paragraph_format.space_after = Pt(6)
            partes = re.split(r"(\*\*.*?\*\*)", linha)
            for parte in partes:
                if parte.startswith("**") and parte.endswith("**"):
                    p.add_run(parte[2:-2]).bold = True
                else:
                    p.add_run(parte)
        i += 1

    # Seção de Figuras no Padrão ABNT
    if figuras_geradas:
        p_sec_fig = doc.add_paragraph()
        p_sec_fig.paragraph_format.space_before = Pt(24)
        run_sec_fig = p_sec_fig.add_run("ANEXO: ILUSTRAÇÕES E EVIDÊNCIAS GRÁFICAS")
        run_sec_fig.bold = True
        run_sec_fig.font.size = Pt(12)

        for fig in figuras_geradas:
            caminho_img = fig.get("caminho")
            legenda = sanitizar_texto_latex(fig.get("legenda", "Ilustração técnica"))
            if caminho_img and Path(caminho_img).exists():
                p_leg = doc.add_paragraph()
                p_leg.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_leg.paragraph_format.space_before = Pt(14)
                p_leg.paragraph_format.space_after = Pt(4)
                run_l = p_leg.add_run(legenda)
                run_l.bold = True
                run_l.font.size = Pt(10)

                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.add_run().add_picture(str(caminho_img), width=Cm(15))

                p_fonte = doc.add_paragraph()
                p_fonte.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_fonte.paragraph_format.space_after = Pt(12)
                run_f = p_fonte.add_run("Fonte: Elaborado pelos autores com base em medições meteorológicas (2026).")
                run_f.font.size = Pt(10)
                run_f.italic = True

    doc.save(str(caminho_docx_saida))


# ==============================================================================
# ORQUESTRADOR PRINCIPAL
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Agente Editorial e Redator de Relatório Estatístico Climatológico"
    )
    args = parser.parse_args()

    inicio_execucao = datetime.now()
    timestamp_str = inicio_execucao.strftime("%Y%m%d_%H%M%S")

    print("=" * 75)
    print("ETAPA 3: AGENTE EDITORIAL E REDATOR CIENTÍFICO (SEM LATEX CRU / TOM FORMAL)")
    print("=" * 75)

    if not ARQUIVO_DADOS_CSV.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {ARQUIVO_DADOS_CSV}")
    if not ARQUIVO_ESTATISTICAS.exists():
        raise FileNotFoundError(f"Arquivo de estatísticas não encontrado: {ARQUIVO_ESTATISTICAS}")
    if not ARQUIVO_PROMPT.exists():
        raise FileNotFoundError(f"Template de prompt não encontrado: {ARQUIVO_PROMPT}")

    df = pd.read_csv(ARQUIVO_DADOS_CSV)
    estatisticas_json = json.loads(ARQUIVO_ESTATISTICAS.read_text(encoding="utf-8"))
    metadados = estatisticas_json.get("metadados", {})

    print(f"\n-> Dados estatísticos carregados:")
    print(f"   Localidade: {metadados.get('cidade')} | Período: {metadados.get('periodo', {}).get('inicio')} a {metadados.get('periodo', {}).get('fim')}")

    # 1. Consulta a IA com o novo prompt estrito
    print("\n[1/4] Consultando o modelo Gemini (Redação intuitiva, sem LaTeX e impessoal)...")
    template_prompt = ARQUIVO_PROMPT.read_text(encoding="utf-8")
    prompt_renderizado = (
        template_prompt
        .replace("{cidade}", str(metadados.get("cidade", "Rio de Janeiro")))
        .replace("{periodo_inicio}", str(metadados.get("periodo", {}).get("inicio", "")))
        .replace("{periodo_fim}", str(metadados.get("periodo", {}).get("fim", "")))
        .replace("{tamanho_amostral}", str(metadados.get("tamanho_amostral", 14)))
        .replace("{estatisticas_json}", json.dumps(estatisticas_json, indent=2, ensure_ascii=False))
    )

    resposta_modelo = consultar_modelo(prompt_renderizado)

    # 2. Extrai o plano editorial autônomo e o texto Markdown
    plano_editorial, texto_markdown = extrair_resposta_dupla(resposta_modelo)
    titulo_relatorio = plano_editorial.get("titulo_relatorio", "Relatório Técnico-Científico de Estatística Aplicada ao Clima")
    figuras_solicitadas = plano_editorial.get("figuras_encomendadas", [])

    print(f"\n[2/4] Plano Editorial recebido da IA:")
    print(f"      • Título Definido: \"{titulo_relatorio}\"")
    print(f"      • Figuras Solicitadas ({len(figuras_solicitadas)}):")

    # 3. Python executa as ferramentas gráficas encomendadas
    figuras_geradas = []
    for idx, config_fig in enumerate(figuras_solicitadas, start=1):
        tipo = config_fig.get("tipo_ferramenta")
        legenda = config_fig.get("legenda_abnt", f"Figura {idx}")
        print(f"        [{idx}] Ferramenta: '{tipo}' -> Legenda: {legenda}")
        caminho_fig = despachar_geracao_figura(df, config_fig, idx, PASTA_GRAFICOS)
        if caminho_fig and caminho_fig.exists():
            figuras_geradas.append({
                "id": f"figura_{idx}",
                "tipo": tipo,
                "legenda": legenda,
                "caminho": caminho_fig
            })

    # 4. Salva artefatos limpos
    print("\n[3/4] Persistindo Plano Editorial e Markdown Limpo...")
    texto_markdown_limpo = sanitizar_texto_latex(texto_markdown)
    ARQUIVO_SAIDA_PLANO.write_text(json.dumps(plano_editorial, indent=2, ensure_ascii=False), encoding="utf-8")
    ARQUIVO_SAIDA_MD.write_text(texto_markdown_limpo, encoding="utf-8")
    print(f"      • Plano Editorial salvo: {ARQUIVO_SAIDA_PLANO.name}")
    print(f"      • Markdown Limpo salvo: {ARQUIVO_SAIDA_MD.name}")

    # 5. Exporta para HTML Executivo e Word ABNT com sanitização e diagramação aprimoradas
    print("\n[4/4] Diagramando saídas em HTML Executivo e Word ABNT...")
    gerar_relatorio_html(texto_markdown_limpo, figuras_geradas, ARQUIVO_SAIDA_HTML, titulo_relatorio)
    print(f"      • Documento HTML salvo: {ARQUIVO_SAIDA_HTML.name}")

    gerar_relatorio_docx(texto_markdown_limpo, figuras_geradas, ARQUIVO_SAIDA_DOCX, metadados, titulo_relatorio)
    print(f"      • Documento Word ABNT salvo: {ARQUIVO_SAIDA_DOCX.name}")

    # 6. Registra auditoria
    registro_run = {
        "timestamp": timestamp_str,
        "etapa": "03_relatorio",
        "metadados": metadados,
        "plano_editorial_ia": plano_editorial,
        "artefatos_produzidos": {
            "plano_editorial": str(ARQUIVO_SAIDA_PLANO.name),
            "relatorio_markdown": str(ARQUIVO_SAIDA_MD.name),
            "relatorio_html": str(ARQUIVO_SAIDA_HTML.name),
            "relatorio_docx": str(ARQUIVO_SAIDA_DOCX.name),
            "total_figuras_geradas": len(figuras_geradas)
        }
    }
    arquivo_run = PASTA_RUNS / f"run_{timestamp_str}_relatorio.json"
    arquivo_run.write_text(json.dumps(registro_run, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 75)
    print("ETAPA 3 CONCLUÍDA COM SUCESSO! SAÍDAS REFINADAS:")
    print("=" * 75)
    print(f"1. Markdown (Texto Limpo): {ARQUIVO_SAIDA_MD}")
    print(f"2. HTML Executivo:         {ARQUIVO_SAIDA_HTML}")
    print(f"3. Word Padrão ABNT:       {ARQUIVO_SAIDA_DOCX}")
    print(f"4. Figuras Encomendadas:   {len(figuras_geradas)} imagens em {PASTA_GRAFICOS}")
    print("=" * 75)


if __name__ == "__main__":
    main()
