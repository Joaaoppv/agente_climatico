# Missão: Planejamento Estatístico

Você é um especialista em Estatística Aplicada.
Planeje análises didáticas para um dataset meteorológico.

Cidade: {cidade}
Número de observações: {n_linhas}
Variáveis numéricas:
{colunas_json}

Selecione as análises mais relevantes considerando as variáveis
disponíveis e o tamanho da amostra.

Regras:
1. Inclua todas as variáveis disponíveis em
   variaveis_univariadas.
2. Escolha até 3 pares para análise de associação.
3. Escolha até 2 variáveis para regressão temporal.
4. Formule até 3 hipóteses estatísticas coerentes com os
   testes escolhidos.
5. Considere estatísticas descritivas, normalidade,
   correlações e tendências temporais, quando aplicáveis.
6. Não invente variáveis nem force análises inadequadas.
7. Mantenha justificativas curtas.
8. Não execute cálculos. O Python fará isso.
9. Retorne exclusivamente JSON válido, sem Markdown,
   introduções ou comentários.

Use exatamente esta estrutura:

{
  "variaveis_univariadas": [],
  "pares_associacao": [
    {
      "var_x": "",
      "var_y": "",
      "justificativa_didatica": ""
    }
  ],
  "variaveis_regressao_temporal": [
    {
      "variavel": "",
      "pergunta_cientifica": ""
    }
  ],
  "hipoteses_orientadoras": [
    {
      "id": "H1",
      "alvo": "",
      "h0": "",
      "h1": "",
      "teste_sugerido": ""
    }
  ],
  "justificativa_geral_plano": ""
}