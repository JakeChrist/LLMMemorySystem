import argparse

from ms_utils.logger import Logger

logger = Logger(__name__)


def run_repl(llm_name: str, db_path: str) -> None:
    """Run a simple interactive REPL using ``core.agent.Agent``."""
    from core.agent import Agent

    agent = Agent(llm_name, db_path=db_path)
    try:
        while True:
            try:
                text = input(" > ").strip()
            except EOFError:
                print()
                break

            if not text:
                continue
            if text.lower() in {"exit", "quit"}:
                break
            response = agent.receive(text)
            logger.info(response)
    except KeyboardInterrupt:
        print()


def main(argv: list[str] | None = None) -> None:
    """Entry point for the LLMemory system."""
    parser = argparse.ArgumentParser(description="LLMemory entry point")
    parser.add_argument(
        "mode",
        choices=["cli", "gui", "repl"],
        help="Operation mode: cli, gui or repl",
    )
    parser.add_argument(
        "--llm",
        default="local",
        help="LLM backend to use (e.g. local, openai)",
    )
    parser.add_argument(
        "--db",
        default="memory.db",
        help="Path to SQLite database",
    )

    args, remaining = parser.parse_known_args(argv)

    if args.mode == "cli":
        from cli.memory_cli import main as cli_main

        cli_main(["--db", args.db, *remaining])
    elif args.mode == "gui":
        from gui.qt_interface import run_gui

        from core.agent import Agent

        agent = Agent(args.llm, db_path=args.db)
        # Start background dreaming when launching the GUI so that summaries
        # accumulate automatically while the interface is open.
        scheduler = agent.memory.start_dreaming()
        try:
            run_gui(agent)
        finally:
            scheduler.stop()
    else:  # repl
        run_repl(args.llm, args.db)


if __name__ == "__main__":
    main()
