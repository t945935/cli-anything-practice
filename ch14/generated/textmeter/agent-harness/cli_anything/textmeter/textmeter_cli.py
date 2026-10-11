"""Click commands, consistent responses, and a stateless REPL."""
import json
import os
from pathlib import Path
import shlex
import sys

import click

from cli_anything.textmeter.core.export import export_report
from cli_anything.textmeter.utils.textmeter_backend import analyze


def emit(command: str | None, data: object = None,
         error: Exception | None = None) -> None:
    """Write one JSON object to stdout; errors never masquerade as success."""
    envelope = {
        "schema_version": 1, "command": command, "ok": error is None,
        "data": data if error is None else None,
        "error": None if error is None else {
            "code": type(error).__name__, "message": str(error)
        },
    }
    click.echo(json.dumps(envelope, ensure_ascii=False))


@click.group(invoke_without_command=True)
@click.option("--json", "json_mode", is_flag=True,
              help="Emit a single JSON response for one-shot commands.")
@click.pass_context
def cli(ctx: click.Context, json_mode: bool) -> None:
    """Analyze UTF-8 text or export statistics without overwriting files."""
    ctx.ensure_object(dict)
    ctx.obj["json_mode"] = json_mode
    if ctx.invoked_subcommand is None:
        if json_mode:
            raise click.UsageError("--json requires analyze or export")
        ctx.invoke(repl)


@cli.command("analyze")
@click.argument("input_path", type=click.Path(path_type=Path))
def analyze_command(input_path: Path) -> None:
    """Analyze INPUT_PATH through the installed TextMeter backend."""
    emit("analyze", analyze(input_path))


@cli.command("export")
@click.argument("input_path", type=click.Path(path_type=Path))
@click.option("--output", required=True, type=click.Path(path_type=Path))
def export_command(input_path: Path, output: Path) -> None:
    """Write a new JSON report; existing paths are never replaced."""
    emit("export", export_report(input_path, output))


@cli.command()
@click.pass_context
def repl(ctx: click.Context) -> None:
    """Run commands interactively; quit and exit end the loop."""
    if ctx.obj.get("json_mode"):
        raise click.UsageError("--json is for one-shot commands, not repl")
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    skin = session = None
    if interactive:
        from cli_anything.textmeter.utils.repl_skin import ReplSkin
        skin = ReplSkin("textmeter", version="0.1.0", history_file=os.devnull)
        skin.skill_install_cmd = "Use the packaged skill; see the book README"
        skin.print_banner()
        session = skin.create_prompt_session()
    while True:
        try:
            line = skin.get_input(session) if skin else sys.stdin.readline()
            if not skin and not line:
                break
            words = shlex.split(line)
            if not words:
                continue
            if words[0] in {"quit", "exit"}:
                break
            if words == ["help"]:
                words = ["--help"]
            if not any(w in {"analyze", "export", "--help"} for w in words):
                raise ValueError("Use analyze, export, help or quit")
            if "repl" in words:
                raise ValueError("Nested REPL is not supported")
            run(words)
        except (ValueError, KeyboardInterrupt) as error:
            emit(None, error=error)
        except EOFError:
            break
    if skin:
        skin.print_goodbye()


def run(argv: list[str]) -> int:
    """Execute once and translate handled exceptions into the book contract."""
    command = next((arg for arg in argv if arg in {"analyze", "export"}), None)
    try:
        cli.main(args=argv, prog_name="cli-anything-textmeter",
                 standalone_mode=False)
        return 0
    except (click.ClickException, OSError, ValueError) as error:
        emit(command, error=error)
        return 2
    except (click.Abort, KeyboardInterrupt):
        emit(command, error=RuntimeError("Interrupted"))
        return 130


def main() -> None:
    """Console entry point."""
    raise SystemExit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
