from kordel_racing.quality.contracts import LAPS_CONTRACT


def test_laps_contract_declares_expected_rules():
    assert LAPS_CONTRACT.dataset == "laps"
    assert LAPS_CONTRACT.required_columns == (
        "session_key",
        "driver_number",
        "lap_number",
        "lap_duration",
    )
    assert LAPS_CONTRACT.non_nullable_columns == (
        "session_key",
        "driver_number",
        "lap_number",
    )
    assert LAPS_CONTRACT.logical_key == (
        "session_key",
        "driver_number",
        "lap_number",
    )
