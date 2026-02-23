"""CLI entry point for CashFlow Story pipeline."""

import sys
import time
import glob

import click
import yaml
import logging
from pathlib import Path
from typing import Optional

from src.pipeline import CashFlowStoryPipeline
from src.utils.logger import setup_logging


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """
    CashFlow Story Pipeline - ERP XML to board-ready insights.
    
    Transforms ERP financial data into executive-ready cash flow stories
    with Power of One analysis, cash quality assessment, and AI insights.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(level=logging.DEBUG if verbose else logging.INFO)


@cli.command()
@click.option(
    "--input", "-i",
    type=click.Path(exists=True),
    required=True,
    help="Path to ERP data file (XML or Excel)"
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True),
    default="config.yaml",
    help="Configuration file path"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="output",
    help="Output directory for reports"
)
@click.option(
    "--no-ai",
    is_flag=True,
    help="Skip AI narrative generation"
)
@click.option(
    "--format", "-f",
    multiple=True,
    type=click.Choice(["excel", "html", "pdf", "json"], case_sensitive=False),
    default=["excel", "html"],
    help="Output formats to generate"
)
@click.pass_context
def run(
    ctx: click.Context,
    input: str,
    config: str,
    output: str,
    no_ai: bool,
    format: tuple
) -> None:
    """
    Run CashFlow Story analysis on ERP data.

    Example:
        $ cashflow-story run --input balancete.xml --output reports/
    """
    try:
        Path(output).mkdir(parents=True, exist_ok=True)
        config_name = Path(config).stem
        pipeline = CashFlowStoryPipeline(
            config_name=config_name, config_path=config
        )
        result = pipeline.run(
            input_path=input,
            output_path=output,
            options={
                "no_ai": no_ai,
                "format": list(format),
                "verbose": ctx.obj["verbose"],
            },
        )
        click.echo(f"Analysis complete for {result.company}")
        click.echo(f"Periods analyzed: {len(result.periods)}")
        click.echo(f"Power of One levers: {len(result.power_of_one)}")
        click.echo(f"Cash quality metrics: {len(result.cash_quality)}")
        click.echo(f"AI insights: {'Yes' if result.ai_insights else 'Skipped'}")
        click.echo(f"Output: {output}")
    except Exception as e:
        raise click.ClickException(str(e))


@cli.command()
@click.option(
    "--folder", "-f",
    type=click.Path(exists=True),
    required=True,
    help="Folder to watch for ERP files"
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True),
    default="config.yaml",
    help="Configuration file path"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="output",
    help="Output directory for reports"
)
@click.option(
    "--interval",
    type=int,
    default=60,
    help="Check interval in seconds"
)
@click.pass_context
def watch(
    ctx: click.Context,
    folder: str,
    config: str,
    output: str,
    interval: int
) -> None:
    """
    Watch folder for ERP files and auto-process.

    Example:
        $ cashflow-story watch --folder erp_inbox/
    """
    click.echo(f"Watching: {folder}")
    click.echo(f"Output: {output}")
    click.echo(f"Check interval: {interval}s")

    processed: set = set()
    config_name = Path(config).stem

    try:
        while True:
            xml_files = glob.glob(str(Path(folder) / "*.xml"))
            xlsx_files = glob.glob(str(Path(folder) / "*.xlsx"))
            all_files = xml_files + xlsx_files

            for file in all_files:
                if file not in processed:
                    click.echo(f"New file detected: {file}")
                    try:
                        Path(output).mkdir(parents=True, exist_ok=True)
                        pipeline = CashFlowStoryPipeline(
                            config_name=config_name, config_path=config
                        )
                        pipeline.run(
                            input_path=file,
                            output_path=output,
                            options={
                                "no_ai": False,
                                "format": ["excel", "html"],
                                "verbose": ctx.obj["verbose"],
                            },
                        )
                        click.echo(f"Processed: {file}")
                    except Exception as e:
                        click.echo(f"Error processing {file}: {e}")
                    processed.add(file)

            time.sleep(interval)
    except KeyboardInterrupt:
        click.echo("Watch stopped.")


@cli.command()
@click.option(
    "--config", "-c",
    type=click.Path(exists=True),
    required=True,
    help="Configuration file to validate"
)
@click.pass_context
def validate(ctx: click.Context, config: str) -> None:
    """
    Validate configuration file.

    Example:
        $ cashflow-story validate --config config.yaml
    """
    errors: list = []

    try:
        with open(config) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        click.echo(click.style(f"Failed to load config: {e}", fg="red"))
        sys.exit(1)

    if not isinstance(data, dict):
        click.echo(click.style("Config file is not a valid YAML mapping.", fg="red"))
        sys.exit(1)

    click.echo(f"Config: {config}")
    click.echo(f"Company: {data.get('company', {}).get('name', 'N/A')}")

    if "company" not in data:
        errors.append("Missing required section: 'company'")
    if "account_mapping" not in data:
        errors.append("Missing required section: 'account_mapping'")

    account_mapping = data.get("account_mapping", {})
    click.echo(f"Account categories: {len(account_mapping)}")

    required_categories = ["revenue", "deductions", "cogs", "operating_expenses"]
    for category in required_categories:
        if category not in account_mapping:
            errors.append(f"Missing required account category: '{category}'")
            continue
        cat_data = account_mapping[category]
        if not isinstance(cat_data, dict) or "accounts" not in cat_data:
            errors.append(f"Category '{category}' missing 'accounts' list")
            continue
        accounts = cat_data["accounts"]
        if not isinstance(accounts, list):
            errors.append(f"Category '{category}': 'accounts' must be a list")
            continue
        for acct in accounts:
            if not isinstance(acct, str):
                errors.append(
                    f"Category '{category}': account '{acct}' must be a string"
                )

    for msg in errors:
        click.echo(click.style(msg, fg="red"))

    if errors:
        click.echo(click.style("Validation: FAILED", fg="red"))
        sys.exit(1)
    else:
        click.echo(click.style("Validation: PASSED", fg="green"))


if __name__ == "__main__":
    cli()
