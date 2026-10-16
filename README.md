# Agente Climático — Pipeline de Análise Meteorológica

Pipeline de três etapas que coleta dados climáticos via API, realiza análise estatística completa e gera um relatório técnico-científico em HTML e Word (ABNT), com gráficos gerados automaticamente.

---

## Estrutura do Projeto

```
agente_climatico/
│
├── README.md                          # Este arquivo
│
├── input/
│   └── fontes.json                    # Catálogo de fontes de dados (Open-Meteo, INMET etc.)
│
├── prompts/
│   ├── 01_prompt_coleta.md            # Prompt do Agente 1 (decisão autônoma de fonte)
│   ├── 02_prompt_analise.md           # Prompt do Agente 2 (plano estatístico)
│   └── 03_prompt_relatorio.md         # Prompt do Agente 3 (editorial e redação)
│
├── scripts/                           # Scripts Python de cada agente
│   ├── 01_coleta.py
│   ├── 02_analise.py
│   └── 03_relatorio.py
│
├── runs/                              # Logs de execução (gerados automaticamente)
│   └── run_<timestamp>_<etapa>.json
│
└── output/
    ├── 01_coleta/
    │   ├── dados_clima.csv            # Dataset meteorológico coletado
    │   └── decisao_coleta.json        # Decisão estruturada da IA sobre a fonte usada
    │
    ├── 02_analise/
    │   ├── plano_analise.json         # Plano estatístico decidido pela IA
    │   └── analise_estatistica.json   # Resultados completos da análise
    │
    └── 03_relatorio/
        ├── graficos/                  # Figuras PNG geradas pelo motor Python
        │   └── figura_*.png
        ├── word/                      # Relatório Word (padrão ABNT)
        │   └── relatorio_climatico.docx
        ├── html/                      # Relatório HTML executivo
        │   └── relatorio_climatico.html
        ├── markdown/                  # Texto bruto do relatório
        │   └── relatorio_climatico.md
        └── planos/                    # Plano editorial decidido pela IA
            └── plano_editorial.json
```

---

## Pré-requisitos

- Python 3.10 ou superior
- Ferramenta `agy` instalada em `%LOCALAPPDATA%\agy\bin\agy.exe`
- Pacotes Python:

```powershell
pip install pandas requests scipy numpy matplotlib python-docx markdown
```

---

## Como Executar o Pipeline

Os três scripts devem ser executados **na ordem abaixo**, a partir da **raiz do projeto** (`agente_climatico\`).

### Etapa 1 — Coleta de Dados Meteorológicos

O agente consulta a IA para decidir autonomamente qual fonte usar, coleta os dados via API e salva o dataset.

```powershell
python scripts\01_coleta.py
```

**Saídas geradas:**
- `output\01_coleta\dados_clima.csv`
- `output\01_coleta\decisao_coleta.json`
- `runs\run_<timestamp>_coleta.json`

---

### Etapa 2 — Análise Estatística

O agente lê o CSV da etapa anterior, define um plano de análise com a IA e executa estatísticas descritivas, testes de hipótese, correlações e regressões temporais.

```powershell
python scripts\02_analise.py
```

**Saídas geradas:**
- `output\02_analise\plano_analise.json`
- `output\02_analise\analise_estatistica.json`
- `runs\run_<timestamp>_analise.json`

> Para usar um CSV alternativo:
> ```powershell
> python scripts\02_analise.py --arquivo_csv "caminho\para\outro.csv"
> ```

---

### Etapa 3 — Geração do Relatório

O agente lê os resultados estatísticos, decide quais gráficos gerar, redige o relatório completo e exporta para HTML executivo e Word ABNT.

```powershell
python scripts\03_relatorio.py
```

**Saídas geradas:**
- `output\03_relatorio\graficos\figura_*.png`
- `output\03_relatorio\word\relatorio_climatico.docx`
- `output\03_relatorio\html\relatorio_climatico.html`
- `output\03_relatorio\markdown\relatorio_climatico.md`
- `output\03_relatorio\planos\plano_editorial.json`
- `runs\run_<timestamp>_relatorio.json`

---

## Execução Sequencial Completa (Comando Único)

```powershell
python scripts\01_coleta.py; if ($LASTEXITCODE -eq 0) { python scripts\02_analise.py } else { Write-Error "Etapa 1 falhou." }; if ($LASTEXITCODE -eq 0) { python scripts\03_relatorio.py } else { Write-Error "Etapa 2 falhou." }
```

---

## Dependências entre Etapas

```
01_coleta.py
    └── gera → output\01_coleta\dados_clima.csv
                    │
                    ▼
            02_analise.py
                └── gera → output\02_analise\analise_estatistica.json
                                    │
                                    ▼
                            03_relatorio.py
                                └── gera → output\03_relatorio\*
```

> **Importante:** Não execute as etapas fora de ordem.
> A Etapa 2 requer o `dados_clima.csv` da Etapa 1.
> A Etapa 3 requer o `analise_estatistica.json` da Etapa 2.

---

## Logs de Execução

Cada execução gera um arquivo `run_<timestamp>_<etapa>.json` na pasta `runs\`, contendo metadados como duração, caminhos dos artefatos gerados, modelo utilizado e parâmetros de entrada.
