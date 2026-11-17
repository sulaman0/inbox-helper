"""CLI entry points via Typer."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .models import AuditAction
from . import audit, store, classify as _classify, draft as _draft

app = typer.Typer(help="Inbox Helper — classify and draft replies for candidate emails.")
console = Console()


@app.command()
def run(
    messages_path: str = typer.Argument("data/messages.json", help="Path to messages JSON or CSV"),
    offline: bool = typer.Option(False, "--offline", help="Force offline mode (no LLM)"),
) -> None:
    """Classify messages and generate drafts. Writes out/drafts.json."""
    path = Path(messages_path)
    if not path.exists():
        console.print(f"[red]File not found: {path}[/red]")
        raise typer.Exit(1)

    messages = store.load_messages(path)
    console.print(f"[bold]Loaded {len(messages)} messages[/bold]")

    if offline:
        console.print("[yellow]Running in OFFLINE mode (rule-based classifier)[/yellow]")
    elif not _classify.is_llm_available():
        console.print("[yellow]No ANTHROPIC_API_KEY found — running in OFFLINE mode[/yellow]")
        offline = True

    drafts = []
    fallback_count = 0

    for msg in messages:
        classification, source, fell_back = _classify.classify_message(msg, offline=offline)
        if fell_back:
            fallback_count += 1
        audit.log(msg.id, AuditAction.classified, f"intent={classification.intent.value} source={source}")

        draft, _ = _draft.generate_draft(msg, classification, offline=offline)
        audit.log(msg.id, AuditAction.drafted, f"generated_by={draft.generated_by}")
        drafts.append(draft)

    store.save_drafts(drafts)

    if fallback_count:
        console.print(f"[yellow]{fallback_count} message(s) fell back to offline classifier[/yellow]")

    # Print summary table grouped by intent
    _print_summary(drafts)
    console.print(f"\n[green]Drafts saved to out/drafts.json[/green]")
    console.print("Run [bold]python -m inbox_helper review[/bold] to open the review UI.")


def _print_summary(drafts) -> None:
    from collections import Counter
    counts: Counter = Counter()
    urgency_map: dict = {}
    for d in drafts:
        counts[d.classification.intent.value] += 1
        urgency_map[d.classification.intent.value] = d.classification.urgency.value

    table = Table(title="Messages by Intent", show_lines=True)
    table.add_column("Intent", style="cyan")
    table.add_column("Count", justify="right", style="bold")
    table.add_column("Sample Urgency", style="yellow")

    for intent, count in sorted(counts.items(), key=lambda x: -x[1]):
        table.add_row(intent, str(count), urgency_map.get(intent, ""))

    console.print(table)


@app.command()
def review() -> None:
    """Launch the Streamlit review UI."""
    app_path = Path(__file__).parent.parent / "app" / "review_app.py"
    if not app_path.exists():
        console.print("[red]Review app not found at app/review_app.py[/red]")
        raise typer.Exit(1)
    drafts_path = Path("out/drafts.json")
    if not drafts_path.exists():
        console.print("[yellow]No drafts found. Run 'python -m inbox_helper run' first.[/yellow]")
        raise typer.Exit(1)
    console.print("[bold green]Launching Streamlit review UI...[/bold green]")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)], check=False)


@app.command()
def eval(
    offline: bool = typer.Option(False, "--offline", help="Evaluate in offline mode"),
) -> None:
    """Evaluate classifier accuracy against data/labels.json."""
    labels_path = Path("data/labels.json")
    messages_path = Path("data/messages.json")

    if not labels_path.exists():
        console.print("[red]data/labels.json not found[/red]")
        raise typer.Exit(1)
    if not messages_path.exists():
        console.print("[red]data/messages.json not found[/red]")
        raise typer.Exit(1)

    messages = store.load_messages(messages_path)
    with open(labels_path) as f:
        labels_data = json.load(f)
    labels = {item["id"]: item["intent"] for item in labels_data}

    if offline or not _classify.is_llm_available():
        console.print("[yellow]Evaluating in OFFLINE mode[/yellow]")
        offline = True

    correct = 0
    total = 0
    confusion: dict[str, dict[str, int]] = {}

    for msg in messages:
        if msg.id not in labels:
            continue
        true_label = labels[msg.id]
        classification, _, _ = _classify.classify_message(msg, offline=offline)
        pred_label = classification.intent.value
        total += 1
        if pred_label == true_label:
            correct += 1
        confusion.setdefault(true_label, {})
        confusion[true_label][pred_label] = confusion[true_label].get(pred_label, 0) + 1

    accuracy = correct / total if total else 0.0
    console.print(f"\n[bold]Accuracy: {accuracy:.1%}  ({correct}/{total})[/bold]")

    # Confusion table
    intents = sorted(confusion.keys())
    table = Table(title="Confusion Matrix (rows=true, cols=predicted)")
    table.add_column("True \\ Pred", style="bold")
    for i in intents:
        table.add_column(i[:8], justify="right")

    for true_label in intents:
        row = [true_label[:8]]
        for pred_label in intents:
            count = confusion.get(true_label, {}).get(pred_label, 0)
            if true_label == pred_label and count > 0:
                row.append(f"[green]{count}[/green]")
            elif count > 0:
                row.append(f"[red]{count}[/red]")
            else:
                row.append("·")
        table.add_row(*row)

    console.print(table)
    console.print(f"\nMode: {'offline' if offline else 'llm'}")
