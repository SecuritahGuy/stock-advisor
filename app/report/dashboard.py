"""
CLI dashboard for displaying portfolio information and trading signals.
"""
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dashboard")

# Initialize Rich console
console = Console()


def create_portfolio_table(portfolio_data):
    """
    Create a Rich table for portfolio positions.
    
    Args:
        portfolio_data (dict): Portfolio valuation data
        
    Returns:
        rich.table.Table: Table for display
    """
    table = Table(title="Portfolio Positions")
    
    # Add columns
    table.add_column("Ticker", style="cyan")
    table.add_column("Shares", justify="right")
    table.add_column("Cost Basis", justify="right")
    table.add_column("Current Price", justify="right")
    table.add_column("Current Value", justify="right")
    table.add_column("P/L", justify="right")
    table.add_column("P/L %", justify="right")
    
    # Add position rows
    for position in portfolio_data['positions']:
        # Determine P/L color
        pl_color = "green" if position['pl'] >= 0 else "red"
        
        table.add_row(
            position['ticker'],
            f"{position['shares']:.2f}",
            f"${position['cost_basis']:.2f}",
            f"${position.get('current_price', 0):.2f}",
            f"${position['current_value']:.2f}",
            f"${position['pl']:.2f}", 
            f"{position['pl_pct']:.2f}%",
            style=None,
            end_section=(position == portfolio_data['positions'][-1])
        )
    
    # Add totals row
    table.add_row(
        "TOTAL",
        "",
        f"${portfolio_data['total_cost']:.2f}",
        "",
        f"${portfolio_data['total_value']:.2f}",
        f"${portfolio_data['total_pl']:.2f}",
        f"{portfolio_data['total_pl_pct']:.2f}%",
        style="bold"
    )
    
    return table


def create_signals_table(signals):
    """
    Create a Rich table for trading signals.
    
    Args:
        signals (list): List of Signal objects
        
    Returns:
        rich.table.Table: Table for display
    """
    table = Table(title="Recent Trading Signals")
    
    # Add columns
    table.add_column("Timestamp", style="dim")
    table.add_column("Ticker", style="cyan")
    table.add_column("Action")
    table.add_column("Price", justify="right")
    table.add_column("Strength")
    table.add_column("Reason")
    
    # Add signal rows
    for signal in signals:
        # Determine action color
        action_color = "green" if signal.action.value == "BUY" else "red"
        
        table.add_row(
            signal.timestamp.strftime("%Y-%m-%d %H:%M"),
            signal.ticker,
            Text(signal.action.value, style=action_color),
            f"${signal.price:.2f}",
            signal.strength.value,
            signal.reason
        )
    
    return table


def create_metrics_table(metrics):
    """
    Create a Rich table for portfolio metrics.
    
    Args:
        metrics (dict): Portfolio performance metrics
        
    Returns:
        rich.table.Table: Table for display
    """
    table = Table(title=f"Performance Metrics ({metrics.get('period', 'all').capitalize()})")
    
    # Add columns
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    
    # Add metric rows
    if 'start_date' in metrics and 'end_date' in metrics:
        table.add_row("Period", f"{metrics['start_date'].strftime('%Y-%m-%d')} to {metrics['end_date'].strftime('%Y-%m-%d')}")
    
    if 'start_value' in metrics and 'end_value' in metrics:
        table.add_row("Start Value", f"${metrics['start_value']:.2f}")
        table.add_row("End Value", f"${metrics['end_value']:.2f}")
    
    if 'absolute_return' in metrics:
        return_color = "green" if metrics['absolute_return'] >= 0 else "red"
        table.add_row("Absolute Return", Text(f"${metrics['absolute_return']:.2f}", style=return_color))
    
    if 'percent_return' in metrics:
        pct_color = "green" if metrics['percent_return'] >= 0 else "red"
        table.add_row("Percent Return", Text(f"{metrics['percent_return']:.2f}%", style=pct_color))
    
    if 'annualized_return' in metrics:
        ann_color = "green" if metrics['annualized_return'] >= 0 else "red"
        table.add_row("Annualized Return", Text(f"{metrics['annualized_return']:.2f}%", style=ann_color))
    
    if 'volatility' in metrics:
        table.add_row("Volatility (Ann.)", f"{metrics['volatility']:.2f}%")
    
    if 'sharpe_ratio' in metrics:
        table.add_row("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")
    
    if 'days_held' in metrics:
        table.add_row("Days Held", f"{metrics['days_held']}")
    
    return table


def display_empty_portfolio_message():
    """
    Display a message on the dashboard when the portfolio is empty.
    """
    print("\n[bold yellow]Your portfolio is currently empty. Add positions to start tracking performance.[/bold yellow]\n")


def display_dashboard(portfolio_data, signals, metrics):
    """
    Display the main dashboard with portfolio, signals, and metrics.
    
    Args:
        portfolio_data (dict): Portfolio valuation data
        signals (list): List of Signal objects
        metrics (dict): Portfolio performance metrics
    """
    console.clear()
    
    # Create layout
    layout = Layout()
    
    # Split into sections
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    # Add header
    title = Text("STOCK ADVISOR DASHBOARD", style="bold blue")
    subtitle = Text("Real-time portfolio tracking and trading signals", style="italic")
    header_text = title + "\n" + subtitle
    layout["header"].update(Align.center(header_text))
    
    # Split main section
    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right", ratio=2)
    )
    
    # Add portfolio metrics to left panel
    layout["left"].update(create_metrics_table(metrics))
    
    # Split right section for portfolio and signals
    layout["right"].split(
        Layout(name="portfolio"),
        Layout(name="signals")
    )
    
    # Add portfolio table
    if not portfolio_data['positions']:
        display_empty_portfolio_message()
    else:
        layout["portfolio"].update(create_portfolio_table(portfolio_data))
    
    # Add signals table
    layout["signals"].update(create_signals_table(signals))
    
    # Add footer
    current_time = Text(f"Last Updated: {signals[0].timestamp.strftime('%Y-%m-%d %H:%M:%S')}" if signals else "No signals yet")
    disclaimer = Text("This is not financial advice. Use at your own risk.", style="dim italic")
    footer_text = current_time + "\n" + disclaimer
    layout["footer"].update(Align.center(footer_text))
    
    # Render the layout
    console.print(layout)


def display_error(message):
    """
    Display an error message.
    
    Args:
        message (str): Error message to display
    """
    console.print(Panel(message, title="Error", style="bold red"))
