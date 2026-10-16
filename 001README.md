# Agente Climático — Pipeline de Análise Meteorológica

Pipeline de três etapas para coleta de dados meteorológicos, análise estatística e geração de relatórios em Word e HTML.

## Pré-requisitos

- Python 3.10 ou superior.
- OpenCode CLI instalado e configurado.
- Dependências Python instaladas:

```powershell
pip install pandas requests scipy numpy matplotlib python-docx markdown
```

## Como executar

Execute os comandos abaixo no terminal, a partir da raiz do projeto.

### 1. Coleta de dados

```powershell
python scripts/01_coleta.py
```

### 2. Análise estatística

```powershell
python scripts/02_analise.py
```

### 3. Geração do relatório

```powershell
python scripts/03_relatorio.py
```

**Importante:** execute as etapas na ordem apresentada. Cada etapa utiliza os arquivos gerados pela anterior.

## Executar o pipeline completo

Para executar as três etapas sequencialmente no PowerShell, interrompendo em caso de erro:

```powershell
python scripts/01_coleta.py
if ($LASTEXITCODE -ne 0) { throw "Falha na etapa 1." }

python scripts/02_analise.py
if ($LASTEXITCODE -ne 0) { throw "Falha na etapa 2." }

python scripts/03_relatorio.py
if ($LASTEXITCODE -ne 0) { throw "Falha na etapa 3." }
```

## Saídas

Os arquivos são gerados automaticamente nas pastas `output/` e `runs/`, incluindo:

- Dados meteorológicos em CSV.
- Resultados da análise estatística em JSON.
- Gráficos em PNG.
- Relatório em Markdown, HTML e Word.
- Registros das execuções.