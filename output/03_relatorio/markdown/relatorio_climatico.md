# Relatório Técnico de Estatística Aplicada: Análise Microclimática de Curitiba

## 1. Introdução e Contexto Amostral

O presente relatório descreve o comportamento microclimático de Curitiba no período de 16/09/2026 a 15/10/2026, com tamanho amostral de 30 dias. O objetivo é caracterizar a distribuição das variáveis meteorológicas, avaliar associações entre pares de variáveis e testar hipóteses de normalidade, correlação e tendência temporal. A amostra cobre um intervalo sazonal restrito (transição entre inverno e primavera), de modo que os resultados descrevem exclusivamente o período observado e não permitem generalizações para outras épocas do ano ou para o clima de longo prazo.

## 2. Estatística Descritiva: Medidas de Posição e Dispersão

### 2.1. Tendência Central: Média, Mediana e Moda

A temperatura média (16,80 °C) apresenta média, mediana (17,30 °C) e moda (17,90 °C) próximas, indicando distribuição aproximadamente simétrica. Comportamento semelhante ocorre nas temperaturas máxima e mínima. Em contraste, a precipitação acumulada tem média (6,00 mm) superior à mediana (4,40 mm) e moda igual a 0,0 mm, o que sinaliza concentração de dias secos e influência de eventos chuvosos isolados. A umidade relativa média (87,03%) e a pressão à superfície (913,45 hPa) mostram valores consistentes ao longo do período.

### 2.2. Variabilidade e Dispersão: Desvio Padrão, Variância, Amplitude e IQR

A temperatura média diária tem desvio padrão de 2,69 °C e IQR de 4,18 °C. A temperatura máxima aparente é a mais dispersa (s = 4,97 °C; amplitude total de 18,9 °C), refletindo a influência de vento e umidade na sensação térmica. A precipitação apresenta alta variabilidade (s = 6,24 mm; amplitude de 27,5 mm), reforçando o caráter episódico das chuvas. A radiação solar (s = 5,99 MJ/m²), o vento (s = 4,35 km/h) e a umidade (s = 5,03%) completam o quadro de variabilidade moderada. Esses valores descrevem a dispersão amostral e não devem ser interpretados como indicadores de instabilidade meteorológica permanente.

### 2.3. Síntese dos Dados

| Variável | Média | Mediana | Moda | DP (s) | Mín | Máx | IQR | IC 95% |
|---|---|---|---|---|---|---|---|---|
| temperature_2m_max (°C) | 21,73 | 22,15 | 24,60 | 3,94 | 14,5 | 29,4 | 5,60 | [20,26; 23,20] |
| temperature_2m_min (°C) | 13,46 | 13,85 | 14,50 | 2,24 | 9,5 | 18,3 | 3,15 | [12,62; 14,29] |
| temperature_2m_mean (°C) | 16,80 | 17,30 | 17,90 | 2,69 | 11,2 | 20,7 | 4,18 | [15,79; 17,80] |
| apparent_temperature_max (°C) | 22,77 | 22,85 | 23,10 | 4,97 | 13,1 | 32,0 | 7,83 | [20,92; 24,63] |
| apparent_temperature_min (°C) | 13,11 | 13,60 | 9,00 | 3,03 | 7,5 | 18,6 | 4,58 | [11,98; 14,24] |
| precipitation_sum (mm) | 6,00 | 4,40 | 0,00 | 6,24 | 0,0 | 27,5 | 9,63 | [3,67; 8,34] |
| relative_humidity_2m_mean (%) | 87,03 | 87,50 | 88,00 | 5,03 | 76,0 | 98,0 | 6,00 | [85,15; 88,91] |
| wind_speed_10m_max (km/h) | 14,41 | 13,55 | 15,70 | 4,35 | 8,5 | 26,5 | 4,35 | [12,79; 16,04] |
| shortwave_radiation_sum (MJ/m²) | 14,23 | 13,75 | 6,90 | 5,99 | 3,55 | 24,85 | 8,26 | [11,99; 16,47] |
| surface_pressure_mean (hPa) | 913,45 | 913,65 | 914,40 | 2,86 | 909,4 | 921,0 | 3,45 | [912,38; 914,52] |

## 3. Análise de Associação e Relação entre Variáveis

### 3.1. Covariância e Coeficientes de Correlação: Pearson e Spearman

A covariância indica o sentido da variação conjunta, mas depende das unidades; a correlação de Pearson mede a intensidade linear na escala de -1 a +1, e a de Spearman avalia a associação monotônica por postos. Ambas foram calculadas para três pares, todos com 30 pares de observações. Associação estatística não comprova causalidade.

### 3.2. Interpretação dos Pares Reais

O par temperature_2m_max e apparent_temperature_max apresentou covariância de 19,21 e correlações quase perfeitas (r de Pearson = 0,9818; rho de Spearman = 0,9775; p-valor ≈ 0), ambas significativas a 5%. A radiação solar mostrou associação forte e positiva com a temperatura máxima (r = 0,7082; rho = 0,6928; p ≤ 0,00002). Já a umidade relativa apresentou correlação moderada e negativa com a temperatura média (r = -0,5869; rho = -0,5928; p ≤ 0,00065). Os três resultados são coerentes fisicamente, mas permanecem restritos ao período amostrado.

## 4. Inferência Estatística, Testes de Hipótese e Tendência Temporal

### 4.1. Intervalos de Confiança de 95% via t-Student

Os intervalos de confiança de 95% foram calculados com distribuição t-Student (29 graus de liberdade) e estão na tabela. A temperatura média situa-se entre 15,79 °C e 17,80 °C, com margem de erro de 1,01 °C. A precipitação apresenta o intervalo mais amplo (margem de 2,33 mm), reflexo de sua alta dispersão. Esses intervalos refletem a estimativa amostral e não uma previsão.

### 4.2. Teste de Normalidade de Shapiro-Wilk: H0, H1 e Veredito

A hipótese nula (H0) afirma que a variável segue distribuição normal, contra a alternativa (H1) de não normalidade. Não se rejeitou a normalidade para a maioria das variáveis (por exemplo, temperature_2m_mean: W = 0,954; p = 0,216), assim como para umidade, radiação, temperaturas máxima e mínima e pressão em nível de 5%. Rejeitou-se a normalidade para precipitation_sum (W = 0,840; p = 0,00039) e wind_speed_10m_max (W = 0,924; p = 0,035). Cabe registrar que 30 observações constituem amostra pequena, o que limita o poder do teste.

### 4.3. Regressão Linear e Modelagem de Tendência Temporal

A regressão temporal para temperature_2m_mean estimou coeficiente angular de +0,1001 °C/dia (R² = 0,107; p = 0,078), classificado como sem tendência estatisticamente significativa a 5%. Para precipitation_sum, o coeficiente foi +0,107 mm/dia (R² = 0,023; p = 0,426), também sem significância. Ambas as variações descrevem apenas flutuações do intervalo de 30 dias e não constituem evidência de tendência climática duradoura. O teste de Mann-Kendall sugerido nas hipóteses não teve resultado disponibilizado.

## 5. Conclusões e Considerações Finais

- A temperatura média diária foi de 16,80 °C, com distribuição simétrica e baixa dispersão; a precipitação mostrou-se episódica e assimétrica.
- As associações observadas foram muito forte para o par máximo real/aparente e moderada a forte para radiação, temperatura e umidade, todas significativas a 5%.
- Não se rejeitou a normalidade para a maioria das variáveis, exceto precipitação e vento; os intervalos de confiança de 95% foram estimados via t-Student.
- Nenhuma tendência temporal foi estatisticamente significativa, e o tamanho amostral (30 dias) impõe limitações claras à generalização dos resultados.