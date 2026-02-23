
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from swarm_v2.core.swarm_engine import SwarmEngine

console = Console()

async def interactive_cli():
    engine = SwarmEngine()
    
    console.print(Panel.fit(
        "[bold green]TRM AGENT SWARM V2[/bold green]\n"
        "[dim]Neural Expert Collaborative Framework[/dim]",
        border_style="green"
    ))

    table = Table(title="Expert Team Registry", border_style="cyan")
    table.add_column("Expert", style="bold magenta")
    table.add_column("Role", style="yellow")
    table.add_column("Specialties", style="dim italic")

    for role, agent in engine.team.items():
        table.add_row(agent.persona.name, role, ", ".join(agent.persona.specialties))
    
    console.print(table)

    while True:
        console.print("\n[bold cyan]Choose Command:[/bold cyan]")
        console.print("1. [green]BROADCAST[/green] (Ask whole team)")
        table_cmd = Table.grid(padding=(0, 2))
        table_cmd.add_row("2. [yellow]DELEGATE[/yellow] (Target expert)", "3. [red]EXIT[/red]")
        console.print(table_cmd)

        choice = await asyncio.to_thread(input, "\n>> ")
        
        if choice == "3":
            console.print("[bold red]Shutting down swarm...[/bold red]")
            break
        
        if choice == "1":
            task = await asyncio.to_thread(input, "Enter task for the team: ")
            console.print(f"\n[bold green]Broadcasting to Swarm...[/bold green]")
            responses = await engine.broadcast(task)
            
            for role, res in responses.items():
                console.print(Panel(res, title=f"[bold]{role} ({engine.team[role].persona.name})[/bold]", border_style="green"))
        
        elif choice == "2":
            role = await asyncio.to_thread(input, "Enter expert role: ")
            task = await asyncio.to_thread(input, "Enter detailed task: ")
            console.print(f"\n[bold yellow]Delegating to {role}...[/bold yellow]")
            res = await engine.delegate_to(role, task)
            console.print(Panel(res, title=f"[bold]{role}[/bold]", border_style="yellow"))

if __name__ == "__main__":
    asyncio.run(interactive_cli())
