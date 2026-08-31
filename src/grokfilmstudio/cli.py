"""
Command Line Interface for GrokFilmStudio.

Provides CLI access to all major pipeline operations.
"""

import asyncio
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from grokfilmstudio.config import settings
from grokfilmstudio.compiler.prompt_compiler import PromptCompiler
from grokfilmstudio.compiler.script_parser import ScriptParser
from grokfilmstudio.models.production_bible import (
    AudioAnchor,
    CharacterAnchor,
    ContextAnchor,
    LocationAnchor,
    ProductionBible,
    WorldAnchor,
)
from grokfilmstudio.models.shotlist import ShotStatus
from grokfilmstudio.pipeline.ffmpeg_assembly import FFmpegAssembly
from grokfilmstudio.pipeline.timeline_export import TimelineExport
from grokfilmstudio.pipeline.batch_generator import BatchGenerationManager
from grokfilmstudio.state import StatePersistenceManager

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="grokfilm")
def main():
    """GrokFilmStudio - AI Film Production Automation System

    A full-stack automation layer for Grok/Flux video workflows.
    """
    pass


# =============================================================================
# Project Management Commands
# =============================================================================


@main.group()
def project():
    """Project management commands."""
    pass


@project.command("new")
@click.argument("name")
@click.option("--output-dir", type=click.Path(), default=None, help="Output directory")
def project_new(name: str, output_dir: Optional[str]):
    """Create a new project."""
    pm = StatePersistenceManager()

    project_id, bible, shotlist, state = pm.create_project(project_name=name)

    console.print(
        Panel.fit(
            f"[green]Project Created![/green]\n\n"
            f"Project ID: [cyan]{project_id}[/cyan]\n"
            f"Name: {name}\n"
            f"Directory: {pm.get_project_dir(project_id)}",
            title="New Project",
        )
    )


@project.command("list")
def project_list():
    """List all projects."""
    pm = StatePersistenceManager()

    if not settings.projects_dir.exists():
        console.print("[yellow]No projects found.[/yellow]")
        return

    projects = [d for d in settings.projects_dir.iterdir() if d.is_dir()]

    if not projects:
        console.print("[yellow]No projects found.[/yellow]")
        return

    table = Table(title="Projects")
    table.add_column("Project ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Created", style="green")

    for proj_dir in sorted(projects):
        state_path = proj_dir / "state.json"
        bible_path = proj_dir / "production_bible.json"

        if bible_path.exists():
            import json

            with open(bible_path) as f:
                bible_data = json.load(f)
            project_id = bible_data.get("project_id", "Unknown")
            name = bible_data.get("project_name", "Unknown")
            created = bible_data.get("created_at", "Unknown")[:10]

            table.add_row(project_id, name, created)

    console.print(table)


@project.command("info")
@click.argument("project_id")
def project_info(project_id: str):
    """Show project information."""
    pm = StatePersistenceManager()

    bible, shotlist, state = pm.recover_project(project_id)

    if not bible:
        console.print(f"[red]Project not found: {project_id}[/red]")
        return

    console.print(Panel(f"Project: {bible.project_name}", title="Project Info"))

    # Show summary
    if state:
        summary = state.get_completion_summary()
        console.print(f"Phase: {summary['current_phase']}")
        console.print(f"Progress: {summary['completed_shots']}/{summary['total_shots']} shots ({summary['completion_percent']}%)")


# =============================================================================
# Bible Management Commands
# =============================================================================


@main.group()
def bible():
    """Production bible management commands."""
    pass


@bible.command("add-character")
@click.argument("project_id")
@click.option("--name", required=True, help="Character name")
@click.option("--dna", required=True, help="DNA prompt (max 150 chars)")
@click.option("--ref-image", type=click.Path(), help="Reference image path")
def bible_add_character(
    project_id: str,
    name: str,
    dna: str,
    ref_image: Optional[str],
):
    """Add a character to the production bible."""
    pm = StatePersistenceManager()

    bible, _, _ = pm.recover_project(project_id)

    if not bible:
        console.print(f"[red]Project not found: {project_id}[/red]")
        return

    character = CharacterAnchor(
        name=name,
        dna_prompt=dna,
        master_reference_image=ref_image,
    )

    bible.add_character(character)
    pm.save_bible(bible)

    console.print(
        f"[green]Added character:[/green] {name} ({character.character_id})"
    )


@bible.command("set-style")
@click.argument("project_id")
@click.option("--style", required=True, help="Style prompt")
@click.option("--aspect-ratio", default="16:9", help="Aspect ratio")
@click.option("--color-grade", default=None, help="Color grade")
def bible_set_style(
    project_id: str,
    style: str,
    aspect_ratio: str,
    color_grade: Optional[str],
):
    """Set the world/style anchor."""
    pm = StatePersistenceManager()

    bible, _, _ = pm.recover_project(project_id)

    if not bible:
        console.print(f"[red]Project not found: {project_id}[/red]")
        return

    bible.world_anchors = WorldAnchor(
        style_prompt=style,
        aspect_ratio=aspect_ratio,
        color_grade=color_grade,
    )

    pm.save_bible(bible)
    console.print(f"[green]Style updated:[/green] {style[:50]}...")


@bible.command("add-location")
@click.argument("project_id")
@click.option("--name", required=True, help="Location name (e.g., 'Sarah's Apartment')")
@click.option("--dna", required=True, help="Location DNA prompt (key visual elements)")
@click.option("--lighting", default=None, help="Typical lighting condition")
@click.option("--mood", default=None, help="Emotional atmosphere")
@click.option("--ref-image", type=click.Path(), help="Reference image path")
def bible_add_location(
    project_id: str,
    name: str,
    dna: str,
    lighting: Optional[str],
    mood: Optional[str],
    ref_image: Optional[str],
):
    """Add a location anchor to lock environment consistency."""
    pm = StatePersistenceManager()

    bible, _, _ = pm.recover_project(project_id)

    if not bible:
        console.print(f"[red]Project not found: {project_id}[/red]")
        return

    location = LocationAnchor(
        name=name,
        dna_prompt=dna,
        lighting=lighting,
        mood=mood,
        master_reference_image=ref_image,
    )

    bible.add_location(location)
    pm.save_bible(bible)

    console.print(
        f"[green]Added location:[/green] {name} ({location.location_id})"
    )


@bible.command("add-context")
@click.argument("project_id")
@click.option("--name", required=True, help="Context name (e.g., 'The Chase Scene')")
@click.option("--time", default=None, help="Time period (e.g., 'Night, 2 AM')")
@click.option("--weather", default=None, help="Weather conditions")
@click.option("--mood", default=None, help="Story mood")
@click.option("--notes", default=None, help="Continuity notes")
def bible_add_context(
    project_id: str,
    name: str,
    time: Optional[str],
    weather: Optional[str],
    mood: Optional[str],
    notes: Optional[str],
):
    """Add a context anchor to lock story continuity."""
    pm = StatePersistenceManager()

    bible, _, _ = pm.recover_project(project_id)

    if not bible:
        console.print(f"[red]Project not found: {project_id}[/red]")
        return

    context = ContextAnchor(
        name=name,
        time_period=time,
        weather=weather,
        story_mood=mood,
        continuity_notes=notes,
    )

    bible.add_context(context)
    pm.save_bible(bible)

    console.print(
        f"[green]Added context:[/green] {name} ({context.context_id})"
    )


@bible.command("summary")
@click.argument("project_id")
def bible_summary(project_id: str):
    """Show summary of all DNA anchors in the production bible."""
    pm = StatePersistenceManager()

    bible, _, _ = pm.recover_project(project_id)

    if not bible:
        console.print(f"[red]Project not found: {project_id}[/red]")
        return

    console.print(Panel(f"Production Bible: {bible.project_name}", title="DNA Summary"))

    # Characters
    if bible.character_anchors:
        console.print("\n[bold cyan]Characters:[/bold cyan]")
        for char in bible.character_anchors:
            console.print(f"  • {char.name}: {char.dna_prompt[:60]}...")

    # Locations
    if bible.location_anchors:
        console.print("\n[bold cyan]Locations:[/bold cyan]")
        for loc in bible.location_anchors:
            console.print(f"  • {loc.name}: {loc.dna_prompt[:60]}...")

    # Contexts
    if bible.context_anchors:
        console.print("\n[bold cyan]Contexts:[/bold cyan]")
        for ctx in bible.context_anchors:
            time_weather = f"{ctx.time_period or ''} {ctx.weather or ''}".strip()
            console.print(f"  • {ctx.name}: {time_weather} - {ctx.story_mood or ''}")

    # World Style
    if bible.world_anchors:
        console.print(f"\n[bold cyan]World Style:[/bold cyan] {bible.world_anchors.style_prompt}")


# =============================================================================
# Script & Shotlist Commands
# =============================================================================


@main.group()
def script():
    """Script parsing and shotlist commands."""
    pass


@script.command("parse")
@click.argument("project_id")
@click.argument("script_file", type=click.Path(exists=True))
@click.option(
    "--format",
    type=click.Choice(["auto", "synopsis", "treatment", "script"]),
    default="auto",
    help="Script format",
)
@click.option(
    "--duration",
    type=float,
    default=3.0,
    help="Default shot duration (seconds)",
)
def script_parse(
    project_id: str,
    script_file: str,
    format: str,
    duration: float,
):
    """Parse a script into a shotlist."""
    pm = StatePersistenceManager()

    bible, _, _ = pm.recover_project(project_id)

    if not bible:
        console.print(f"[red]Project not found: {project_id}[/red]")
        return

    # Read script
    with open(script_file, "r") as f:
        script_text = f.read()

    # Parse
    parser = ScriptParser(bible, default_shot_duration=duration)
    shotlist = parser.auto_generate_shots(script_text, format=format)

    # Save
    pm.save_shotlist(shotlist)

    console.print(
        Panel.fit(
            f"[green]Script parsed![/green]\n\n"
            f"Shots created: {shotlist.total_shots}\n"
            f"Total duration: {shotlist.total_duration_seconds:.1f}s",
            title="Parse Complete",
        )
    )


@script.command("list")
@click.argument("project_id")
def script_list(project_id: str):
    """List shots in the shotlist."""
    pm = StatePersistenceManager()

    shotlist = pm.load_shotlist(project_id)

    if not shotlist:
        console.print(f"[red]No shotlist found for: {project_id}[/red]")
        return

    table = Table(title=f"Shots for {project_id}")
    table.add_column("Shot ID", style="cyan")
    table.add_column("Scene", style="magenta")
    table.add_column("Action", style="green")
    table.add_column("Status", style="yellow")

    for shot in shotlist.shots:
        table.add_row(
            shot.shot_id,
            str(shot.scene_number),
            shot.action_description[:40] + "..." if len(shot.action_description) > 40 else shot.action_description,
            shot.status.value,
        )

    console.print(table)


# =============================================================================
# Compile Commands
# =============================================================================


@main.group()
def compile():
    """Prompt compilation commands."""
    pass


@compile.command("all")
@click.argument("project_id")
def compile_all(project_id: str):
    """Compile prompts for all shots."""
    pm = StatePersistenceManager()

    bible = pm.load_bible(project_id)
    shotlist = pm.load_shotlist(project_id)

    if not bible:
        console.print(f"[red]Project not found: {project_id}[/red]")
        return

    if not shotlist:
        console.print(f"[red]No shotlist found for: {project_id}[/red]")
        return

    compiler = PromptCompiler(bible)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Compiling prompts...", total=len(shotlist.shots))

        for shot in shotlist.shots:
            prompt, errors, warnings = compiler.compile_and_validate(shot)
            shot.compiled_prompt = prompt

            if errors:
                console.print(f"[red]Errors for {shot.shot_id}:[/red] {errors}")

            progress.advance(task)

    pm.save_shotlist(shotlist)
    console.print(f"[green]Compiled prompts for {len(shotlist.shots)} shots[/green]")


@compile.command("preview")
@click.argument("project_id")
@click.argument("shot_id")
def compile_preview(project_id: str, shot_id: str):
    """Preview compiled prompt for a shot."""
    pm = StatePersistenceManager()

    bible = pm.load_bible(project_id)
    shotlist = pm.load_shotlist(project_id)

    if not bible or not shotlist:
        console.print("[red]Project not found[/red]")
        return

    shot = shotlist.get_shot(shot_id)
    if not shot:
        console.print(f"[red]Shot not found: {shot_id}[/red]")
        return

    compiler = PromptCompiler(bible)
    prompt, errors, warnings = compiler.compile_and_validate(shot)

    console.print(Panel(prompt, title=f"Prompt for {shot_id}"))

    if errors:
        for err in errors:
            console.print(f"[red]Error:[/red] {err}")
    if warnings:
        for warn in warnings:
            console.print(f"[yellow]Warning:[/yellow] {warn}")


# =============================================================================
# Generate Commands (Browser Automation)
# =============================================================================


@main.group()
def generate():
    """Generation commands (requires Grok credentials)."""
    pass


@generate.command("batch")
@click.argument("project_id")
@click.option("--location", default=None, help="Location ID to lock DNA")
@click.option("--context", default=None, help="Context ID to lock DNA")
@click.option("--stage", type=click.Choice(["all", "keyframes", "videos", "assemble"]), default="all")
def generate_batch(project_id: str, location: Optional[str], context: Optional[str], stage: str):
    """Generate shots in batch mode with DNA locking."""
    pm = StatePersistenceManager()

    bible, shotlist, state = pm.recover_project(project_id)

    if not bible or not shotlist:
        console.print(f"[red]Project not found: {project_id}[/red]")
        return

    console.print(
        Panel.fit(
            f"[cyan]Batch Generation[/cyan]\n\n"
            f"Project: {bible.project_name}\n"
            f"Location Lock: {location or 'None'}\n"
            f"Context Lock: {context or 'None'}\n"
            f"Stage: {stage}",
            title="Batch Generation",
        )
    )

    # Initialize batch manager (without GrokController for simulation)
    batch_mgr = BatchGenerationManager(project_id)
    job = batch_mgr.create_batch_job(location_id=location, context_id=context)

    console.print(f"\n[green]Created batch job:[/green] {job.job_id}")
    console.print(f"Shots to process: {len(job.shot_ids)}")

    # Run generation stages
    async def run_generation():
        if stage in ["all", "keyframes"]:
            console.print("\n[cyan]Stage 1: Generating keyframes...[/cyan]")
            job = await batch_mgr.run_keyframe_generation(job)
            console.print(f"[green]Keyframes complete:[/green] {job.completed_shots}/{job.total_shots}")

            if stage == "keyframes":
                console.print("\n[yellow]Stopping at keyframes for review[/yellow]")
                return

        if stage in ["all", "videos"]:
            console.print("\n[cyan]Stage 2: Generating videos...[/cyan]")
            job = await batch_mgr.run_video_generation(job)
            console.print(f"[green]Videos complete:[/green] {job.completed_shots}/{job.total_shots}")

        if stage == "all":
            console.print("\n[cyan]Stage 3: Assembling timeline...[/cyan]")
            output = batch_mgr.run_assembly(job)
            console.print(f"[green]Assembly complete:[/green] {output}")

    # Run async
    import asyncio
    asyncio.run(run_generation())

    # Show summary
    summary = batch_mgr.get_batch_summary()
    console.print("\n" + "=" * 50)
    console.print("[bold]Generation Summary:[/bold]")
    console.print(f"  Status: {summary.get('status', 'N/A')}")
    console.print(f"  Progress: {summary.get('progress_percent', 0)}%")
    console.print(f"  Keyframes: {summary.get('keyframes_generated', 0)}")
    console.print(f"  Videos: {summary.get('videos_generated', 0)}")
    if summary.get('errors'):
        console.print(f"  Errors: {len(summary['errors'])}")


@generate.command("keyframes")
@click.argument("project_id")
@click.option("--shot", default=None, help="Specific shot ID (or all)")
@click.option("--headless/--no-headless", default=True, help="Headless mode")
def generate_keyframes(project_id: str, shot: Optional[str], headless: bool):
    """Generate keyframes for shots (legacy - use 'generate batch')."""
    console.print("[yellow]Browser automation module - requires Grok credentials[/yellow]")
    console.print("Configure GROK_USERNAME and GROK_PASSWORD in .env")
    console.print("[dim]Tip: Use 'grokfilm generate batch' for batch generation with DNA locking[/dim]")


@generate.command("videos")
@click.argument("project_id")
@click.option("--shot", default=None, help="Specific shot ID (or all)")
def generate_videos(project_id: str, shot: Optional[str]):
    """Generate videos from keyframes (legacy - use 'generate batch')."""
    console.print("[yellow]Browser automation module - requires Grok credentials[/yellow]")
    console.print("Configure GROK_USERNAME and GROK_PASSWORD in .env")
    console.print("[dim]Tip: Use 'grokfilm generate batch' for batch generation with DNA locking[/dim]")


# =============================================================================
# Pipeline Commands
# =============================================================================


@main.group()
def pipeline():
    """Pipeline execution commands."""
    pass


@pipeline.command("run")
@click.argument("project_id")
@click.option("--phase", default="all", help="Specific phase to run")
@click.option("--location", default=None, help="Location ID to lock DNA")
@click.option("--context", default=None, help="Context ID to lock DNA")
def pipeline_run(project_id: str, phase: str, location: Optional[str], context: Optional[str]):
    """Run the full generation pipeline with batch processing."""
    console.print(
        Panel(
            f"Starting pipeline for [cyan]{project_id}[/cyan]\n\n"
            "Pipeline Stages:\n"
            "1. [cyan]Parse & Compile[/cyan] - Generate shots from script, compile prompts\n"
            "2. [cyan]Keyframes[/cyan] - Generate all keyframes with locked DNA\n"
            "3. [cyan]Review[/cyan] - [HUMAN REVIEW POINT] Approve/reject keyframes\n"
            "4. [cyan]Videos[/cyan] - Generate videos from approved keyframes\n"
            "5. [cyan]Assembly[/cyan] - Stitch clips, mix audio, export timeline",
            title="Pipeline Run",
        )
    )

    pm = StatePersistenceManager()
    bible, shotlist, state = pm.recover_project(project_id)

    if not bible or not shotlist:
        console.print(f"[red]Project not found: {project_id}[/red]")
        return

    console.print(f"\n[green]Shots to process:[/green] {len(shotlist.shots)}")
    console.print(f"[green]Location lock:[/green] {location or 'None'}")
    console.print(f"[green]Context lock:[/green] {context or 'None'}")

    # Use batch generation manager
    console.print("\n[cyan]Initializing batch generation manager...[/cyan]")
    batch_mgr = BatchGenerationManager(project_id)
    job = batch_mgr.create_batch_job(location_id=location, context_id=context)

    async def run_pipeline():
        # Stage 1: Keyframes
        if phase in ["all", "keyframes"]:
            console.print("\n" + "=" * 50)
            console.print("[bold cyan]STAGE 1: Generating Keyframes[/bold cyan]")
            console.print("=" * 50)

            job = await batch_mgr.run_keyframe_generation(job)

            console.print(f"\n[green]✓ Keyframes generated:[/green] {len(job.keyframes_generated)}")
            if job.errors:
                console.print(f"[yellow]Warnings:[/yellow] {len(job.errors)} issues")

            console.print("\n[yellow]⏸ PAUSE: Review keyframes before continuing[/yellow]")
            console.print("Run 'grokfilm generate batch --stage=videos' to continue")

        # Stage 2: Videos (if user wants to continue)
        if phase in ["all", "videos"]:
            console.print("\n" + "=" * 50)
            console.print("[bold cyan]STAGE 2: Generating Videos[/bold cyan]")
            console.print("=" * 50)

            job = await batch_mgr.run_video_generation(job)

            console.print(f"\n[green]✓ Videos generated:[/green] {len(job.videos_generated)}")

        # Stage 3: Assembly
        if phase == "all":
            console.print("\n" + "=" * 50)
            console.print("[bold cyan]STAGE 3: Assembling Timeline[/bold cyan]")
            console.print("=" * 50)

            output = batch_mgr.run_assembly(job)
            console.print(f"\n[green]✓ Final video:[/green] {output}")

            # Generate exports
            console.print("\n[cyan]Generating timeline exports...[/cyan]")
            batch_mgr._generate_timeline_exports()
            console.print(f"[green]✓ Exports saved to:[/green] {batch_mgr.exports_dir}")

    # Run async
    import asyncio
    asyncio.run(run_pipeline())

    # Final summary
    console.print("\n" + "=" * 50)
    console.print("[bold]Pipeline Complete![/bold]")
    summary = batch_mgr.get_batch_summary()
    for key, value in summary.items():
        if value:
            console.print(f"  {key}: {value}")


# =============================================================================
# Export Commands
# =============================================================================


@main.group()
def export():
    """Export commands."""
    pass


@export.command("timeline")
@click.argument("project_id")
@click.option(
    "--format",
    type=click.Choice(["all", "fcpxml", "edl", "premiere"]),
    default="all",
    help="Export format",
)
def export_timeline(project_id: str, format: str):
    """Export timeline for NLE import."""
    pm = StatePersistenceManager()

    shotlist = pm.load_shotlist(project_id)
    bible = pm.load_bible(project_id)

    if not shotlist:
        console.print(f"[red]No shotlist found for: {project_id}[/red]")
        return

    project_name = bible.project_name if bible else project_id
    output_dir = pm.get_project_dir(project_id) / "exports"

    exporter = TimelineExport(shotlist, project_name)

    if format == "all":
        results = exporter.generate_all(output_dir)
        for fmt, path in results.items():
            console.print(f"[green]{fmt}:[/green] {path}")
    else:
        console.print(f"[yellow]Exporting {format}...[/yellow]")
        # Would call specific export method here


@export.command("assembly")
@click.argument("project_id")
@click.option("--output", type=click.Path(), help="Output file path")
def export_assembly(project_id: str, output: Optional[str]):
    """Assemble final video from clips."""
    pm = StatePersistenceManager()

    shotlist = pm.load_shotlist(project_id)

    if not shotlist:
        console.print(f"[red]No shotlist found for: {project_id}[/red]")
        return

    # Collect clips with audio
    clips = []
    for shot in shotlist.shots:
        if shot.video_path:
            clips.append((Path(shot.video_path), Path(shot.audio_path) if shot.audio_path else None))

    if not clips:
        console.print("[red]No video clips found[/red]")
        return

    assembler = FFmpegAssembly()
    output_path = Path(output) if output else pm.get_project_dir(project_id) / "final.mp4"

    console.print(f"[green]Assembling {len(clips)} clips...[/green]")
    result = assembler.assemble_timeline(clips, output_path)
    console.print(f"[green]Output:[/green] {result}")


# =============================================================================
# Main Entry Point
# =============================================================================


if __name__ == "__main__":
    main()
