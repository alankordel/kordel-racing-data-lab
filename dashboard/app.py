"""Dashboard local das tabelas Gold."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Kordel Racing Data Lab", page_icon="🏁", layout="wide")

st.title("🏁 Kordel Racing Data Lab")
st.subheader("Análise de desempenho e estratégia com dados da OpenF1")
st.caption(
    "Dados históricos processados localmente nas camadas Bronze, Silver e Gold, "
    "com validações de qualidade antes das métricas analíticas."
)

gold_root = Path("data/gold")
sessions = sorted(gold_root.glob("session_*"))
if not sessions:
    st.info("Nenhum dado Gold encontrado. Execute `python main.py` antes de abrir o dashboard.")
    st.stop()

st.sidebar.header("Filtros")
selected = st.sidebar.selectbox("Sessão", sessions, format_func=lambda path: path.name)


def read_table(name: str) -> pd.DataFrame:
    path = selected / f"{name}.parquet"
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


laps = read_table("driver_lap_performance")
summary = read_table("driver_session_summary")
tyres = read_table("tyre_stint_analysis")
pits = read_table("pit_stop_analysis")

if laps.empty:
    st.warning("A tabela de voltas está vazia para esta sessão. Execute novamente o pipeline.")
    st.stop()

teams = sorted(laps["team_name"].dropna().unique()) if "team_name" in laps else []
chosen_teams = st.sidebar.multiselect("Equipes", teams)
available_laps = laps[laps["team_name"].isin(chosen_teams)] if chosen_teams else laps
drivers = sorted(available_laps["driver_name"].dropna().unique())
default_drivers = drivers[: min(3, len(drivers))]
chosen_drivers = st.sidebar.multiselect("Pilotos", drivers, default=default_drivers)
filtered = available_laps[available_laps["driver_name"].isin(chosen_drivers)] if chosen_drivers else available_laps

selected_names = filtered["driver_name"].dropna().unique()
filtered_summary = summary[summary["driver_name"].isin(selected_names)] if not summary.empty else summary
filtered_tyres = tyres[tyres["driver_name"].isin(selected_names)] if not tyres.empty else tyres
filtered_pits = pits[pits["driver_name"].isin(selected_names)] if not pits.empty else pits

st.divider()
st.header("Visão geral da sessão")

valid_laps = filtered[filtered["is_valid_lap"]]
best_row = valid_laps.loc[valid_laps["lap_duration_seconds"].idxmin()] if not valid_laps.empty else None
consistent_row = (
    filtered_summary.dropna(subset=["consistency_std"]).sort_values("consistency_std").iloc[0]
    if not filtered_summary.empty and filtered_summary["consistency_std"].notna().any()
    else None
)
average_pits = filtered_summary["total_pit_stops"].fillna(0).mean() if "total_pit_stops" in filtered_summary else None

kpis = st.columns(3)
kpis[0].metric("Piloto com melhor volta", best_row["driver_name"] if best_row is not None else "—")
kpis[1].metric("Melhor tempo", f"{best_row['lap_duration_seconds']:.3f} s" if best_row is not None else "—")
kpis[2].metric("Piloto mais consistente", consistent_row["driver_name"] if consistent_row is not None else "—")

kpis = st.columns(3)
kpis[0].metric("Voltas válidas", int(valid_laps.shape[0]))
kpis[1].metric("Média de pit stops", f"{average_pits:.1f}" if pd.notna(average_pits) else "—")
kpis[2].metric("Pilotos selecionados", filtered["driver_number"].nunique())

st.divider()
st.header("Ritmo e consistência")
st.caption("Compare a evolução dos tempos por volta e a dispersão de cada piloto.")

pace_chart, consistency_chart = st.columns((2, 1))
with pace_chart:
    st.plotly_chart(
        px.line(
            filtered,
            x="lap_number",
            y="lap_duration_seconds",
            color="driver_name",
            markers=True,
            labels={
                "lap_number": "Volta",
                "lap_duration_seconds": "Tempo (s)",
                "driver_name": "Piloto",
            },
        ),
        use_container_width=True,
    )
with consistency_chart:
    if filtered_summary.empty:
        st.info("Resumo de consistência indisponível.")
    else:
        st.plotly_chart(
            px.bar(
                filtered_summary.sort_values("consistency_std"),
                x="driver_name",
                y="consistency_std",
                color="team_name",
                labels={
                    "driver_name": "Piloto",
                    "consistency_std": "Desvio-padrão (s)",
                    "team_name": "Equipe",
                },
            ),
            use_container_width=True,
        )

st.subheader("Melhores voltas")
if filtered_summary.empty:
    st.info("Resumo de voltas indisponível.")
else:
    columns = [
        column
        for column in (
            "driver_name",
            "team_name",
            "best_lap",
            "average_lap",
            "consistency_std",
            "final_position",
        )
        if column in filtered_summary
    ]
    st.dataframe(filtered_summary.sort_values("best_lap")[columns], use_container_width=True, hide_index=True)

st.divider()
st.header("Estratégia")
tyre_tab, pit_tab = st.tabs(["Pneus", "Pit stops"])

with tyre_tab:
    st.caption("A degradação é a inclinação linear do tempo por volta em cada stint.")
    if filtered_tyres.empty:
        st.info("Não há stints suficientes para esta análise.")
    else:
        st.plotly_chart(
            px.scatter(
                filtered_tyres,
                x="stint_length",
                y="degradation_per_lap",
                color="compound",
                hover_name="driver_name",
                size="stint_length",
                labels={
                    "stint_length": "Extensão do stint",
                    "degradation_per_lap": "Degradação por volta (s)",
                    "compound": "Composto",
                },
            ),
            use_container_width=True,
        )

with pit_tab:
    if filtered_pits.empty:
        st.info("Não há dados de pit stops para esta sessão.")
    else:
        duration = "stop_duration" if "stop_duration" in filtered_pits else "pit_duration_seconds"
        st.plotly_chart(
            px.box(
                filtered_pits,
                x="driver_name",
                y=duration,
                color="team_name",
                points="all",
                labels={"driver_name": "Piloto", duration: "Duração (s)", "team_name": "Equipe"},
            ),
            use_container_width=True,
        )

st.warning(
    "As métricas são descritivas. Tráfego, combustível, clima, bandeiras e diferenças de estratégia "
    "podem afetar os resultados; as visualizações não demonstram causalidade."
)
