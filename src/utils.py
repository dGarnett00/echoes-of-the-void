"""Utility functions for display, formatting, and text effects."""

import sys
import time
import os
from typing import Optional

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False


# ── Color constants ──────────────────────────────────────────────────────────

class Colors:
    """Terminal color codes."""

    if COLORAMA_AVAILABLE:
        CORA      = Fore.CYAN
        RESONANCE = Fore.MAGENTA
        WARNING   = Fore.YELLOW
        CRITICAL  = Fore.RED
        NPC       = Fore.GREEN
        ROOM      = Fore.BLUE
        RESET     = Style.RESET_ALL
        DIM       = Style.DIM
        BRIGHT    = Style.BRIGHT
        WHITE     = Fore.WHITE
    else:
        CORA      = ""
        RESONANCE = ""
        WARNING   = ""
        CRITICAL  = ""
        NPC       = ""
        ROOM      = ""
        RESET     = ""
        DIM       = ""
        BRIGHT    = ""
        WHITE     = ""


# ── Typewriter effect ────────────────────────────────────────────────────────

TYPEWRITER_SPEED: float = 0.025   # seconds per character (default)
TYPEWRITER_ENABLED: bool = True


def typewrite(text: str, speed: Optional[float] = None, color: str = "") -> None:
    """Print text with a typewriter effect; press Enter to skip."""
    if not TYPEWRITER_ENABLED or not text:
        print(color + text + Colors.RESET)
        return

    delay = speed if speed is not None else TYPEWRITER_SPEED
    output = color + text + Colors.RESET

    for char in output:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def slow_print(text: str, color: str = "") -> None:
    """Print text slowly (story prose speed)."""
    typewrite(text, speed=0.03, color=color)


def fast_print(text: str, color: str = "") -> None:
    """Print text quickly (UI feedback speed)."""
    typewrite(text, speed=0.005, color=color)


def instant_print(text: str, color: str = "") -> None:
    """Print text instantly."""
    print(color + text + Colors.RESET)


# ── Display helpers ──────────────────────────────────────────────────────────

TERMINAL_WIDTH: int = 78


def divider(char: str = "─", width: int = TERMINAL_WIDTH, color: str = "") -> None:
    """Print a horizontal divider."""
    print(color + char * width + Colors.RESET)


def header(title: str, color: str = Colors.ROOM) -> None:
    """Print a styled header."""
    pad = max(0, TERMINAL_WIDTH - len(title) - 4)
    left = pad // 2
    right = pad - left
    print(color + "══" + "═" * left + f" {title} " + "═" * right + "══" + Colors.RESET)


def box(lines: list, color: str = "") -> None:
    """Print text inside a simple box."""
    width = max(len(l) for l in lines) + 4
    print(color + "┌" + "─" * (width - 2) + "┐" + Colors.RESET)
    for line in lines:
        padding = width - 4 - len(line)
        print(color + "│ " + line + " " * padding + " │" + Colors.RESET)
    print(color + "└" + "─" * (width - 2) + "┘" + Colors.RESET)


def resource_bar(label: str, value: float, max_value: float = 100.0,
                 width: int = 20, color: str = "") -> str:
    """Generate a text progress bar for a resource."""
    pct = max(0.0, min(1.0, value / max_value))
    filled = int(pct * width)
    empty  = width - filled

    if pct > 0.6:
        bar_color = Fore.GREEN if COLORAMA_AVAILABLE else ""
    elif pct > 0.3:
        bar_color = Fore.YELLOW if COLORAMA_AVAILABLE else ""
    else:
        bar_color = Fore.RED if COLORAMA_AVAILABLE else ""

    bar = bar_color + "█" * filled + Colors.DIM + "░" * empty + Colors.RESET
    return f"{color}{label:<12}{Colors.RESET} [{bar}] {value:5.1f}"


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


# ── ASCII Art ────────────────────────────────────────────────────────────────

TITLE_ART = r"""
  ███████╗ ██████╗██╗  ██╗ ██████╗ ███████╗███████╗
  ██╔════╝██╔════╝██║  ██║██╔═══██╗██╔════╝██╔════╝
  █████╗  ██║     ███████║██║   ██║█████╗  ███████╗
  ██╔══╝  ██║     ██╔══██║██║   ██║██╔══╝  ╚════██║
  ███████╗╚██████╗██║  ██║╚██████╔╝███████╗███████║
  ╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝

         ██████╗ ███████╗    ████████╗██╗  ██╗███████╗
         ██╔══██╗██╔════╝    ╚══██╔══╝██║  ██║██╔════╝
         ██║  ██║█████╗         ██║   ███████║█████╗
         ██║  ██║██╔══╝         ██║   ██╔══██║██╔══╝
         ██████╔╝██║            ██║   ██║  ██║███████╗
         ╚═════╝ ╚═╝            ╚═╝   ╚═╝  ╚═╝╚══════╝

            ██╗   ██╗ ██████╗ ██╗██████╗
            ██║   ██║██╔═══██╗██║██╔══██╗
            ██║   ██║██║   ██║██║██║  ██║
            ╚██╗ ██╔╝██║   ██║██║██║  ██║
             ╚████╔╝ ╚██████╔╝██║██████╔╝
              ╚═══╝   ╚═════╝ ╚═╝╚═════╝

  ══════════════════════════════════════════════════════
       UNS Meridian · Year 2847 · Cycle Unknown
         "Not all who drift are lost."
  ══════════════════════════════════════════════════════
"""


def show_title() -> None:
    """Display the title screen."""
    if COLORAMA_AVAILABLE:
        print(Fore.CYAN + TITLE_ART + Style.RESET_ALL)
    else:
        print(TITLE_ART)


# ── Input helpers ────────────────────────────────────────────────────────────

def prompt(text: str = "> ") -> str:
    """Get player input with a styled prompt."""
    try:
        color = Colors.BRIGHT + Colors.WHITE if COLORAMA_AVAILABLE else ""
        return input(color + text + Colors.RESET).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "quit"


def press_enter(message: str = "[ Press ENTER to continue ]") -> None:
    """Pause and wait for player to press Enter."""
    try:
        input(Colors.DIM + message + Colors.RESET)
    except (EOFError, KeyboardInterrupt):
        pass


# ── Status display ───────────────────────────────────────────────────────────

def display_status(resources: dict, cycle: int, location: str) -> None:
    """Print the current resource status panel."""
    header(f"STATUS — Cycle {cycle}", color=Colors.ROOM)
    instant_print(f"  Location : {location}", color=Colors.ROOM)
    divider("─", 40)
    instant_print(resource_bar("O₂",      resources.get("o2", 0),      100))
    instant_print(resource_bar("Power",   resources.get("power", 0),   100))
    instant_print(resource_bar("Rations", resources.get("rations", 0), 100))
    instant_print(resource_bar("Sanity",  resources.get("sanity", 0),  100))
    instant_print(resource_bar("Trust",   resources.get("trust", 0),   100))
    divider("─", 40)


def display_help() -> None:
    """Print the help screen."""
    header("COMMANDS", color=Colors.CORA)
    commands = [
        ("EXAMINE / LOOK [target]",   "Inspect an object, person, or room"),
        ("MOVE / GO [direction/room]","Move to an adjacent area"),
        ("TALK [NPC name]",           "Speak with a crew member"),
        ("QUERY CORA [question]",     "Ask the ship AI a question"),
        ("ALLOCATE [system] [amount]","Distribute power to subsystems"),
        ("USE [item]",                "Use an item from your inventory"),
        ("REPAIR [target]",           "Attempt to repair a damaged system"),
        ("THEORIZE [note]",           "Record a theory on your theory board"),
        ("REST",                      "Rest to recover sanity (costs 1 cycle)"),
        ("CONFRONT [NPC name]",       "Confront an NPC with evidence"),
        ("INVENTORY / INV",           "Show your inventory"),
        ("STATUS",                    "Show resource status panel"),
        ("HELP",                      "Show this help screen"),
        ("SAVE [slot]",               "Save game (slot 1-3, default: 1)"),
        ("LOAD [slot]",               "Load game from a save slot"),
        ("QUIT / EXIT",               "Quit the game"),
    ]
    for cmd, desc in commands:
        instant_print(f"  {Colors.CORA}{cmd:<35}{Colors.RESET} {desc}")
    divider()
