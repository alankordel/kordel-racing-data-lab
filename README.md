# Kordel Racing Data Lab

Pipeline local de dados de Fórmula 1 que consome a API pública OpenF1, organiza dados nas camadas Bronze, Silver e Gold e apresenta análises em um dashboard Streamlit.

## Arquitetura e tecnologias

```text
OpenF1 -> Bronze/Parquet -> Silver/Parquet -> Gold/Parquet -> Streamlit + Plotly
```

Python 3.12+, requests, pandas, PyArrow, YAML, pytest, Ruff, Streamlit e Plotly. A arquitetura completa e suas limitações estão em [docs/architecture.md](docs/architecture.md); as tabelas estão em [docs/data_dictionary.md](docs/data_dictionary.md).

## Instalação

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## Execução

O exemplo configurado é a corrida de Abu Dhabi de 2025 (`session_key=9839`):

```bash
python main.py
```

Para escolher outra sessão sem editar arquivos:

```bash
python -m kordel_racing.cli run --meeting-key 1276 --session-key 9839
```

Também é possível indicar `--output-dir` e uma lista após `--endpoints`. Configurações permanentes ficam em `config/settings.yaml`. Consulte `meetings` e `sessions` na [documentação OpenF1](https://openf1.org/docs/) para descobrir chaves válidas.

## Dashboard e qualidade

```bash
streamlit run dashboard/app.py
pytest --cov=src/kordel_racing
ruff check .
```

O dashboard não consulta a internet e orienta executar o pipeline quando não há dados.

## Saídas e análises

Os arquivos gerados ficam em `data/{bronze,silver,gold}` e não são versionados. O resumo traz melhor volta, média, mediana, consistência (desvio-padrão), total e média de pit stops, resultado final e compostos. As análises cobrem:

1. ritmo e melhores voltas entre pilotos;
2. consistência de tempos por piloto;
3. degradação descritiva de pneus por regressão linear em cada stint;
4. distribuição de duração dos pit stops.

Tráfego, combustível, bandeiras e clima podem afetar os tempos. As métricas descrevem a amostra e não provam causalidade.

### Dados de exemplo versionados

A pasta `data/samples/session_9839` contém uma execução de referência em formatos fáceis de inspecionar:

- `json/`: respostas Bronze da OpenF1 e metadados da extração;
- `csv/`: quatro tabelas analíticas Gold.

Para atualizar os exemplos após executar o pipeline:

```bash
python scripts/export_samples.py --meeting-key 1276 --session-key 9839
```

## Estrutura

```text
config/            configuração YAML
dashboard/         aplicação Streamlit
data/              camadas geradas
docs/              arquitetura e dicionário
src/kordel_racing/ cliente, transformações, métricas e CLI
tests/             testes unitários e fixtures sintéticas
.github/workflows/ integração contínua
```

## Limitações e roadmap

A OpenF1 é não oficial, disponibiliza dados históricos desde 2023 e pode alterar schemas. O MVP tolera endpoints vazios e registra falhas, mas ainda não possui contratos formais de schema. Evoluções naturais são contratos por endpoint, testes de integração opcionais, análises climáticas alinhadas no tempo e uma execução Spark/Databricks não obrigatória.

## Aprendizados

O projeto demonstra separação entre extração e transformação, idempotência por sessão, armazenamento colunar, testes sem internet, observabilidade por logs e construção de métricas com limitações explícitas.
