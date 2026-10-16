# Agente Climático — Pipeline Autônomo de Análise Meteorológica

Pipeline de ponta a ponta que **coleta dados climáticos reais via API**, executa uma
**análise estatística completa** e **redige um relatório técnico-científico** (HTML
executivo + Word padrão ABNT), com gráficos gerados automaticamente.

O diferencial do projeto é que, em **cada etapa, um agente de IA decide sozinho** o que
fazer (qual fonte de dados usar, quais variáveis coletar, qual plano estatístico aplicar
e como redigir o relatório). O **Python é apenas o "braço técnico"**, que executa a
decisão da IA de forma determinística e reproduzível.

> **Motor de IA — leia isto primeiro**
>
> O projeto foi originalmente construído com o **Antigravity CLI** (binário `agy`, modelo
> **Gemini**), por ter maior capacidade. Como o Antigravity ficou **sem tokens**, a rodagem
> atual é feita **100% com o [OpenCode](https://opencode.ai)**, usando o provider do próprio
> agente. É por isso que existem os scripts `001/002/003` (OpenCode, atuais) — o Antigravity
> segue documentado no fim deste README apenas como **referência do motor original**.

---

## Índice

1. [Como funciona a arquitetura](#1-como-funciona-a-arquitetura)
2. [Ferramentas necessárias (instalação passo a passo)](#2-ferramentas-necessárias-instalação-passo-a-passo)
3. [Como chamar o agente no terminal](#3-como-chamar-o-agente-no-terminal)
4. [Estrutura do projeto](#4-estrutura-do-projeto)
5. [Configuração](#5-configuração)
6. [Execução do pipeline](#6-execução-do-pipeline)
7. [Saídas geradas](#7-saídas-geradas)
8. [Solução de problemas](#8-solução-de-problemas)

---

## 1. Como funciona a arquitetura

Cada etapa é dividida em dois planos:

- **Control Plane (a IA decide):** um *prompt* em Markdown (`prompts/`) é enviado ao OpenCode.
  A IA devolve um **plano estruturado em JSON** (fonte escolhida, variáveis, estratégia
  estatística, plano editorial etc.).
- **Data Plane (o Python executa):** o script lê esse JSON e roda as ferramentas concretas
  (requisições HTTP, cálculos `numpy`/`scipy`, geração de gráficos, exportação).

O fluxo completo é encadeado — a saída de uma etapa é a entrada da próxima:

```
scripts/001_coleta.py
        │  IA decide: melhor fonte + variáveis
        ▼
   output/01_coleta/dados_clima.csv
        │
        ▼
scripts/002_analise.py
        │  IA decide: plano estatístico (testes, correlações, regressões)
        ▼
   output/02_analise/analise_estatistica.json
        │
        ▼
scripts/003_relatorio.py
        │  IA decide: plano editorial + redige o texto técnico
        ▼
   output/03_relatorio/  →  HTML executivo + Word ABNT + gráficos PNG
```

Cada execução também grava um **log de auditoria** em `runs/run_<timestamp>_<etapa>.json`
com os parâmetros usados, a decisão da IA e os artefatos produzidos.

---

## 2. Ferramentas necessárias (instalação passo a passo)

Você só precisa de **três** coisas para rodar o projeto: um editor (opcional), o
**OpenCode** (o cérebro) e o **Python** (o motor). Siga na ordem.

### 2.1 VS Code — editor de código (recomendado, opcional)

Não é obrigatório para executar, mas facilita abrir/editar os arquivos.

- **Site oficial:** https://code.visualstudio.com/
- **Windows (winget):**
  ```powershell
  winget install Microsoft.VisualStudioCode
  ```
- **Extensão do OpenCode no VS Code:** abra a aba *Extensions* (`Ctrl+Shift+X`), procure
  por **OpenCode** e clique em *Install*. (Opcional — o pipeline funciona sem ela.)

### 2.2 OpenCode — o motor de IA oficial do projeto

- **Site / documentação:** https://opencode.ai  — docs do CLI: https://opencode.ai/docs/cli

**Instalação (escolha UMA):**

- **Via npm (mais simples no Windows):**
  ```powershell
  npm install -g opencode-ai
  ```
- **Script oficial (macOS/Linux/WSL):**
  ```bash
  curl -fsSL https://opencode.ai/install | bash
  ```
- **Windows (Chocolatey):**
  ```powershell
  choco install opencode
  ```
- **Windows (Scoop):**
  ```powershell
  scoop install opencode
  ```

> No Windows, o instalador via npm coloca o executável em:
> `%APPDATA%\npm\node_modules\opencode-ai\bin\opencode.exe`
> Os scripts do projeto apontam exatamente para esse caminho.

**Autenticar / configurar o provider (obrigatório antes de rodar):**

```powershell
opencode auth login
```

Siga as instruções na tela para conectar sua conta/API key do provider. As credenciais
ficam salvas no seu perfil (não vão para o repositório).

**Verificar a instalação:**

```powershell
opencode --version
```

### 2.3 Python 3.10 ou superior

- **Site oficial:** https://www.python.org/downloads/ (no Windows, marque
  *"Add python.exe to PATH"* durante a instalação).

**Instale as dependências do projeto** (a partir da raiz `agente_climatico\`):

```powershell
pip install pandas requests scipy numpy matplotlib python-docx markdown
```

### 2.4 Antigravity (motor original — apenas referência)

O projeto **não usa mais** o Antigravity, mas ele foi o motor original. Se quiser
reproduzir a versão antiga, o CLI (`agy`) instala assim:

- **Download / docs:** https://antigravity.google/download
- **Windows (PowerShell):**
  ```powershell
  irm https://antigravity.google/cli/install.ps1 | iex
  ```
- **Windows (CMD):**
  ```cmd
  curl -fsSL https://antigravity.google/cli/install.cmd -o install.cmd && install.cmd && del install.cmd
  ```
- **macOS / Linux:**
  ```bash
  curl -fsSL https://antigravity.google/cli/install.sh | bash
  ```

O binário fica em `%LOCALAPPDATA%\agy\bin\agy.exe`. Antes de usar o CLI, é preciso
autenticar no **Antigravity** ou no **Antigravity IDE**.

---

## 3. Como chamar o agente no terminal

Com o **OpenCode** instalado e autenticado (`opencode auth login`), você pode conversar
com o agente de duas formas:

**Modo interativo (TUI) — para uso manual:**

```powershell
opencode
```

**Modo não-interativo — é o que os scripts usam por baixo dos panos:**

```powershell
opencode run --model opencode/deepseek-v4.1-flash-free "sua pergunta aqui"
```

Os três scripts chamam o OpenCode exatamente assim, passando o prompt da etapa e pedindo
uma resposta em JSON. Exemplo de chamada equivalente à Etapa 1:

```powershell
opencode run --model opencode/deepseek-v4.1-flash-free "Você é um agente de coleta meteorológica..."
```

> **Dica:** você pode abrir o projeto já dentro da TUI do OpenCode (com `opencode` na raiz
> do projeto) e pedir ajuda para rodar/ajustar o pipeline manualmente.

---

## 4. Estrutura do projeto

```
agente_climatico/
│
├── README.md                          # Este arquivo
├── .gitignore
│
├── input/
│   └── fontes.json                    # Catálogo de fontes de dados (Open-Meteo, wttr.in, Wikipedia)
│
├── prompts/                           # "Cérebros" de cada agente (enviados ao OpenCode)
│   ├── 01_prompt_coleta.md            # Agente 1 — decisão autônoma de fonte e variáveis
│   ├── 02_prompt_analise.md           # Agente 2 — plano estatístico
│   └── 03_prompt_relatorio.md         # Agente 3 — plano editorial e redação
│
├── scripts/                           # Scripts Python de cada agente (motor oficial: OpenCode)
│   ├── 001_coleta.py
│   ├── 002_analise.py
│   └── 003_relatorio.py
│
├── runs/                              # Logs de execução (gerados automaticamente)
│   └── run_<timestamp>_<etapa>.json
│
└── output/                            # Artefatos produzidos (exemplos já incluídos)
    ├── 01_coleta/
    │   ├── dados_clima.csv            # Dataset meteorológico coletado
    │   └── decisao_coleta.json        # Decisão estruturada da IA sobre a fonte usada
    ├── 02_analise/
    │   ├── plano_analise.json         # Plano estatístico decidido pela IA
    │   └── analise_estatistica.json   # Resultados completos da análise
    └── 03_relatorio/
        ├── graficos/                  # Figuras PNG geradas pelo motor Python
        ├── word/                      # Relatório Word (padrão ABNT)
        ├── html/                      # Relatório HTML executivo
        ├── markdown/                  # Texto bruto do relatório
        └── planos/                    # Plano editorial decidido pela IA
```

---

## 5. Configuração

As constantes ficam no topo de cada script e quase nunca precisam ser alteradas:

| Configuração       | Onde                              | Valor padrão |
|--------------------|-----------------------------------|--------------|
| Caminho do OpenCode| `OPEN_CODE` em cada `00X_*.py`    | `%APPDATA%\npm\node_modules\opencode-ai\bin\opencode.exe` |
| Modelo da IA       | `MODELO_PADRAO` em cada `00X_*.py`| `opencode/deepseek-v4.1-flash-free` |
| Fontes disponíveis | `input/fontes.json`               | Open-Meteo, wttr.in, Wikipedia |

> **Se o OpenCode estiver instalado em outro lugar** (ex.: via Scoop/Chocolatey), edite a
> constante `OPEN_CODE` / `OPEN_CODE` no topo do script para o caminho correto do
> `opencode.exe`. O mesmo vale para trocar o modelo de IA.

---

## 6. Execução do pipeline

Execute os três scripts **na ordem**, sempre a partir da **raiz do projeto**
(`agente_climatico\`). Não pule etapas: cada uma depende dos arquivos gerados pela anterior.

### Etapa 1 — Coleta de dados meteorológicos

A IA decide qual fonte usar e quais variáveis coletar; o Python consulta a API e salva o CSV.

```powershell
python scripts\001_coleta.py --cidade "São Paulo" --dias 3
```

Argumentos:

| Argumento  | Descrição                                  | Padrão |
|------------|--------------------------------------------|--------|
| `--cidade` | Cidade alvo da coleta                      | `São Paulo` |
| `--dias`   | Quantidade de dias históricos recentes     | `3` |
| `--model`  | Modelo do OpenCode a usar                  | `opencode/deepseek-v4.1-flash-free` |

### Etapa 2 — Análise estatística

A IA define o plano estatístico; o Python executa estatísticas descritivas, testes de
hipótese, correlações e regressões temporais.

```powershell
python scripts\002_analise.py
```

Para usar outro CSV:

```powershell
python scripts\002_analise.py --arquivo_csv "caminho\para\outro.csv"
```

### Etapa 3 — Geração do relatório

A IA decide os gráficos e redige o texto; o Python exporta HTML executivo e Word ABNT.

```powershell
python scripts\003_relatorio.py
```

### Execução completa em um único comando

```powershell
python scripts\001_coleta.py; if ($LASTEXITCODE -eq 0) { python scripts\002_analise.py }; if ($LASTEXITCODE -eq 0) { python scripts\003_relatorio.py }
```

---

## 7. Saídas geradas

| Arquivo                                        | Descrição |
|------------------------------------------------|-----------|
| `output/01_coleta/dados_clima.csv`             | Dataset meteorológico coletado |
| `output/01_coleta/decisao_coleta.json`         | Decisão da IA (fonte + variáveis) |
| `output/02_analise/plano_analise.json`         | Plano estatístico da IA |
| `output/02_analise/analise_estatistica.json`   | Resultados completos da análise |
| `output/03_relatorio/graficos/*.png`           | Figuras geradas |
| `output/03_relatorio/word/relatorio_climatico.docx` | Relatório Word (ABNT) |
| `output/03_relatorio/html/relatorio_climatico.html` | Relatório HTML executivo |
| `output/03_relatorio/markdown/relatorio_climatico.md` | Relatório em Markdown |
| `output/03_relatorio/planos/plano_editorial.json` | Plano editorial da IA |
| `runs/run_<timestamp>_<etapa>.json`            | Log de auditoria de cada execução |

As pastas `output/` e `runs/` já vêm com **exemplos de execuções anteriores**.

---

## 8. Solução de problemas

- **`Executável OpenCode não encontrado em: ...`**
  O OpenCode não está no caminho esperado. Rode `npm install -g opencode-ai` ou ajuste a
  constante `OPEN_CODE` no topo do script para o caminho do seu `opencode.exe`.

- **Resposta vazia / erro de autenticação do OpenCode**
  Rode `opencode auth login` e confirme que o provider está configurado. Teste com
  `opencode run --model opencode/deepseek-v4.1-flash-free "diga olá"`.

- **`ModuleNotFoundError: No module named '...'`**
  Instale as dependências: `pip install pandas requests scipy numpy matplotlib python-docx markdown`.

- **Etapa 2 falha dizendo que o CSV não existe**
  A Etapa 1 precisa rodar antes (ela gera `output/01_coleta/dados_clima.csv`).

- **Etapa 3 falha dizendo que `analise_estatistica.json` não existe**
  A Etapa 2 precisa rodar antes.

---

## Créditos

Projeto desenvolvido como pipeline de **agentes autônomos** aplicados à análise
meteorológica. Motor original: **Antigravity (Gemini)**. Motor atual: **OpenCode**.
