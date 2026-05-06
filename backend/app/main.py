from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from app.agent import brain
from app.database import SessionLocal, init_db

console = Console()


def print_banner():
    console.print(
        Panel.fit(
            Text("Doctor's Agentic OS — Week 1", justify="center", style="bold green"),
            subtitle="Powered by GPT-4o Mini",
            border_style="green",
        )
    )
    console.print("[dim]Type your instructions. Type 'exit' to quit. Type 'new' to start a new session.[/dim]\n")


def main():
    init_db()
    print_banner()

    db = SessionLocal()
    conversation_history: list[dict] = []

    try:
        while True:
            try:
                user_input = Prompt.ask("[bold cyan]Doctor[/bold cyan]").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Session ended.[/dim]")
                break

            if not user_input:
                continue

            if user_input.lower() == "exit":
                console.print("[dim]Goodbye.[/dim]")
                break

            if user_input.lower() == "new":
                conversation_history.clear()
                console.print("[dim]New session started.[/dim]\n")
                continue

            with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
                reply = brain.run(
                    user_message=user_input,
                    db=db,
                    conversation_history=conversation_history,
                )

            console.print(f"\n[bold green]Agent[/bold green]: {reply}\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
