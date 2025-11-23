#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI utilities module
"""

import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED

console = Console()

def get_version():
    """Get version from __version__.py"""
    try:
        version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '__version__.py')
        version = {}
        with open(version_file, 'r', encoding='utf-8') as f:
            exec(f.read(), version)
        return version.get('__version__', '1.0.3')
    except:
        return '1.0.0'

def is_cli_mode():
    """Check if running in CLI mode"""
    return sys.stdin.isatty()

def print_banner(force=False):
    """Print banner only in CLI mode unless forced"""
    if not is_cli_mode() and not force:
        return
        
    version = get_version()
    banner = f"""
    🌊  EndAbyss  🌀
    ----------------------
     _____           _    ___  _                       
    |  ___|         | |  / _ \| |                      
    | |__  _ __   __| | / /_\ \ |__  _   _ ___ ___    
    |  __|| '_ \ / _` | |  _  | '_ \| | | / __/ __|   
    | |___| | | | (_| | | | | | |_) | |_| \__ \__ \   
    \____/|_| |_|\__,_| \_| |_/_.__/ \__, |___/___/   
                                      __/ |            
                                     |___/         v{version}
    """
    
    banner_panel = Panel(
        banner,
        title=r"[bold cyan]Red Teaming and Web Bug Bounty Fast Endpoint Discovery Tool[/]",
        subtitle=r"[bold blue]by. arrester (https://github.com/arrester/endabyss)[/]",
        style="bold blue",
        box=ROUNDED
    )
    console.print(banner_panel)

def print_usage():
    """Print usage information"""
    usage_table = Table(
        title="[bold cyan]EndAbyss Usage Guide[/]",
        box=ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    
    usage_table.add_column("Command", style="cyan", justify="left")
    usage_table.add_column("Description", style="white", justify="left")
    usage_table.add_column("Example", style="green", justify="left")
    
    usage_table.add_row(
        "endabyss -t <url>",
        "Scan single target",
        "endabyss -t http://example.com"
    )
    usage_table.add_row(
        "endabyss -t <url> -o <file>",
        "Save results to file",
        "endabyss -t http://example.com -o results.txt"
    )
    usage_table.add_row(
        "endabyss -t <url> -m d",
        "Enable dynamic scanning",
        "endabyss -t http://example.com -m d"
    )
    usage_table.add_row(
        "endabyss -tf <file>",
        "Scan multiple targets from file",
        "endabyss -tf targets.txt"
    )
    
    options_table = Table(
        title="[bold cyan]Available Options[/]",
        box=ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    
    options_table.add_column("Option", style="cyan", justify="left")
    options_table.add_column("Description", style="white", justify="left")
    
    options_table.add_row("-h, --help", "Show this help message")
    options_table.add_row("-t, --target", "Target URL or domain (e.g. http://example.com)")
    options_table.add_row("-tf, --targetfile", "File containing list of targets")
    options_table.add_row("-m, --mode", "Scan mode: static (default) or dynamic")
    options_table.add_row("-o, --output", "Output file to save results")
    options_table.add_row("-v, --verbose", "Increase output verbosity (-v, -vv, -vvv)")
    options_table.add_row("-d, --depth", "Crawling depth (default: 5, unlimited: 0)")
    options_table.add_row("-c, --concurrency", "Number of concurrent requests (default: 10)")
    options_table.add_row("-s, --session", "Session file path (cookies or JSON)")
    options_table.add_row("-ds, --dirscan", "Enable directory scanning")
    options_table.add_row("-w, --wordlist", "Wordlist file for directory scanning")
    options_table.add_row("--delay", "Delay between requests in seconds (default: 0)")
    options_table.add_row("--random-delay", "Random delay range (e.g. 1-3)")
    options_table.add_row("--timeout", "Request timeout in seconds (default: 30)")
    options_table.add_row("--retry", "Number of retries on failure (default: 3)")
    options_table.add_row("--user-agent", "Custom User-Agent string")
    options_table.add_row("--proxy", "Proxy URL (HTTP/HTTPS/SOCKS5)")
    options_table.add_row("--rate-limit", "Rate limit (requests per second)")
    options_table.add_row("--headless", "Run browser in headless mode (dynamic mode)")
    options_table.add_row("--wait-time", "Wait time for page load in seconds (default: 3)")
    options_table.add_row("--exclude-ext", "Exclude file extensions (comma-separated)")
    options_table.add_row("--include-ext", "Include only these extensions (comma-separated)")
    options_table.add_row("--exclude-path", "Exclude paths (comma-separated)")
    options_table.add_row("--include-path", "Include only these paths (comma-separated)")
    options_table.add_row("--min-params", "Minimum number of parameters to include")
    options_table.add_row("--status-codes", "HTTP status codes to include (comma-separated)")
    options_table.add_row("--error-log", "File to save error logs")
    options_table.add_row("-pipeurl", "Output URLs only for pipeline")
    options_table.add_row("-pipeendpoint", "Output endpoints only for pipeline")
    options_table.add_row("-pipeparam", "Output parameters only for pipeline")
    options_table.add_row("-pipejson", "Output all results in JSON format for pipeline")
    options_table.add_row("--silent", "Silent mode (no banner, no progress output)")
    
    console.print("\n[bold cyan]Description:[/]")
    console.print("EndAbyss is a fast endpoint discovery tool that crawls websites to collect endpoints and parameters for bug bounty and red team operations.\n")
    
    console.print(usage_table)
    console.print("\n")
    console.print(options_table)
    console.print("\n[bold cyan]Note:[/] Configure default settings in config.yaml\n")

def print_status(message, status="info", cli_only=True):
    """Print status messages with color coding"""
    if cli_only and not is_cli_mode():
        return
        
    colors = {
        "info": "blue",
        "success": "green",
        "warning": "yellow", 
        "error": "red"
    }
    
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    console.print(f"[bold {colors[status]}]{icons[status]} {message}[/]")

def main():
    """Main entry point for CLI"""
    if len(sys.argv) == 1:
        print_banner(force=True)
        print_usage()
        sys.exit(0)

if __name__ == "__main__":
    main()
