from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .config import load_settings
from .hf_client import HuggingFaceClient
from .presentation_agent import PresentationAgent

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


@app.command()
def chat(
    max_tokens: int = typer.Option(512, help="Max tokens to generate"),
    temperature: float = typer.Option(0.7, help="Sampling temperature"),
) -> None:
    """Interactive chat using Gemini API."""
    settings = load_settings()
    if settings.llm_provider != "gemini":
        console.print("[red]LLM_PROVIDER must be 'gemini' for chat.[/red]")
        raise typer.Exit(code=1)

    from .gemini_client import GeminiClient  # local import to avoid unused import when not chatting

    client = GeminiClient(settings.gemini_api_key)  # type: ignore[arg-type]

    messages: list[dict[str, str]] = [{"role": "system", "content": settings.system_prompt}]

    console.print(f"Model: [bold]{settings.gemini_model}[/bold]")
    console.print("Type 'exit' to quit.\n")

    try:
        while True:
            user_text = console.input("[bold cyan]You[/bold cyan]> ").strip()
            if not user_text:
                continue
            if user_text.lower() in {"exit", "quit"}:
                break

            messages.append({"role": "user", "content": user_text})
            reply = client.chat(
                model=settings.gemini_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            messages.append({"role": "assistant", "content": reply})
            console.print(f"[bold green]Agent[/bold green]> {reply}\n")
    finally:
        client.close()


@app.command()
def make_presentation(
    folder: str = typer.Argument(..., help="Folder containing the paper (.tex, figures, bibs)"),
    main_tex: str = typer.Option(None, help="Optional main .tex filename; otherwise auto-detects"),
    title: str = typer.Option("", help="Presentation title (optional)"),
    author: str = typer.Option("", help="Author(s) (optional)"),
    institute: str = typer.Option("", help="Institute (optional)"),
    output_tex: str = typer.Option(None, help="Path to write Beamer .tex (default: {folder}/presentation.tex)"),
    report_path: str = typer.Option("report.json", help="Path to write processing report"),
    style_prompt_opt: str = typer.Option("", help="Style prompt (if empty, you will be prompted)"),
    tex_only: bool = typer.Option(False, "--tex-only", help="Skip PDF compilation (only generate .tex file)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Build a Beamer presentation after user prompt + confirmation."""

    console.print("[bold]Presentation Builder[/bold]")
    console.print(f"Folder: {folder}")
    if main_tex:
        console.print(f"Main .tex: {main_tex}")

    # Get style prompt interactively if not provided via flag (plain input to ensure visibility)
    style_prompt = style_prompt_opt.strip()
    if not style_prompt:
        try:
            print("Style prompt (required): ", end="", flush=True)
            style_prompt = input().strip()
        except EOFError:
            style_prompt = ""
    if not style_prompt:
        console.print("[red]Aborted:[/red] style prompt is required.")
        raise typer.Exit(code=1)

    # Explicit confirmation unless --yes (plain input for reliability)
    if not yes:
        try:
            print("Proceed to generate slides? [y/N]: ", end="", flush=True)
            confirm_resp = input().strip().lower()
        except EOFError:
            confirm_resp = ""
        if confirm_resp not in {"y", "yes"}:
            console.print("Aborted by user.")
            raise typer.Exit(code=1)

    agent = PresentationAgent()

    try:
        agent.load_tex_from_folder(folder, main_filename=main_tex)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Failed to load TeX:[/red] {exc}")
        raise typer.Exit(code=1)

    # Set metadata if provided
    agent.set_presentation_params(
        title=title or "Presentation",
        author=author or "",
        institute=institute or "",
        style_prompt=style_prompt,
    )

    try:
        beamer_code = agent.generate_presentation()
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Generation failed:[/red] {exc}")
        raise typer.Exit(code=1)

    # Save outputs
    try:
        tex_path = agent.save_presentation(output_tex)
        agent.save_report(report_path)

        # Compile to PDF by default (unless --tex-only flag is used)
        pdf_path = None
        if not tex_only:
            console.print("[cyan]Compiling to PDF...[/cyan]")
            if agent.compile_to_pdf(tex_path):
                pdf_path = tex_path.with_suffix('.pdf')
                console.print(f"[green]✓ PDF created successfully![/green]")
            else:
                console.print("[yellow]⚠️  PDF compilation failed. .tex file is still available for manual compilation.[/yellow]")

    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Saving failed:[/red] {exc}")
        raise typer.Exit(code=1)

    # Display final output locations
    console.print(f"\n[bold green]✓ Done![/bold green]")
    console.print(f"  📄 Slides (.tex): {tex_path}")
    if pdf_path and pdf_path.exists():
        console.print(f"  📕 PDF: {pdf_path}")
        console.print(f"\n[bold cyan]Open PDF:[/bold cyan] open {pdf_path}")
    console.print(f"  📊 Report: {report_path}")


if __name__ == "__main__":
    app()
