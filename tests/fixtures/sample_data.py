"""Massa sintética pequena e legível."""

DRIVERS = [
    {"session_key": 1, "driver_number": 4, "full_name": "Piloto A", "team_name": "Equipe X"},
    {"session_key": 1, "driver_number": 81, "full_name": "Piloto B", "team_name": "Equipe X"},
]
LAPS = [
    {"session_key": 1, "driver_number": 4, "lap_number": 1, "lap_duration": 91.0},
    {"session_key": 1, "driver_number": 4, "lap_number": 2, "lap_duration": 90.0},
    {"session_key": 1, "driver_number": 4, "lap_number": 3, "lap_duration": 92.0},
    {"session_key": 1, "driver_number": 81, "lap_number": 1, "lap_duration": 90.5},
    {"session_key": 1, "driver_number": 81, "lap_number": 2, "lap_duration": 89.5},
]
STINTS = [
    {"session_key": 1, "driver_number": 4, "stint_number": 1, "lap_start": 1, "lap_end": 3, "compound": "MEDIUM"},
    {"session_key": 1, "driver_number": 81, "stint_number": 1, "lap_start": 1, "lap_end": 2, "compound": "SOFT"},
]
