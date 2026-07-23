"""Dashboard local das tabelas Gold."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Kordel Racing Data Lab", layout="wide")
st.title("Kordel Racing Data Lab")
st.caption("Ritmo, consistência, pneus e pit stops a partir de dados históricos da OpenF1.")

gold_root = Path("data/gold")
sessions = sorted(gold_root.glob("session_*"))
if not sessions:
    st.info("Nenhum dado Gold encontrado. Execute `python main.py` antes de abrir o dashboard.")
    st.stop()

selected = st.sidebar.selectbox("Sessão", sessions, format_func=lambda path: path.name)


def read_table(name: str) -> pd.DataFrame:
    path = selected / f"{name}.parquet"
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


laps = read_table("driver_lap_performance")
summary = read_table("driver_session_summary")
tyres = read_table("tyre_stint_analysis")
pits = read_table("pit_stop_analysis")

if laps.empty:
    st.warning("A tabela de voltas está vazia para esta sessão.")
    st.stop()

drivers = sorted(laps["driver_name"].dropna().unique())
chosen = st.sidebar.multiselect("Pilotos", drivers, default=drivers[: min(3, len(drivers))])
filtered = laps[laps["driver_name"].isin(chosen)] if chosen else laps

best = filtered["lap_duration_seconds"].min()
cols = st.columns(3)
cols[0].metric("Pilotos selecionados", filtered["driver_number"].nunique())
cols[1].metric("Voltas válidas", int(filtered["is_valid_lap"].sum()))
cols[2].metric("Melhor volta", f"{best:.3f} s" if pd.notna(best) else "—")

st.subheader("Melhores voltas")
if not summary.empty:
    st.dataframe(
        summary.sort_values("best_lap")[
            [
                column
                for column in (
                    "driver_name",
                    "team_name",
                    "best_lap",
                    "average_lap",
                    "consistency_std",
                    "final_position",
                )
                if column in summary
            ]
        ],
        use_container_width=True,
    )

st.subheader("Comparação de ritmo")
st.plotly_chart(
    px.line(filtered, x="lap_number", y="lap_duration_seconds", color="driver_name", markers=True),
    use_container_width=True,
)

st.subheader("Consistência por piloto")
if not summary.empty:
    st.plotly_chart(px.bar(summary, x="driver_name", y="consistency_std", color="team_name"), use_container_width=True)

st.subheader("Degradação de pneus por stint")
if tyres.empty:
    st.info("Não há stints suficientes para esta análise.")
else:
    st.dataframe(tyres, use_container_width=True)
    st.plotly_chart(
        px.scatter(tyres, x="stint_length", y="degradation_per_lap", color="compound", hover_name="driver_name"),
        use_container_width=True,
    )

st.subheader("Desempenho de pit stops")
if pits.empty:
    st.info("Não há dados de pit stops para esta sessão.")
else:
    duration = "stop_duration" if "stop_duration" in pits else "pit_duration_seconds"
    st.plotly_chart(
        px.box(pits, x="driver_name", y=duration, color="team_name", points="all"), use_container_width=True
    )

st.caption(
    "Tempos maiores podem incluir tráfego, bandeiras ou voltas de entrada/saída. "
    "As análises são descritivas e não demonstram causalidade."
)
