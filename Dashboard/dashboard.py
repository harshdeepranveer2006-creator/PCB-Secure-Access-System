import serial
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule
from rich.console import Group
from rich import box
import time
from datetime import datetime

# ── Config ───────────────────────────────────────────────────
PORT = "/dev/cu.usbserial-10"
BAUD = 9600
# ─────────────────────────────────────────────────────────────

state = {
    "status":       "STANDBY",
    "last_key":     "-",
    "input_so_far": "",
    "attempts":     0,
    "granted":      0,
    "denied":       0,
    "log":          [],
    "uptime_start": time.time(),
}

VAULT_LOCKED = (
    "  ╔══════════════════╗  \n"
    "  ║  ┌────────────┐  ║  \n"
    "  ║  │  ╔══════╗  │  ║  \n"
    "  ║  │  ║ (  ) ║  │  ║  \n"
    "  ║  │  ║──────║  │  ║  \n"
    "  ║  │  ║ (  ) ║  │  ║  \n"
    "  ║  │  ╚══════╝  │  ║  \n"
    "  ║  └────────────┘  ║  \n"
    "  ║   ████████████   ║  \n"
    "  ╚═══════[■]════════╝  "
)

VAULT_OPEN = (
    "  ╔══════════════════╗    \n"
    "  ║  ┌────────────┐  ║  / \n"
    "  ║  │  ╔══════╗  │  ║ /  \n"
    "  ║  │  ║ (  ) ║  │  ║/   \n"
    "  ║  │  ║──────║  │  ║    \n"
    "  ║  │  ║ (  ) ║  │       \n"
    "  ║  │  ╚══════╝  │       \n"
    "  ║  └────────────┘       \n"
    "  ║   ████████████        \n"
    "  ╚═══════[□]════════     "
)

VAULT_DENIED = (
    "  ╔══════════════════╗  \n"
    "  ║  ┌────────────┐  ║  \n"
    "  ║  │  ╔══════╗  │  ║  \n"
    "  ║  │  ║ (╳╳) ║  │  ║  \n"
    "  ║  │  ║══╳╳══║  │  ║  \n"
    "  ║  │  ║ (╳╳) ║  │  ║  \n"
    "  ║  │  ╚══════╝  │  ║  \n"
    "  ║  └────────────┘  ║  \n"
    "  ║   ████████████   ║  \n"
    "  ╚═══════[■]════════╝  "
)

VAULT_VERIFY = (
    "  ╔══════════════════╗  \n"
    "  ║  ┌────────────┐  ║  \n"
    "  ║  │  ╔══════╗  │  ║  \n"
    "  ║  │  ║ ( ? ) ║  │  ║  \n"
    "  ║  │  ║──?──?─║  │  ║  \n"
    "  ║  │  ║ ( ? ) ║  │  ║  \n"
    "  ║  │  ╚══════╝  │  ║  \n"
    "  ║  └────────────┘  ║  \n"
    "  ║   ████████████   ║  \n"
    "  ╚═══════[?]════════╝  "
)

def parse_line(line):
    line = line.strip()
    if not line:
        return
    timestamp = datetime.now().strftime("%H:%M:%S")

    if line.startswith("Key pressed:"):
        state["last_key"] = line.split(":")[-1].strip()
        state["status"] = "TYPING"

    elif line.startswith("Input so far:"):
        raw = line.split(":")[-1].strip()
        state["input_so_far"] = "⬤   " * len(raw)

    elif line == "Input cleared.":
        state["input_so_far"] = ""
        state["status"] = "STANDBY"
        log_add(timestamp, Text("SEQUENCE CLEARED", style="yellow"))

    elif line == "Verifying...":
        state["status"] = "VERIFYING"

    elif line == "ACCESS GRANTED":
        state["status"] = "GRANTED"
        state["granted"] += 1
        state["attempts"] += 1
        state["input_so_far"] = ""
        log_add(timestamp, Text("VAULT UNLOCKED  >>>  ACCESS GRANTED", style="bold green"))

    elif line == "ACCESS DENIED":
        state["status"] = "DENIED"
        state["denied"] += 1
        state["attempts"] += 1
        state["input_so_far"] = ""
        log_add(timestamp, Text("BREACH ATTEMPT  >>>  ACCESS DENIED", style="bold red"))

def log_add(timestamp, message):
    entry = Text()
    entry.append(f"  {timestamp}  ║  ", style="bold dim")
    entry.append_text(message)
    state["log"].append(entry)
    if len(state["log"]) > 7:
        state["log"].pop(0)

def vault_panel():
    s = state["status"]

    if s == "GRANTED":
        art    = Text(VAULT_OPEN,   style="bold green",  justify="center")
        badge  = Text(" ✔✔  VAULT UNLOCKED  ✔✔ ", style="bold black on green")
        border = "green"
        title  = "🔓   V A U L T  —  O P E N"
    elif s == "DENIED":
        art    = Text(VAULT_DENIED, style="bold red",    justify="center")
        badge  = Text(" ✘✘  ACCESS DENIED  ✘✘ ",  style="bold white on red")
        border = "red"
        title  = "🔒   V A U L T  —  S E A L E D"
    elif s == "VERIFYING":
        art    = Text(VAULT_VERIFY, style="bold yellow", justify="center")
        badge  = Text(" ◈◈  PROCESSING...  ◈◈ ",  style="bold black on yellow")
        border = "yellow"
        title  = "⟳   V A U L T  —  V E R I F Y I N G"
    elif s == "TYPING":
        art    = Text(VAULT_LOCKED, style="bold cyan",   justify="center")
        badge  = Text(" ⌨⌨  SEQUENCE INPUT  ⌨⌨ ", style="bold cyan")
        border = "cyan"
        title  = "⌨    V A U L T  —  I N P U T"
    else:
        art    = Text(VAULT_LOCKED, style="cyan",        justify="center")
        badge  = Text(" ◉◉  SYSTEM STANDBY  ◉◉ ",  style="dim")
        border = "bright_black"
        title  = "◉   V A U L T  —  S T A N D B Y"

    content = Group(
        Text(""),
        Align(art,   align="center"),
        Text(""),
        Rule(style="dim"),
        Align(badge, align="center"),
        Text(""),
    )
    return Panel(content, title=title, border_style=border,
                 box=box.HEAVY, padding=(0, 1))

def input_panel():
    seq = Text(state["input_so_far"], style="bold cyan", justify="center") \
          if state["input_so_far"] else Text("─ ─  AWAITING SEQUENCE  ─ ─", style="dim", justify="center")

    hint = Text("[ D ] CONFIRM          [ * ] CLEAR", style="dim", justify="center")

    content = Group(
        Text(""),
        Align(Text("C O M B I N A T I O N   I N P U T", style="dim"), align="center"),
        Text(""),
        Rule(characters="═", style="dim"),
        Text(""),
        Align(seq,  align="center"),
        Text(""),
        Rule(characters="═", style="dim"),
        Text(""),
        Align(hint, align="center"),
        Text(""),
    )
    return Panel(content, title="⬡   K E Y P A D   E N T R Y",
                 border_style="cyan", box=box.HEAVY, padding=(0, 2))

def stats_panel():
    attempts = state["attempts"]
    granted  = state["granted"]
    denied   = state["denied"]
    rate     = int((granted / attempts * 100) if attempts > 0 else 0)

    filled   = int(rate / 5)
    bar = Text()
    bar.append("▰" * filled,        style="bold green")
    bar.append("▱" * (20 - filled), style="dim")
    bar.append(f"  {rate}%",         style="bold white")

    uptime_secs = int(time.time() - state["uptime_start"])
    mins, secs  = divmod(uptime_secs, 60)
    hrs,  mins  = divmod(mins, 60)

    t = Table(box=None, show_header=False, padding=(0, 2))
    t.add_column(style="dim",     min_width=16)
    t.add_column(justify="right", min_width=10)

    t.add_row(Text("LAST KEY",     style="dim"), Text(f"  {state['last_key']}", style="bold white"))
    t.add_row(Rule(style="dim"),   Rule(style="dim"))
    t.add_row(Text("ATTEMPTS",     style="dim"), Text(str(attempts), style="bold white"))
    t.add_row(Text("GRANTED",      style="dim"), Text(str(granted),  style="bold green"))
    t.add_row(Text("DENIED",       style="dim"), Text(str(denied),   style="bold red"))
    t.add_row(Rule(style="dim"),   Rule(style="dim"))
    t.add_row(Text("SUCCESS RATE", style="dim"), Text(""))
    t.add_row(bar,                 Text(""))
    t.add_row(Rule(style="dim"),   Rule(style="dim"))
    t.add_row(Text("UPTIME",       style="dim"), Text(f"{hrs:02d}:{mins:02d}:{secs:02d}", style="bold cyan"))

    return Panel(t, title="▣   S T A T I S T I C S",
                 border_style="bright_black", box=box.HEAVY, padding=(1, 1))

def log_panel():
    if state["log"]:
        lines = []
        for entry in state["log"]:
            lines.append(Text(""))
            lines.append(entry)
        content = Group(*lines)
    else:
        content = Text("  ─ ─  NO EVENTS RECORDED  ─ ─", style="dim")

    return Panel(content, title="▤   S E C U R I T Y   L O G",
                 border_style="bright_black", box=box.HEAVY, padding=(0, 2))

def build_dashboard():
    now = datetime.now().strftime("%A   %d %B %Y     %H : %M : %S")

    top_rule  = Rule(characters="═══", style="cyan")
    title     = Text(
        "V  A  U  L  T      C  O  N  T  R  O  L      S  Y  S  T  E  M",
        style="bold cyan", justify="center")
    sub       = Text(now, style="dim cyan", justify="center")
    bot_rule  = Rule(characters="═══", style="cyan")

    header = Group(
        Text(""),
        top_rule,
        Text(""),
        Align(title, align="center"),
        Align(sub,   align="center"),
        Text(""),
        bot_rule,
    )

    top = Columns([vault_panel(), input_panel(), stats_panel()], equal=True)

    return Panel(
        Group(header, Text(""), top, Text(""), log_panel()),
        border_style="cyan",
        box=box.DOUBLE_EDGE,
        padding=(1, 3),
    )

def main():
    print(f"Initialising vault connection on {PORT}...")
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
    except Exception as e:
        print(f"[ERROR] Could not open port: {e}")
        print("Check your PORT setting at the top of the file.")
        return

    print("Connection established. Launching vault dashboard...\n")
    time.sleep(2)

    with Live(build_dashboard(), refresh_per_second=4, screen=True) as live:
        while True:
            try:
                raw = ser.readline()
                if raw:
                    parse_line(raw.decode("utf-8", errors="ignore"))
                live.update(build_dashboard())
            except KeyboardInterrupt:
                print("\nVault dashboard closed.")
                break
            except Exception as e:
                log_add(datetime.now().strftime("%H:%M:%S"),
                        Text(f"SYSTEM ERROR: {e}", style="red"))
                live.update(build_dashboard())

if __name__ == "__main__":
    main()