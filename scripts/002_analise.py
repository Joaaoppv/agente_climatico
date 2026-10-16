
import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# ============================================================
# CONFIGURAÇÕES DO AMBIENTE
# ============================================================

OPEN_CODE = (
    Path.home()
    / "AppData/Roaming/npm/node_modules/opencode-ai/bin/opencode.exe"
)

MODELO_PADRAO = "opencode/deepseek-v4.1-flash-free"

PASTA_ATUAL = Path(__file__).resolve().parent
PASTA_RAIZ = (
    PASTA_ATUAL.parent
    if PASTA_ATUAL.name in ("runs", "scripts")
    else PASTA_ATUAL
)

ARQUIVO_DADOS_CSV = (
    PASTA_RAIZ
    / "output"
    / "01_coleta"
    / "dados_clima.csv"
)

ARQUIVO_PROMPT = (
    PASTA_RAIZ
    / "prompts"
    / "02_prompt_analise.md"
)

PASTA_OUTPUT = PASTA_RAIZ / "output" / "02_analise"
PASTA_RUNS = PASTA_RAIZ / "runs"

ARQUIVO_SAIDA_PLANO = PASTA_OUTPUT / "plano_analise.json"
ARQUIVO_SAIDA_ESTATISTICAS = (
    PASTA_OUTPUT / "analise_estatistica.json"
)

PASTA_OUTPUT.mkdir(parents=True, exist_ok=True)
PASTA_RUNS.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONSULTA AO MODELO
# ============================================================

def consultar_modelo(texto_prompt, modelo=MODELO_PADRAO):
    """Consulta um modelo pelo CLI do OpenCode."""

    if not OPEN_CODE.exists():
        raise FileNotFoundError(
            f"Executável OpenCode não encontrado em: {OPEN_CODE}"
        )

    resposta = subprocess.run(

        [
            str(OPEN_CODE),
            "run",
            "--pure",
            "--dir",
            str(PASTA_RAIZ),
            "--agent",
            "build",
            "--model",
            modelo,
            texto_prompt,
        ],

        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300
    )

    if resposta.returncode != 0:
        erro = resposta.stderr.strip() or (
            f"Código de saída: {resposta.returncode}"
        )
        raise RuntimeError(
            f"Erro na execução do OpenCode: {erro}"
        )

    saida = resposta.stdout.strip()

    if not saida:
        raise RuntimeError(
        "O OpenCode retornou uma resposta vazia.\n"
        f"STDERR: {resposta.stderr.strip()!r}\n"
        f"STDOUT: {resposta.stdout!r}\n"
        f"Código de saída: {resposta.returncode}"        )

    return saida


# ============================================================
# EXTRAÇÃO DO PLANO JSON
# ============================================================

def extrair_plano_json(resposta_modelo):
    """Extrai o bloco JSON com o plano estatístico decidido pela IA."""

    # 1. Tenta capturar um bloco ```json ... ```
    blocos = re.findall(
        r"```(?:json)?\s*([\s\S]*?)\s*```",
        resposta_modelo,
        flags=re.IGNORECASE
    )

    for bloco in reversed(blocos):
        try:
            dados = json.loads(bloco.strip())

            if (
                "variaveis_univariadas" in dados
                or "pares_associacao" in dados
            ):
                return dados

        except (json.JSONDecodeError, TypeError):
            continue

    # 2. Tenta encontrar objetos JSON na resposta
    decodificador = json.JSONDecoder()

    for match in re.finditer(r"\{", resposta_modelo):
        try:
            dados, _ = decodificador.raw_decode(
                resposta_modelo[match.start():]
            )

            if (
                isinstance(dados, dict)
                and (
                    "variaveis_univariadas" in dados
                    or "pares_associacao" in dados
                )
            ):
                return dados

        except json.JSONDecodeError:
            continue

    raise ValueError(
        "A IA não retornou um JSON estruturado válido "
        "com o plano de análise."
    )


# ============================================================
# ESTATÍSTICA UNIVARIADA
# ============================================================

def calcular_moda_discretizada(serie, casas_decimais=1):
    """Calcula a moda sobre valores arredondados."""

    valores_arredondados = serie.round(casas_decimais)
    contagens = valores_arredondados.value_counts()

    if contagens.empty:
        return None

    freq_max = contagens.iloc[0]

    if freq_max <= 1 and len(serie) > 3:
        return None

    modas = contagens[
        contagens == freq_max
    ].index.tolist()

    return round(float(modas[0]), 4)


def calcular_univariada(serie):
    """Calcula estatísticas descritivas univariadas."""

    valores = serie.dropna().to_numpy(dtype=float)
    n = len(valores)

    if n == 0:
        return {}

    media = float(np.mean(valores))
    mediana = float(np.median(valores))
    moda = calcular_moda_discretizada(
        pd.Series(valores)
    )

    variancia = (
        float(np.var(valores, ddof=1))
        if n > 1 else 0.0
    )

    desvio_padrao = (
        float(np.std(valores, ddof=1))
        if n > 1 else 0.0
    )

    val_min = float(np.min(valores))
    val_max = float(np.max(valores))
    amplitude = float(val_max - val_min)

    p25 = float(np.percentile(valores, 25))
    p75 = float(np.percentile(valores, 75))
    iqr = float(p75 - p25)

    skewness = (
        float(stats.skew(valores, bias=False))
        if n > 2 else 0.0
    )

    kurtosis = (
        float(stats.kurtosis(valores, bias=False))
        if n > 3 else 0.0
    )

    # Intervalo de confiança para a média
    ic_95 = None

    if n > 1 and desvio_padrao > 0:
        erro_padrao = desvio_padrao / np.sqrt(n)

        margem = float(
            stats.t.ppf(
                0.975,
                df=n - 1
            ) * erro_padrao
        )

        ic_95 = {
            "limite_inferior": round(
                media - margem, 4
            ),
            "limite_superior": round(
                media + margem, 4
            ),
            "margem_erro": round(margem, 4),
            "nivel_confianca": 0.95,
            "distribuicao": "t-Student",
            "graus_liberdade": n - 1
        }

    # Teste de normalidade de Shapiro-Wilk
    teste_shapiro = None

    if 3 <= n <= 5000:
        stat_w, p_val = stats.shapiro(valores)

        teste_shapiro = {
            "estatistica_w": round(
                float(stat_w), 4
            ),
            "p_valor": round(
                float(p_val), 5
            ),
            "distribuicao_normal_5pct": bool(
                p_val >= 0.05
            ),
            "interpretacao": (
                "Não há evidências para rejeitar a normalidade"
                if p_val >= 0.05
                else "Rejeita-se a hipótese de normalidade"
            )
        }

    return {
        "n_observacoes": n,
        "medidas_posicao": {
            "media": round(media, 4),
            "mediana": round(mediana, 4),
            "moda": moda,
            "percentil_25": round(p25, 4),
            "percentil_75": round(p75, 4)
        },
        "medidas_dispersao": {
            "variancia_amostral": round(
                variancia, 4
            ),
            "desvio_padrao": round(
                desvio_padrao, 4
            ),
            "minimo": round(val_min, 4),
            "maximo": round(val_max, 4),
            "amplitude_total": round(
                amplitude, 4
            ),
            "amplitude_interquartil_iqr": round(
                iqr, 4
            )
        },
        "forma_distribuicao": {
            "assimetria_skewness": round(
                skewness, 4
            ),
            "curtose_kurtosis": round(
                kurtosis, 4
            )
        },
        "intervalo_confianca_95": ic_95,
        "teste_normalidade_shapiro": teste_shapiro
    }


# ============================================================
# ESTATÍSTICA BIVARIADA
# ============================================================

def classificar_forca_correlacao(r):
    """Classifica a magnitude da correlação."""

    modulo = abs(r)
    direcao = (
        "positiva" if r >= 0 else "negativa"
    )

    if modulo >= 0.8:
        forca = "muito forte"
    elif modulo >= 0.6:
        forca = "forte"
    elif modulo >= 0.4:
        forca = "moderada"
    elif modulo >= 0.2:
        forca = "fraca"
    else:
        forca = "muito fraca ou desprezível"

    return f"{forca} {direcao}"


def calcular_bivariada(df, var_x, var_y):
    """Calcula covariância e correlações de Pearson e Spearman."""

    sub = df[[var_x, var_y]].dropna()

    if len(sub) < 3:
        return None

    x = sub[var_x].to_numpy(dtype=float)
    y = sub[var_y].to_numpy(dtype=float)

    if np.std(x) == 0 or np.std(y) == 0:
        return None

    cov = float(np.cov(x, y, ddof=1)[0, 1])

    r_pearson, p_pearson = stats.pearsonr(x, y)
    rho_spearman, p_spearman = stats.spearmanr(x, y)

    return {
        "variavel_x": var_x,
        "variavel_y": var_y,
        "n_pares": len(sub),
        "covariancia": round(cov, 4),
        "correlacao_pearson": {
            "coeficiente_r": round(
                float(r_pearson), 4
            ),
            "p_valor": round(
                float(p_pearson), 5
            ),
            "significativo_5pct": bool(
                p_pearson < 0.05
            ),
            "classificacao": classificar_forca_correlacao(
                r_pearson
            )
        },
        "correlacao_spearman": {
            "coeficiente_rho": round(
                float(rho_spearman), 4
            ),
            "p_valor": round(
                float(p_spearman), 5
            ),
            "significativo_5pct": bool(
                p_spearman < 0.05
            ),
            "classificacao": classificar_forca_correlacao(
                rho_spearman
            )
        }
    }


# ============================================================
# REGRESSÃO TEMPORAL
# ============================================================

def calcular_regressao_temporal(df, variavel):
    """Modela a evolução temporal por regressão linear simples."""

    sub = df[["data", variavel]].dropna().copy()

    if len(sub) < 3:
        return None

    sub["data"] = pd.to_datetime(
        sub["data"],
        errors="coerce"
    )

    sub = sub.dropna(subset=["data"])
    sub = sub.sort_values("data")

    if len(sub) < 3:
        return None

    x = (
        sub["data"] - sub["data"].min()
    ).dt.total_seconds().to_numpy() / 86400

    y = sub[variavel].to_numpy(dtype=float)

    if len(np.unique(x)) < 2:
        return None

    reg = stats.linregress(x, y)
    r2 = float(reg.rvalue ** 2)

    if reg.pvalue < 0.05:
        tendencia = (
            "ascendente"
            if reg.slope > 0
            else "descendente"
        )
    else:
        tendencia = (
            "sem tendência estatisticamente significativa a 5%"
        )

    return {
        "variavel": variavel,
        "periodo_dias": len(sub),
        "coeficiente_angular_beta": round(
            float(reg.slope), 4
        ),
        "intercepto_alpha": round(
            float(reg.intercept), 4
        ),
        "coeficiente_determinacao_r2": round(
            r2, 4
        ),
        "p_valor_inclinacao": round(
            float(reg.pvalue), 5
        ),
        "erro_padrao": round(
            float(reg.stderr), 4
        ),
        "significativo_5pct": bool(
            reg.pvalue < 0.05
        ),
        "tendencia_diagnosticada": tendencia,
        "interpretacao_pratica": (
            f"Variação média estimada de "
            f"{reg.slope:+.4f} unidades/dia"
        )
    }


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Agente de Análise Estatística "
            "(Planejamento via IA + Motor Matemático em Python)"
        )
    )

    parser.add_argument(
        "--arquivo_csv",
        type=str,
        default=str(ARQUIVO_DADOS_CSV),
        help="Caminho do arquivo CSV de entrada"
    )

    args = parser.parse_args()

    inicio_execucao = datetime.now()
    timestamp_str = inicio_execucao.strftime(
        "%Y%m%d_%H%M%S"
    )

    print("=" * 75)
    print(
        "ETAPA 2: AGENTE DE ANÁLISE ESTATÍSTICA "
        "(ESTRATÉGIA IA + MOTOR NUMÉRICO)"
    )
    print("=" * 75)

    caminho_csv = Path(args.arquivo_csv)

    if not caminho_csv.exists():
        raise FileNotFoundError(
            f"Arquivo CSV não encontrado: {caminho_csv}"
        )

    df = pd.read_csv(caminho_csv)

    if df.empty:
        raise ValueError(
            "O arquivo CSV não contém observações."
        )

    cidade = (
        df["cidade"].iloc[0]
        if "cidade" in df.columns
        else "Cidade Não Informada"
    )

    colunas_numericas = (
        df.select_dtypes(include=[np.number])
        .columns.tolist()
    )

    print(f"\n-> Dataset carregado: {caminho_csv.name}")
    print(
        f"   Localidade: {cidade} | "
        f"Linhas: {len(df)} | "
        f"Variáveis numéricas: {len(colunas_numericas)}"
    )

    # 1. Carrega o template de prompt
    if not ARQUIVO_PROMPT.exists():
        raise FileNotFoundError(
            f"Template de prompt não encontrado: {ARQUIVO_PROMPT}"
        )

    template_prompt = ARQUIVO_PROMPT.read_text(
        encoding="utf-8"
    )

    prompt_renderizado = (
        template_prompt
        .replace("{cidade}", str(cidade))
        .replace("{n_linhas}", str(len(df)))
        .replace(
            "{colunas_json}",
            json.dumps(
                colunas_numericas,
                indent=2,
                ensure_ascii=False
            )
        )
    )

    # 2. Consulta o modelo
    print(
        f"\n[1/4] Consultando o modelo OpenCode "
        f"({MODELO_PADRAO}) para planejar a bateria analítica..."
    )

    resposta_ia = consultar_modelo(prompt_renderizado)

    (PASTA_OUTPUT / "resposta_bruta_ia.txt").write_text(
    resposta_ia,
    encoding="utf-8"
    )

    print("\n--- RESPOSTA BRUTA DA IA ---")
    print(resposta_ia)
    print("--- FIM DA RESPOSTA ---\n")

    # 3. Extrai o plano
    plano_ia = extrair_plano_json(resposta_ia)

    print(
        "\n[2/4] Plano Estatístico formulado "
        "com sucesso pela IA:"
    )

    vars_univariadas = plano_ia.get(
        "variaveis_univariadas",
        colunas_numericas
    )

    pares_associacao = plano_ia.get(
        "pares_associacao",
        []
    )

    vars_regressao = plano_ia.get(
        "variaveis_regressao_temporal",
        []
    )

    # Valida o plano contra as colunas disponíveis
    vars_univariadas = [
        var for var in vars_univariadas
        if isinstance(var, str)
        and var in colunas_numericas
    ]

    pares_associacao = [
        par for par in pares_associacao
        if isinstance(par, dict)
        and par.get("var_x") in colunas_numericas
        and par.get("var_y") in colunas_numericas
    ]

    print(
        f"      • Variáveis para Análise Univariada "
        f"({len(vars_univariadas)}): {vars_univariadas}"
    )

    print(
        f"      • Pares para Associação "
        f"({len(pares_associacao)} pares)"
    )

    print(
        f"      • Modelos de Tendência Temporal "
        f"({len(vars_regressao)} variáveis)"
    )

    # 4. Executa os cálculos matemáticos
    print(
        "\n[3/4] Python executando bateria de "
        "cálculos matemáticos com SciPy e pandas..."
    )

    # A) Estatísticas univariadas
    resultados_univariadas = {}

    for var in vars_univariadas:
        resultados_univariadas[var] = (
            calcular_univariada(df[var])
        )

    # B) Associação entre pares de variáveis
    resultados_bivariadas = []

    for par in pares_associacao:
        vx = par.get("var_x")
        vy = par.get("var_y")

        res = calcular_bivariada(df, vx, vy)

        if res:
            res["justificativa_didatica"] = (
                par.get("justificativa_didatica", "")
            )
            resultados_bivariadas.append(res)

    # C) Regressão temporal
    resultados_regressao = []

    for reg_item in vars_regressao:
        v_nome = (
            reg_item.get("variavel")
            if isinstance(reg_item, dict)
            else reg_item
        )

        if isinstance(v_nome, str) and v_nome in df.columns:
            res_reg = calcular_regressao_temporal(
                df,
                v_nome
            )

            if res_reg:
                if isinstance(reg_item, dict):
                    res_reg["pergunta_cientifica"] = (
                        reg_item.get("pergunta_cientifica", "")
                    )

                resultados_regressao.append(res_reg)

    # Consolidação dos resultados
    resultado_estatistico_completo = {
        "metadados": {
            "gerado_em": timestamp_str,
            "cidade": cidade,
            "tamanho_amostral": len(df),
            "periodo": {
                "inicio": (
                    str(df["data"].min())
                    if "data" in df.columns
                    else None
                ),
                "fim": (
                    str(df["data"].max())
                    if "data" in df.columns
                    else None
                )
            }
        },
        "analise_univariada": resultados_univariadas,
        "analise_bivariada_associacao": resultados_bivariadas,
        "regressao_temporal": resultados_regressao,
        "hipoteses_orientadoras": plano_ia.get(
            "hipoteses_orientadoras",
            []
        )
    }

    # 5. Salva os artefatos
    ARQUIVO_SAIDA_PLANO.write_text(
        json.dumps(
            plano_ia,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    ARQUIVO_SAIDA_ESTATISTICAS.write_text(
        json.dumps(
            resultado_estatistico_completo,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    registro_run = {
        "timestamp": timestamp_str,
        "etapa": "02_analise",
        "modelo": MODELO_PADRAO,
        "parametros": {
            "arquivo_csv": str(caminho_csv.name),
            "cidade": cidade,
            "n_linhas": len(df)
        },
        "plano_ia": plano_ia,
        "sumario_resultados": {
            "total_univariadas": len(
                resultados_univariadas
            ),
            "total_pares_bivariados": len(
                resultados_bivariadas
            ),
            "total_regressoes": len(
                resultados_regressao
            )
        }
    }

    arquivo_run = (
        PASTA_RUNS
        / f"run_{timestamp_str}_analise.json"
    )

    arquivo_run.write_text(
        json.dumps(
            registro_run,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print(
        "\n[4/4] Artefatos estatísticos "
        "gerados com sucesso:"
    )

    print(f"-> Plano da IA: {ARQUIVO_SAIDA_PLANO}")
    print(
        f"-> Estatísticas Calculadas: "
        f"{ARQUIVO_SAIDA_ESTATISTICAS}"
    )
    print(f"-> Registro de Run: {arquivo_run}")

    # Prévia dos resultados
    print("\n" + "=" * 75)
    print("AMOSTRA DOS RESULTADOS CALCULADOS:")
    print("=" * 75)

    if "temperature_2m_max" in resultados_univariadas:
        t_max = resultados_univariadas[
            "temperature_2m_max"
        ]

        print("• Temperatura Máxima (°C):")

        print(
            f"  Média: {t_max['medidas_posicao']['media']} | "
            f"Mediana: {t_max['medidas_posicao']['mediana']} | "
            f"Desv. Padrão: "
            f"{t_max['medidas_dispersao']['desvio_padrao']}"
        )

        ic = t_max["intervalo_confianca_95"]

        if ic is not None:
            print(
                f"  IC 95%: "
                f"[{ic['limite_inferior']}, "
                f"{ic['limite_superior']}]"
            )
        else:
            print("  IC 95%: não calculado")

        shapiro = t_max["teste_normalidade_shapiro"]

        if shapiro is not None:
            classificacao = (
                "Compatível com normalidade"
                if shapiro["distribuicao_normal_5pct"]
                else "Evidência contra normalidade"
            )

            print(
                f"  Shapiro-Wilk (p-valor): "
                f"{shapiro['p_valor']} "
                f"({classificacao})"
            )

    if resultados_bivariadas:
        par0 = resultados_bivariadas[0]

        print(
            f"\n• Associação {par0['variavel_x']} "
            f"vs {par0['variavel_y']}:"
        )

        print(
            f"  Pearson r: "
            f"{par0['correlacao_pearson']['coeficiente_r']} "
            f"({par0['correlacao_pearson']['classificacao']}, "
            f"p={par0['correlacao_pearson']['p_valor']})"
        )

        print(
            f"  Spearman rho: "
            f"{par0['correlacao_spearman']['coeficiente_rho']} "
            f"(p={par0['correlacao_spearman']['p_valor']})"
        )

    print("=" * 75)


if __name__ == "__main__":
    main()
