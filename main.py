import argparse


def run_repl():
    """Run a simple interactive REPL using ``core.agent.Agent``."""
    from core.agent import Agent

    agent = Agent("local")
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
            print(response)
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
    args, remaining = parser.parse_known_args(argv)

    if args.mode == "cli":
        from cli.memory_cli import main as cli_main

        cli_main(remaining)
    elif args.mode == "gui":
        from gui.qt_interface import run_gui

        from core.agent import Agent

        agent = Agent("local")
        run_gui(agent)
    else:  # repl
        run_repl()


if __name__ == "__main__":
    main()
