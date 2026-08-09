# Qualidade de dados

## O que é um contrato de dados

Um contrato de dados descreve a estrutura e as regras mínimas que um dataset precisa cumprir para ser consumido com
segurança. Ele torna explícitas expectativas que, sem validação, ficariam espalhadas pelo código ou dependeriam apenas
do comportamento atual da fonte.

O primeiro contrato do projeto cobre a tabela Silver `laps`. A OpenF1 é uma API externa e não oficial; por isso, o
contrato ajuda a identificar mudanças de schema e valores que tornariam as métricas Gold incorretas.

## Posição no pipeline

```text
OpenF1 -> Bronze -> Silver -> Data Quality -> Gold -> Streamlit
```

A validação ocorre depois da padronização Silver e antes das agregações Gold. O pipeline sempre salva o relatório JSON
antes de decidir se pode continuar.

## Contrato de `laps`

| Categoria | Regra |
|---|---|
| Colunas obrigatórias | `session_key`, `driver_number`, `lap_number`, `lap_duration` |
| Chave lógica | `session_key + driver_number + lap_number` |
| Não nulos | `session_key`, `driver_number`, `lap_number` |
| Tipos | As quatro colunas do contrato devem ser numéricas quando preenchidas |
| Domínio | Chaves e número da volta maiores que zero; duração positiva e finita |
| Unicidade | Não pode haver duas linhas com a mesma chave lógica |

`lap_duration` pode ser nula. A OpenF1 pode não informar duração para voltas incompletas, de saída dos boxes ou sem
cronometragem válida. Esses casos geram aviso e não são usados nas métricas de tempo.

Colunas extras são permitidas para que a evolução aditiva do schema da API não interrompa o pipeline.

## Severidades

- **ERROR:** violação estrutural, chave nula, tipo incompatível, domínio inválido ou chave duplicada. A camada Gold não é
  criada para aquela execução.
- **WARNING:** condição aceitável que merece acompanhamento, como dataset vazio ou duração nula. O pipeline pode seguir.

Quando há `ERROR`, o pipeline lança `DataQualityError` com uma mensagem compreensível e o caminho do relatório. Dataset
vazio é tratado como `WARNING` para preservar o comportamento tolerante já existente quando um endpoint não retorna
registros.

## Relatório JSON

Os relatórios são gerados em `data/quality/laps_quality_<session_key>.json` e contêm:

- dataset, sessão, horário e status final;
- total de linhas válidas e inválidas;
- quantidades de erros e avisos;
- resultado de cada regra (`PASS`, `ERROR`, `WARNING` ou `NOT_EVALUATED`);
- regra, mensagem, linhas afetadas e até cinco registros de exemplo para cada ocorrência.

Arquivos gerados em `data/quality/` não são versionados. Apenas a pasta vazia é mantida no Git.

## Limitações e evolução

O contrato atual valida uma tabela isolada e não verifica relações com pilotos, sessões ou stints. As regras de domínio
são intencionalmente conservadoras para não rejeitar situações legítimas de corrida.

Os próximos contratos planejados são `drivers`, `stints`, `pit_stops`, `weather` e `race_results`. Depois deles, poderão
ser adicionadas validações entre datasets, como pilotos de `laps` existentes em `drivers`.
