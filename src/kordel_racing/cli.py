"""CLI enxuta para selecionar sessão e destinos."""

import argparse

from kordel_racing.pipelines.full_pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa o Kordel Racing Data Lab")
    parser.add_argument("command", choices=["run"], nargs="?", default="run")
    parser.add_argument("--session-key", type=int)
    parser.add_argument("--meeting-key", type=int)
    parser.add_argument("--output-dir")
    parser.add_argument("--endpoints", nargs="+")
    args = parser.parse_args()
    run_pipeline(
        session_key=args.session_key,
        meeting_key=args.meeting_key,
        output_dir=args.output_dir,
        endpoints=args.endpoints,
    )


if __name__ == "__main__":
    main()
