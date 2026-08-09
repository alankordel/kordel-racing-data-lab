# Arquitetura

## Objetivo

O projeto exercita engenharia e análise de dados com um pipeline local, reproduzível e fácil de explicar. Ele coleta dados históricos da Fórmula 1 e os transforma em tabelas analíticas.

## Fonte

A fonte é a API REST pública [OpenF1](https://openf1.org/docs/), base `https://api.openf1.org/v1`. Dados históricos desde 2023 não exigem autenticação. O plano gratuito permite até 3 requisições por segundo e 30 por minuto. O cliente respeita o limite por segundo; para não exceder o limite por minuto, o MVP consulta somente oito endpoints por execução.

O exemplo usa a corrida de Abu Dhabi de 2025 (`meeting_key=1276`, `session_key=9839`), presente nos exemplos atuais da documentação. Endpoints confirmados e usados: `sessions`, `drivers`, `laps`, `stints`, `pit`, `weather`, `position` e `session_result`. Filtros são passados como parâmetros HTTP, principalmente `session_key`.

## Fluxo

```text
OpenF1 REST -> Bronze -> Silver -> Data Quality -> Gold -> Streamlit
```

- **Bronze:** um Parquet por endpoint e `metadata.json` com consulta, horário, contagem e status. O pipeline usa JSON como
  fallback quando um campo mistura tipos incompatíveis com Parquet (por exemplo, `gap_to_leader` numérico e `"+1 LAP"`).
- **Silver:** nomes em snake_case, strings limpas, datas UTC, durações numéricas e duplicados removidos.
- **Data Quality:** aplica o contrato de `laps`, gera relatório JSON e interrompe a Gold quando encontra erros críticos.
- **Gold:** desempenho por volta, resumo da sessão, análise de stints e pit stops.
- **Consumo:** dashboard lê somente os arquivos Gold; não chama a API.

## Decisões técnicas

- Python, pandas e Parquet mantêm a solução portátil e familiar.
- YAML centraliza sessão, endpoints, timeouts e diretório.
- Falha em um endpoint fica registrada sem perder datasets já coletados.
- Warnings de qualidade são observáveis, mas não bloqueiam; erros estruturais, de tipo, domínio ou chave bloqueiam a Gold.
- Não há banco, orquestrador ou cloud obrigatórios neste MVP.
- Dados gerados não são versionados.

## Limitações

A OpenF1 é uma fonte não oficial. Campos podem mudar e alguns não existem em sessões antigas. A regressão de degradação não controla combustível, tráfego, bandeiras ou temperatura. Voltas sem duração são excluídas das métricas. O controle de taxa é local a um processo.

## Próximos passos

Adicionar contratos para os demais endpoints, validações entre datasets, testes de integração opt-in, particionamento
por temporada e adaptação opcional para Spark/Databricks.
