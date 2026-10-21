# Agente Climático — Pipeline Autônomo de Análise Meteorológica

> **Só quer instalar uma IA no terminal?**
> Vá direto para a [seção 0](#0-ia-no-terminal--instale-e-use-sua-ia-comece-aqui). Ela
> ensina a instalar e conversar com OpenCode (DeepSeek), Claude Code e Antigravity de
> forma **independente** — você não precisa clonar nem entender este projeto.
>
> **Quer entender ou rodar este projeto?** Continue na seção 1.

Pipeline de ponta a ponta que **coleta dados climáticos reais via API**, executa uma
**análise estatística completa** e **redige um relatório técnico-científico** (HTML
executivo + Word padrão ABNT), com gráficos gerados automaticamente.

O diferencial do projeto é que, em **cada etapa, um agente de IA decide sozinho** o que
fazer (qual fonte de dados usar, quais variáveis coletar, qual plano estatístico aplicar
e como redigir o relatório). O **Python é apenas o "braço técnico"**, que executa a
decisão da IA de forma determinística e reproduzível.

---

## Índice

0. [IA no terminal — instale e use sua IA (comece aqui)](#0-ia-no-terminal--instale-e-use-sua-ia-comece-aqui)
1. [Como funciona a arquitetura](#1-como-funciona-a-arquitetura)
2. [Dependências do projeto](#2-dependências-do-projeto)
3. [Estrutura do projeto](#3-estrutura-do-projeto)
4. [Configuração](#4-configuração)
5. [Execução do pipeline](#5-execução-do-pipeline)
6. [Saídas geradas](#6-saídas-geradas)
7. [Solução de problemas](#7-solução-de-problemas)

---

## 0. IA no terminal — instale e use sua IA (comece aqui)

Esta seção é **independente do projeto**. Ela ensina apenas a instalar uma IA no terminal
do VS Code e conversar com ela para estudar, escrever código, rodar Python, criar projetos
etc. Se é só isso que você quer, **pare aqui** — não precisa do restante do README.

### Qual escolher?

| Ferramenta | Modelo | Custo | Seção |
|------------|--------|-------|-------|
| **OpenCode** | DeepSeek | grátis (modelo free, com limites) | 0.2 |
| **Claude Code** | Anthropic | plano pago (o gratuito não inclui) | 0.3 |
| **Antigravity** (`agy`) | Gemini (Google) | conta Google, com limites | 0.4 |

Escolha **uma** ferramenta e siga só a seção dela; todas usam o mesmo terminal.

### 0.1 Pré-requisitos (Windows)

**Passo 1 — abrir o PowerShell**
Se você já tem o VS Code, pode usar o terminal dele. Se ainda não tem, abra o PowerShell
do Windows: tecle `Win`, digite **PowerShell** e pressione Enter (ou `Win+X` → *Terminal*).

**Passo 2 — instalar o VS Code**
- Site oficial: https://code.visualstudio.com/
- Instalação por comando:
  ```powershell
  winget install Microsoft.VisualStudioCode
  ```

**Passo 3 — instalar o Node.js LTS** (necessário para o OpenCode; pule se for usar só
Claude Code ou Antigravity)
- Site oficial: https://nodejs.org/
- Instalação por comando:
  ```powershell
  winget install OpenJS.NodeJS.LTS
  ```

> Se `winget` não for reconhecido, baixe os instaladores pelos sites oficiais acima e
> instale manualmente. Na primeira vez, o `winget` pode pedir para aceitar os termos de
> origem — digite `Y` e pressione Enter.

**Passo 4 — abrir o terminal do VS Code**
Abra o VS Code (se ele já estava aberto, feche e reabra) e abra um terminal novo com
`` Ctrl+` `` (ou *Terminal → New Terminal*) — é a faixa que aparece na parte de baixo da
janela. Ele deve estar em **PowerShell** (no Windows é o padrão); se estiver em CMD ou Git
Bash, clique na seta ao lado do `+` e escolha **PowerShell**. Todos os comandos deste guia
(blocos `powershell`) rodam nesse terminal, **um de cada vez**.

**Passo 5 — conferir a instalação** (só se você instalou o Node)
```powershell
node -v
npm -v
```
`node -v` mostra algo como `v24.x.x` e `npm -v` mostra `11.x.x`. Se aparecerem as versões,
está pronto. Se der "não reconhecido", feche e reabra o terminal; persistindo, reinstale o
Node.js. Se você pulou o Node (Claude Code ou Antigravity), siga direto para a sua seção.

> Se o PowerShell bloquear algum comando (por exemplo, `npm.ps1`) com erro de política de
> execução, rode `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, confirme com `S` e
> tente de novo.

### 0.2 OpenCode — modelos DeepSeek (grátis)

> **Antes de começar:** Node.js instalado (seção 0.1).

Abra um terminal novo no VS Code (`` Ctrl+` `` ou *Terminal → New Terminal*), confirme que
está em **PowerShell** e rode os passos abaixo **um de cada vez**. O uso é todo pela
**interface que abre no terminal**; você não precisa decorar comandos.

**Passo 1 — instalar**
```powershell
npm install -g opencode-ai
```
O terminal mostra os pacotes sendo baixados e termina sem erro.

**Passo 2 — conferir a instalação**
```powershell
opencode --version
```
Deve aparecer o número da versão. Se der "não reconhecido", feche e reabra o terminal.

**Passo 3 — entrar na sua conta**
```powershell
opencode auth login
```
Aparece uma **lista de providers**. Para o modelo gratuito, escolha **OpenCode Zen**
(`opencode`) com as setas `↑`/`↓` e Enter; autorize no navegador se pedir. Se aparecer um
campo de **API key**, crie a conta em https://opencode.ai/auth, copie a chave e cole no
terminal. No fim, o terminal confirma que a credencial foi salva e você volta ao shell.

**Passo 4 — abrir a interface**
```powershell
opencode
```
A tela do OpenCode ocupa o terminal e mostra uma **caixa de texto na parte de baixo**.
Digite sua pergunta e pressione Enter; a resposta aparece acima, aos poucos. Para usar o
modelo DeepSeek gratuito, digite `/models` e escolha **deepseek-v4.1-flash-free** (se ele
não aparecer, escolha outro modelo disponível na lista; o gratuito pode ter limites de
uso). Para sair: `/exit` ou `Ctrl+C`.

> Outras formas de instalar (Scoop, Chocolatey, macOS/Linux): https://opencode.ai/docs/cli

### 0.3 Claude Code — para quem tem plano pago

> **Antes de começar:** conta **Claude paga** (Pro, Max, Team, Enterprise ou Console) — o
> plano gratuito **não** inclui o Claude Code. O **Git** no Windows é opcional: se quiser
> o Bash tool, instale com `winget install Git.Git` ou em https://git-scm.com/download/win.

Abra um terminal novo no VS Code (`` Ctrl+` `` ou *Terminal → New Terminal*), confirme que
está em **PowerShell** e rode os passos abaixo **um de cada vez**. O uso é todo pela
**interface que abre no terminal**.

**Passo 1 — instalar**
```powershell
irm https://claude.ai/install.ps1 | iex
```
O instalador baixa o Claude Code sem mostrar progresso — aguarde terminar.

**Passo 2 — conferir a instalação**
Feche e reabra o terminal (para atualizar o PATH) e rode:
```powershell
claude --version
```
Deve aparecer a versão, algo como `2.x.x (Claude Code)`. Se der "não reconhecido", feche e
reabra o terminal.

**Passo 3 — abrir e fazer login**
```powershell
claude
```
Na primeira vez, escolha o tema e depois **Claude account** (assinatura Pro/Max). O
navegador abre para você autorizar; ao voltar ao terminal, a interface já estará pronta,
com uma caixa de texto na parte de baixo.

> Prefira sempre o login pela conta no navegador. A opção **API key** existe, mas exige
> gerar a chave no painel da Anthropic — é mais trabalho e só vale para quem usa créditos
> de API.

**Passo 4 — conversar**
Digite sua pergunta e pressione Enter; a resposta aparece na própria interface. Para sair:
`/exit` ou `Ctrl+D`.

> O Claude Code usa apenas modelos da Anthropic — ele **não** acessa os modelos DeepSeek
> do OpenCode. São ferramentas independentes.

### 0.4 Antigravity (`agy`) — Gemini (Google)

Abra um terminal novo no VS Code (`` Ctrl+` `` ou *Terminal → New Terminal*), confirme que
está em **PowerShell** e rode os passos abaixo **um de cada vez**. O uso é todo pela
**interface que abre no terminal**.

**Passo 1 — instalar**
```powershell
irm https://antigravity.google/cli/install.ps1 | iex
```
O PowerShell baixa e instala o CLI. O binário fica em `%LOCALAPPDATA%\agy\bin\agy.exe`.

**Passo 2 — abrir e autenticar**
```powershell
agy
```
Na primeira vez, autentique-se com sua conta **Google** quando solicitado (pode abrir o
navegador ou pedir login no Antigravity IDE). Depois a interface aparece no terminal, com
uma caixa de texto para conversar. Se `agy` não for reconhecido, feche e reabra o terminal.

**Passo 3 — conversar**
Digite sua pergunta e pressione Enter. Para sair: `Ctrl+C`.

> Download/documentação: https://antigravity.google/download
> Foi o motor original deste projeto; hoje é apenas mais uma alternativa, sujeita aos
> limites de tokens da conta.

### 0.5 Dicas para conversar com a IA

- Escreva em português e seja específico: "crie um script Python que lê um CSV e plota um
  gráfico" funciona melhor que "me ajuda com Python".
- Cole o erro completo quando algo falhar.
- A IA pode pedir **permissão** para rodar comandos ou criar/editar arquivos — leia antes
  de aceitar.
- Peça para ela **executar** o que criou (rodar o Python, testar o script) em vez de só
  mostrar o código.
- Para a IA **ler um arquivo**, clique com o botão direito sobre ele no VS Code, escolha
  **Copy Path** (*Copiar Caminho*) e cole o caminho na conversa — ex.: "leia
  `C:\projetos\script.py` e explique o que ele faz".
- Abra a pasta onde quer trabalhar no VS Code (*File → Open Folder*) **antes** de iniciar a
  IA: ela enxerga e edita os arquivos dessa pasta.
- Para colar um texto no terminal, use `Ctrl+V` ou clique com o botão direito.
- Comandos úteis: `/help` (ajuda) e `/exit` (sair) na maioria das interfaces; no OpenCode,
  `/models` troca o modelo; `Ctrl+C` cancela uma resposta ou fecha a interface.

### 0.6 Problemas comuns

| Problema | Solução |
|----------|---------|
| `winget` não reconhecido | Baixe VS Code e Node.js pelos sites oficiais e instale manualmente. |
| `node`/`npm` não reconhecido | Feche e reabra o VS Code/terminal. Se persistir, reinstale o Node.js LTS marcando a opção de adicionar ao PATH. |
| `opencode` não reconhecido | Feche e reabra o terminal. Confira `npm config get prefix` e se essa pasta está no PATH. |
| `claude` não reconhecido | Feche e reabra o terminal; se persistir, veja https://code.claude.com/docs/en/troubleshoot-install. |
| Erro de política de execução no PowerShell | Rode `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e tente de novo. |
| Login falha no OpenCode | Rode `opencode auth login` novamente e escolha OpenCode Zen (`opencode`) ou refaça a API key em https://opencode.ai/auth. |
| Login falha no Claude | Confirme se o plano é pago (Pro/Max/Team/Enterprise/Console) e refaça o login pela conta no navegador. |
| `claude` sem Bash/Git no Windows | O Git é opcional (o Claude usa PowerShell sem ele). Para o Bash tool: `winget install Git.Git`. |

---

## 1. Como funciona a arquitetura

> **Motor de IA do pipeline:** o projeto foi originalmente construído com o **Antigravity
> CLI** (binário `agy`, modelo **Gemini**), por ter maior capacidade. Como o Antigravity
> ficou **sem tokens**, a rodagem atual é feita **100% com o
> [OpenCode](https://opencode.ai)**, usando o provider do próprio agente. É por isso que
> existem os scripts `001/002/003` (OpenCode, atuais) — o Antigravity segue documentado na
> seção 0.4 apenas como **referência do motor original**.

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

> **Como a IA é chamada:** os scripts rodam o OpenCode em modo não-interativo
> (`opencode run --model opencode/deepseek-v4.1-flash-free "..."`), passando o prompt de
> cada etapa. Instalação e login estão na seção 0.2; para conversar manualmente, rode
> `opencode` na raiz do projeto.

---

## 2. Dependências do projeto

Para rodar o pipeline você precisa de:

- **OpenCode instalado e autenticado** — passo a passo na seção 0.2. O projeto usa o
  modelo `opencode/deepseek-v4.1-flash-free`.
- **Python 3.10 ou superior** — https://www.python.org/downloads/ (no Windows, marque
  *"Add python.exe to PATH"* durante a instalação).
- **VS Code** (opcional, recomendado) — instalação na seção 0.1.

Instale as dependências Python **a partir da raiz `agente_climatico\`**:

```powershell
pip install pandas requests scipy numpy matplotlib python-docx markdown
```

> Se `pip` não for reconhecido, use `py -m pip install ...`.

---

## 3. Estrutura do projeto

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

## 4. Configuração

As constantes ficam no topo de cada script e quase nunca precisam ser alteradas:

| Configuração        | Onde                                                 | Valor padrão |
|---------------------|------------------------------------------------------|--------------|
| Caminho do OpenCode | `OPEN_CODE` em `001_coleta.py`                       | `opencode.cmd` (resolvido pelo PATH) |
| Caminho do OpenCode | `OPEN_CODE` em `002_analise.py` e `003_relatorio.py` | `%APPDATA%\npm\node_modules\opencode-ai\bin\opencode.exe` |
| Modelo da IA        | `MODELO_PADRAO` em cada `00X_*.py`                   | `opencode/deepseek-v4.1-flash-free` |
| Fontes disponíveis  | `input/fontes.json`                                  | Open-Meteo, wttr.in, Wikipedia |

> A Etapa 1 chama `opencode.cmd` (criado pela instalação via npm) e depende do PATH; as
> Etapas 2 e 3 usam o caminho absoluto da tabela. Se o OpenCode estiver em outro lugar,
> ajuste `OPEN_CODE` no topo do script correspondente. O mesmo vale para trocar o modelo.

---

## 5. Execução do pipeline

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

## 6. Saídas geradas

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

## 7. Solução de problemas

Para problemas de instalação/login das IAs (Node, PATH, PowerShell), veja a **seção 0.6**.

- **`Executável OpenCode não encontrado em: ...`** (Etapas 2 e 3)
  O caminho em `OPEN_CODE` não existe. Instale via npm (seção 0.2) ou ajuste a constante
  no topo do script para o caminho do seu `opencode.exe`.

- **`'opencode.cmd' não é reconhecido...`** (Etapa 1)
  O OpenCode não está no PATH. Rode `npm install -g opencode-ai` e reabra o terminal, ou
  ajuste `OPEN_CODE` no topo de `001_coleta.py`.

- **Resposta vazia / erro de autenticação**
  Rode `opencode auth login` e confirme o provider. Teste com
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
