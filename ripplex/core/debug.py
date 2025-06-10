"""Debug visualization for flow execution."""
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.syntax import Syntax

@dataclass
class NodeInfo:
    """Information about a flow node."""
    id: int
    code: str
    status: str = "pending"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[Exception] = None
    result: Any = None
    dependencies: set = field(default_factory=set)
    
    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

class FlowDebugger:
    """Visual debugger for flow execution."""
    
    def __init__(self, nodes: List[Dict], source_code: str = ""):
        self.nodes = [NodeInfo(
            id=i,
            code=self._get_node_code(node),
            dependencies=node.get('deps', set())
        ) for i, node in enumerate(nodes)]
        self.source_code = source_code
        self.console = Console()
        self.live: Optional[Live] = None
        self.start_time = time.time()
        
    def _get_node_code(self, node: Dict) -> str:
        """Extract readable code from node."""
        # This is a simplified version - in reality, we'd decompile the code object
        return f"Node {node.get('code', 'unknown')}"
    
    def start(self):
        """Start the live display."""
        self.live = Live(self._build_layout(), refresh_per_second=10, console=self.console)
        self.live.start()
    
    def stop(self):
        """Stop the live display."""
        if self.live:
            self.live.stop()
    
    def update_node(self, node_id: int, status: str, error: Optional[Exception] = None, result: Any = None):
        """Update node status."""
        node = self.nodes[node_id]
        node.status = status
        
        if status == "running":
            node.start_time = time.time()
        elif status in ["done", "error"]:
            node.end_time = time.time()
            node.error = error
            node.result = result
        
        if self.live:
            self.live.update(self._build_layout())
    
    def _build_layout(self) -> Layout:
        """Build the debug layout."""
        layout = Layout()
        
        # Create status table
        table = Table(title="Flow Execution Status")
        table.add_column("Node", justify="right", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Dependencies", justify="left")
        
        for node in self.nodes:
            status_style = {
                "pending": "dim",
                "running": "yellow",
                "done": "green",
                "error": "red"
            }.get(node.status, "white")
            
            duration = f"{node.duration:.2f}s" if node.duration else "-"
            deps = ", ".join(str(d) for d in node.dependencies) or "none"
            
            table.add_row(
                str(node.id),
                f"[{status_style}]{node.status}[/{status_style}]",
                duration,
                deps
            )
        
        # Create summary panel
        elapsed = time.time() - self.start_time
        completed = sum(1 for n in self.nodes if n.status == "done")
        errors = sum(1 for n in self.nodes if n.status == "error")
        
        summary = f"""
Elapsed: {elapsed:.2f}s
Completed: {completed}/{len(self.nodes)}
Errors: {errors}
        """.strip()
        
        layout.split_column(
            Layout(Panel(table, title="Execution Progress"), size=15),
            Layout(Panel(summary, title="Summary"), size=5)
        )
        
        return layout

class LoopDebugger:
    """Simple progress tracker for loop execution."""
    
    def __init__(self, total: int, desc: str = "Processing"):
        self.total = total
        self.desc = desc
        self.completed = 0
        self.errors = 0
        self.console = Console()
        self.live: Optional[Live] = None
        
    def start(self):
        """Start progress display."""
        from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
        
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        )
        self.task = self.progress.add_task(self.desc, total=self.total)
        self.live = Live(self.progress, console=self.console)
        self.live.start()
    
    def update(self, success: bool = True):
        """Update progress."""
        if not success:
            self.errors += 1
        self.completed += 1
        
        if self.progress and self.task is not None:
            self.progress.update(self.task, advance=1)
    
    def stop(self):
        """Stop progress display."""
        if self.live:
            self.live.stop()
            if self.errors > 0:
                self.console.print(f"[red]Completed with {self.errors} errors[/red]")