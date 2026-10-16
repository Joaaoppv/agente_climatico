import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
import pandas as pd
import requests

# Configurações do OpenCode
OPEN_CODE = "opencode.cmd"
MODELO_PADRAO = "opencode/deepseek-v4.1-flash-free"

PASTA_ATUAL = Path(__file__).resolve().parent
PASTA_RAIZ = PASTA_ATUAL.parent if PASTA_ATUAL.name in ("runs", "scripts") else PASTA_ATUAL

ARQUIVO_FONTES = PASTA_RAIZ / "input" / "fontes.json"
ARQUIVO_PROMPT = PASTA_RAIZ / "prompts" / "01_prompt_coleta.md"
PASTA_OUTPUT = PASTA_RAIZ / "output" / "01_coleta"
PASTA_RUNS = PASTA_RAIZ / "runs"

ARQUIVO_SAIDA_CSV = PASTA_OUTPUT / "dados_clima.csv"
ARQUIVO_SAIDA_DECISAO = PASTA_OUTPUT / "decisao_coleta.json"

PASTA_OUTPUT.mkdir(parents=True, exist_ok=True)
PASTA_RUNS.mkdir(parents=True, exist_ok=True)

COORDENADAS_PADRAO = {
    "sao paulo": (-23.5505, -46.6333),
    "são paulo": (-23.5505, -46.6333),
    "rio de janeiro": (-22.9068, -43.1729),
    "curitiba": (-25.4284, -49.2733),
    "belo horizonte": (-19.9208, -43.9378),
    "brasilia": (-15.7975, -47.8919),
    "brasília": (-15.7975, -47.8919),
    "porto alegre": (-30.0346, -51.2177),
    "salvador": (-12.9777, -38.5016),
    "recife": (-8.0476, -34.8770),
    "fortaleza": (-3.7319, -38.5267),
}


def obter_coordenadas(cidade):
    """Obtém latitude e longitude via API ou tabela local."""
    chave = cidade.strip().lower()
    if chave in COORDENADAS_PADRAO:
        return COORDENADAS_PADRAO[chave]

    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={requests.utils.quote(cidade)}&count=1&language=pt&format=json"
    )
    resposta = requests.get(url, timeout=15)
    resposta.raise_for_status()
    dados = resposta.json()

    if dados.get("results"):
        resultado = dados["results"][0]
        return float(resultado["latitude"]), float(resultado["longitude"])

    raise ValueError(f"Não foi possível localizar as coordenadas da cidade: {cidade}")


def consultar_modelo(texto_prompt, modelo=MODELO_PADRAO):
    """Consulta um modelo pelo CLI do OpenCode."""
    open_code_exe = (
        Path.home()
        / "AppData/Roaming/npm/node_modules/opencode-ai/bin/opencode.exe"
    )

    resposta = subprocess.run(
        [
            str(open_code_exe),
            "run",
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
        erro = resposta.stderr.strip() or f"Código de saída: {resposta.returncode}"
        raise RuntimeError(f"Erro na execução do OpenCode: {erro}")

    saida = resposta.stdout.strip()

    if not saida:
        raise RuntimeError("O OpenCode retornou uma resposta vazia.")

    return saida

def extrair_decisao_json(resposta_modelo):
    """Extrai o bloco JSON estruturado com a decisão da IA."""
    match_bloco = re.search(
        r"```(?:json)?\s*(\{[\s\S]*?\})\s*```",
        resposta_modelo
    )
    if match_bloco:
        try:
            return json.loads(match_bloco.group(1))
        except json.JSONDecodeError:
            pass

    matches = re.findall(r"\{[\s\S]*?\}", resposta_modelo)
    for candidato in reversed(matches):
        try:
            dados = json.loads(candidato)
            if "fonte_escolhida" in dados:
                return dados
        except json.JSONDecodeError:
            continue

    raise ValueError(
        "A IA não retornou um JSON estruturado válido "
        "com o campo 'fonte_escolhida'."
    )


def coletar_open_meteo(cidade, dias, config_fonte, variaveis_escolhidas):
    """Executa a coleta via Open-Meteo usando as variáveis escolhidas pela IA."""
    lat, lon = obter_coordenadas(cidade)
    endpoint = config_fonte["url"]

    if not variaveis_escolhidas:
        variaveis_escolhidas = [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum"
        ]

    variaveis_param = ",".join(variaveis_escolhidas)
    url = (
        f"{endpoint}?latitude={lat}&longitude={lon}"
        f"&daily={variaveis_param}"
        f"&timezone=auto&past_days={dias}&forecast_days=0"
    )

    print(f"-> Conectando ao endpoint Open-Meteo: {url}")
    resposta = requests.get(url, timeout=20)
    resposta.raise_for_status()
    dados_daily = resposta.json().get("daily", {})

    if not dados_daily:
        raise RuntimeError(
            "A API Open-Meteo não retornou dados diários "
            "para as variáveis solicitadas."
        )

    df = pd.DataFrame(dados_daily)

    if "time" in df.columns:
        df = df.rename(columns={"time": "data"})

    df["cidade"] = cidade
    return df


def coletar_wttr_in(cidade, dias, config_fonte, variaveis_escolhidas):
    """Executa a coleta determinística via wttr.in."""
    endpoint = config_fonte["url"]
    cidade_formatada = cidade.strip().replace(" ", "+")
    url = f"{endpoint}/{cidade_formatada}?format=j1"

    print(f"-> Conectando ao endpoint wttr.in: {url}")
    resposta = requests.get(url, timeout=20)
    resposta.raise_for_status()
    dados = resposta.json()

    linhas = []
    for item in dados.get("weather", [])[:dias]:
        linhas.append({
            "data": item.get("date"),
            "temp_max_c": float(item.get("maxtempC", 0)),
            "temp_min_c": float(item.get("mintempC", 0)),
            "sensacao_max_c": float(item.get("avgtempC", 0)),
            "chuva_mm": float(
                item.get(
                    "totalprecipMM",
                    item.get("hourly", [{}])[0].get("precipMM", 0)
                )
            ),
            "cidade": cidade
        })

    return pd.DataFrame(linhas)


def executar_coleta(decisao_ia, cidade, dias, catalogo_fontes):
    """Executa a ferramenta Python indicada pela decisão da IA."""
    fonte_id = decisao_ia.get("fonte_escolhida", "").strip().lower()
    variaveis = decisao_ia.get("variaveis_selecionadas", [])

    fontes_dict = {
        f["id"]: f
        for f in catalogo_fontes.get("fontes_disponiveis", [])
    }

    if fonte_id not in fontes_dict:
        raise ValueError(
            f"Fonte '{fonte_id}' escolhida pela IA não encontrada no catálogo."
        )

    config = fontes_dict[fonte_id]

    if fonte_id == "open_meteo":
        return coletar_open_meteo(cidade, dias, config, variaveis)
    elif fonte_id == "wttr_in":
        return coletar_wttr_in(cidade, dias, config, variaveis)
    elif fonte_id == "wikipedia":
        raise RuntimeError(
            "A fonte Wikipedia foi escolhida, mas ela contém apenas resumos "
            "qualitativos e não possui dados diários recentes estruturados "
            "para exportação."
        )
    else:
        raise NotImplementedError(
            f"Ferramenta de extração não implementada para a fonte: {fonte_id}"
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Agente de Coleta e Ingestão de Dados Meteorológicos "
            "(Decisão Autônoma via JSON)"
        )
    )
    parser.add_argument(
        "--cidade",
        type=str,
        default="São Paulo",
        help="Nome da cidade alvo para coleta (Padrão: São Paulo)"
    )
    parser.add_argument(
        "--dias",
        type=int,
        default=3,
        help="Quantidade de dias históricos recentes (Padrão: 3)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=MODELO_PADRAO,
        help=f"Modelo do OpenCode (padrão: {MODELO_PADRAO})"
    )

    args = parser.parse_args()

    inicio_execucao = datetime.now()
    timestamp_str = inicio_execucao.strftime("%Y%m%d_%H%M%S")

    print("=" * 70)
    print("ETAPA 1: AGENTE DE COLETA E INGESTÃO (TOOL CALLING VIA JSON)")
    print(f"Cidade Alvo: {args.cidade} | Período Solicitado: {args.dias} dias")
    print(f"Modelo OpenCode: {args.model}")
    print("=" * 70)

    if not ARQUIVO_FONTES.exists():
        raise FileNotFoundError(
            f"Arquivo de catálogo não encontrado: {ARQUIVO_FONTES}"
        )

    conteudo_fontes_json = ARQUIVO_FONTES.read_text(encoding="utf-8")
    catalogo_fontes = json.loads(conteudo_fontes_json)

    if not ARQUIVO_PROMPT.exists():
        raise FileNotFoundError(
            f"Template de prompt não encontrado: {ARQUIVO_PROMPT}"
        )

    template_prompt = ARQUIVO_PROMPT.read_text(encoding="utf-8")

    prompt_renderizado = (
        template_prompt
        .replace("{cidade}", args.cidade)
        .replace("{dias}", str(args.dias))
        .replace("{fontes_json}", conteudo_fontes_json)
    )

    print("\n[1/4] Consultando o modelo OpenCode para selecionar a fonte...")
    resposta_ia = consultar_modelo(prompt_renderizado, args.model)

    decisao_ia = extrair_decisao_json(resposta_ia)

    print("\n" + "=" * 70)
    print("PLANO ESTRUTURADO DECIDIDO PELA IA (JSON DE SAÍDA):")
    print("=" * 70)
    print(json.dumps(decisao_ia, indent=2, ensure_ascii=False))
    print("=" * 70)

    fonte = decisao_ia.get("fonte_escolhida")
    vars_escolhidas = decisao_ia.get("variaveis_selecionadas", [])

    print(f"\n[2/4] Fonte escolhida: '{fonte}'")
    print(
        f"      Variáveis solicitadas pela IA "
        f"({len(vars_escolhidas)}): {vars_escolhidas}"
    )

    print(f"\n[3/4] Python executando ferramenta de extração para '{fonte}'...")
    df_resultado = executar_coleta(
        decisao_ia,
        args.cidade,
        args.dias,
        catalogo_fontes
    )

    df_resultado.to_csv(
        ARQUIVO_SAIDA_CSV,
        index=False,
        encoding="utf-8"
    )
    ARQUIVO_SAIDA_DECISAO.write_text(
        json.dumps(decisao_ia, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    registro_run = {
        "timestamp": timestamp_str,
        "etapa": "01_coleta",
        "parametros": {
            "cidade": args.cidade,
            "dias": args.dias,
            "model": args.model
        },
        "decisao_ia": decisao_ia,
        "resultado": {
            "arquivo_csv": str(ARQUIVO_SAIDA_CSV.name),
            "total_linhas": len(df_resultado),
            "colunas_geradas": list(df_resultado.columns)
        }
    }

    arquivo_run = PASTA_RUNS / f"run_{timestamp_str}_coleta.json"
    arquivo_run.write_text(
        json.dumps(registro_run, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n[4/4] Artefatos gerados com sucesso:")
    print(f"-> Dataset CSV: {ARQUIVO_SAIDA_CSV}")
    print(f"-> Decisão JSON: {ARQUIVO_SAIDA_DECISAO}")
    print(f"-> Registro de Run: {arquivo_run}")

    print("\nPrévia dos dados estruturados:")
    print(df_resultado.to_string(index=False))
    print(
        f"\nTotal de registros: {len(df_resultado)} "
        f"| Colunas geradas: {list(df_resultado.columns)}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
