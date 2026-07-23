# Dicionário de dados

As colunas podem ser nulas quando a fonte não as disponibiliza.

## Bronze

Cada arquivo preserva as colunas do endpoint OpenF1. `metadata.json` registra `endpoint`, `params`, `extracted_at_utc`, `records`, `status` e `file`.

## Silver

| Tabela | Colunas principais |
|---|---|
| `drivers` | `session_key`, `driver_number`, `full_name`, `team_name` |
| `sessions` | `meeting_key`, `session_key`, `session_name`, `date_start`, `date_end` |
| `laps` | `session_key`, `driver_number`, `lap_number`, `lap_duration_seconds`, setores |
| `stints` | `driver_number`, `stint_number`, `lap_start`, `lap_end`, `compound`, `tyre_age_at_start` |
| `pit_stops` | `driver_number`, `lap_number`, `pit_duration_seconds`, `stop_duration` |
| `weather` | `date`, `air_temperature`, `track_temperature`, `rainfall` |
| `race_results` | `driver_number`, `position`, `points`, `dnf`, `dns`, `dsq` |

## Gold

| Tabela | Finalidade e principais colunas |
|---|---|
| `driver_lap_performance` | Grão piloto/volta; nomes, equipe, tempo e validade |
| `driver_session_summary` | Melhor, média, mediana, desvio-padrão, pits, posição final e compostos |
| `tyre_stint_analysis` | Extensão, melhor/média e inclinação linear do tempo por volta |
| `pit_stop_analysis` | Duração de cada passagem/ parada, piloto e equipe |

`consistency_std` é o desvio-padrão amostral: menor valor indica tempos mais próximos. `degradation_per_lap` é a inclinação da regressão linear do tempo contra o número da volta; valores positivos indicam aumento de tempo, sem afirmar causalidade.

