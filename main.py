from __future__ import annotations

import argparse
import curses
import json
import random
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None  # type: ignore[assignment]


CONFIG_DIR = Path.home() / ".koalatype"
CONFIG_FILE = CONFIG_DIR / "config.toml"
HISTORY_FILE = CONFIG_DIR / "history.json"
ENGLISH_WORDS_FILE = Path(__file__).with_name("1000-most-common-words.txt")
SNIPPETS_DIR = Path(__file__).with_name("snippets")
PYTHON_SNIPPETS_FILE = SNIPPETS_DIR / "python_snippets.txt"
JS_SNIPPETS_FILE = SNIPPETS_DIR / "javascript_snippets.txt"
JAVA_SNIPPETS_FILE = SNIPPETS_DIR / "java_snippets.txt"
GO_SNIPPETS_FILE = SNIPPETS_DIR / "go_snippets.txt"


@dataclass(frozen=True)
class WordPack:
    name: str
    description: str
    words: tuple[str, ...]
    snippets: tuple[str, ...] = ()  # raw code strings with newlines


@dataclass(frozen=True)
class CodeLine:
    indent: int
    tokens: tuple[str, ...]


@dataclass
class TestStats:
    backspace_count: int = 0
    char_misses: dict[str, int] = field(default_factory=dict)
    total_keystrokes: int = 0


def _load_english_words() -> tuple[str, ...]:
    if not ENGLISH_WORDS_FILE.exists():
        raise FileNotFoundError(
            "Missing 1000-most-common-words.txt next to main.py"
        )
    words: list[str] = []
    for line in ENGLISH_WORDS_FILE.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if cleaned:
            words.append(cleaned)
    if not words:
        raise ValueError("English word list file is empty")
    return tuple(words)


def _load_snippets(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    raw = path.read_text(encoding="utf-8")
    snippets: list[str] = []
    for block in raw.split("\n---\n"):
        lines = block.strip().splitlines()
        if lines and lines[0].startswith("#"):
            lines = lines[1:]
        code = "\n".join(lines).strip()
        if code:
            snippets.append(code)
    return tuple(snippets)


def _parse_code_lines(code: str) -> list[CodeLine]:
    result: list[CodeLine] = []
    for raw_line in code.splitlines():
        if not raw_line.strip():
            continue
        stripped = raw_line.lstrip()
        indent = len(raw_line) - len(stripped)
        tokens = tuple(stripped.split())
        if tokens:
            result.append(CodeLine(indent=indent, tokens=tokens))
    return result


def _filter_by_difficulty(
    words: tuple[str, ...], difficulty: str | None
) -> tuple[str, ...]:
    if difficulty is None:
        return words
    if difficulty == "easy":
        filtered = tuple(w for w in words if len(w) <= 4)
    elif difficulty == "medium":
        filtered = tuple(w for w in words if 4 < len(w) <= 7)
    elif difficulty == "hard":
        filtered = tuple(w for w in words if len(w) > 7)
    else:
        return words
    return filtered if filtered else words


def _build_word_packs() -> dict[str, WordPack]:
    packs: dict[str, WordPack] = {
        "python": WordPack(
            name="python",
            description="Python keywords and common identifiers",
            words=(
                "def", "class", "import", "from", "return", "yield", "lambda",
                "async", "await", "with", "as", "try", "except", "finally",
                "raise", "None", "True", "False", "list", "dict", "set",
                "tuple", "str", "int", "float", "bool", "len", "range",
                "print", "enumerate", "self", "isinstance", "property",
                "staticmethod", "classmethod", "super", "pass", "break",
                "continue", "elif", "else", "for", "while", "in", "not",
                "and", "or", "is", "del", "global", "nonlocal", "assert",
            ),
        ),
        "javascript": WordPack(
            name="javascript",
            description="JavaScript keywords and common identifiers",
            words=(
                "const", "let", "var", "function", "return", "if", "else",
                "for", "while", "do", "switch", "case", "break", "continue",
                "new", "this", "class", "extends", "super", "import", "export",
                "default", "from", "async", "await", "try", "catch", "finally",
                "throw", "typeof", "instanceof", "null", "undefined", "true",
                "false", "console", "log", "map", "filter", "reduce", "forEach",
                "push", "pop", "shift", "splice", "slice", "length", "Promise",
                "then", "catch", "fetch", "JSON", "parse", "stringify",
            ),
        ),
        "rust": WordPack(
            name="rust",
            description="Rust keywords and common identifiers",
            words=(
                "fn", "let", "mut", "const", "static", "struct", "enum",
                "impl", "trait", "pub", "mod", "use", "crate", "self",
                "super", "match", "if", "else", "for", "while", "loop",
                "break", "continue", "return", "async", "await", "move",
                "unsafe", "where", "type", "ref", "Box", "Vec", "String",
                "Option", "Result", "Some", "None", "Ok", "Err", "unwrap",
                "clone", "iter", "into", "from", "derive", "println", "macro",
            ),
        ),
        "go": WordPack(
            name="go",
            description="Go keywords and common identifiers",
            words=(
                "func", "var", "const", "type", "struct", "interface", "map",
                "chan", "go", "select", "case", "default", "if", "else",
                "for", "range", "switch", "break", "continue", "return",
                "defer", "panic", "recover", "package", "import", "nil",
                "true", "false", "error", "string", "int", "bool", "byte",
                "make", "append", "len", "cap", "new", "close", "delete",
                "fmt", "Println", "Sprintf", "Errorf", "context", "sync",
            ),
        ),
        "sql": WordPack(
            name="sql",
            description="SQL keywords and common identifiers",
            words=(
                "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES",
                "UPDATE", "SET", "DELETE", "CREATE", "TABLE", "ALTER", "DROP",
                "INDEX", "JOIN", "INNER", "LEFT", "RIGHT", "OUTER", "ON",
                "AND", "OR", "NOT", "IN", "BETWEEN", "LIKE", "IS", "NULL",
                "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET", "AS",
                "COUNT", "SUM", "AVG", "MIN", "MAX", "DISTINCT", "UNION",
                "EXISTS", "CASE", "WHEN", "THEN", "ELSE", "END", "PRIMARY",
                "KEY", "FOREIGN", "REFERENCES", "CONSTRAINT", "DEFAULT",
            ),
        ),
        "java": WordPack(
            name="java",
            description="Java keywords and common identifiers",
            words=(
                "public", "private", "protected", "static", "final", "abstract",
                "class", "interface", "extends", "implements", "new", "this",
                "super", "return", "void", "int", "long", "double", "float",
                "boolean", "char", "byte", "short", "String", "if", "else",
                "for", "while", "do", "switch", "case", "break", "continue",
                "try", "catch", "finally", "throw", "throws", "import",
                "package", "null", "true", "false", "instanceof", "enum",
                "List", "Map", "Set", "HashMap", "ArrayList", "Optional",
                "Stream", "Collections", "Arrays", "Iterator", "Override",
                "System", "println", "toString", "equals", "hashCode",
            ),
        ),
    }
    english_words = _load_english_words()
    packs["english-1000"] = WordPack(
        name="english-1000",
        description=f"Common English words ({len(english_words)} words)",
        words=english_words,
    )
    snippets = _load_snippets(PYTHON_SNIPPETS_FILE)
    if snippets:
        all_tokens: list[str] = []
        for s in snippets:
            all_tokens.extend(s.split())
        packs["python-code"] = WordPack(
            name="python-code",
            description=f"Real Python code -- LeetCode solutions ({len(snippets)} snippets)",
            words=tuple(all_tokens),
            snippets=snippets,
        )
    js_snippets = _load_snippets(JS_SNIPPETS_FILE)
    if js_snippets:
        js_tokens: list[str] = []
        for s in js_snippets:
            js_tokens.extend(s.split())
        packs["javascript-code"] = WordPack(
            name="javascript-code",
            description=f"Real JavaScript code -- open-source snippets ({len(js_snippets)} snippets)",
            words=tuple(js_tokens),
            snippets=js_snippets,
        )
    java_snippets = _load_snippets(JAVA_SNIPPETS_FILE)
    if java_snippets:
        java_tokens: list[str] = []
        for s in java_snippets:
            java_tokens.extend(s.split())
        packs["java-code"] = WordPack(
            name="java-code",
            description=f"Real Java code -- open-source snippets ({len(java_snippets)} snippets)",
            words=tuple(java_tokens),
            snippets=java_snippets,
        )
    go_snippets = _load_snippets(GO_SNIPPETS_FILE)
    if go_snippets:
        go_tokens: list[str] = []
        for s in go_snippets:
            go_tokens.extend(s.split())
        packs["go-code"] = WordPack(
            name="go-code",
            description=f"Real Go code -- open-source snippets ({len(go_snippets)} snippets)",
            words=tuple(go_tokens),
            snippets=go_snippets,
        )
    return packs


def _load_config() -> dict[str, str | int]:
    if tomllib is None or not CONFIG_FILE.exists():
        return {}
    try:
        return tomllib.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_history(entry: dict[str, float | str]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, float | str]] = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            history = []
    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


def _load_history() -> list[dict[str, float | str]]:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _render_history(history: list[dict[str, float | str]], n: int = 10) -> str:
    if not history:
        return "No history yet. Take a typing test!"
    lines = [f"Last {min(n, len(history))} results:"]
    for entry in history[-n:]:
        wpm = entry.get("wpm", 0)
        raw_wpm = entry.get("raw_wpm", 0)
        acc = entry.get("accuracy", 0)
        pack = entry.get("pack", "?")
        ts = entry.get("timestamp", "?")
        lines.append(f"  {ts}  {pack:<15s}  WPM: {wpm:5.1f}  Raw: {raw_wpm:5.1f}  Acc: {acc:5.1f}%")
    best_wpm = max((e.get("wpm", 0) for e in history), default=0)
    best_acc = max((e.get("accuracy", 0) for e in history), default=0)
    lines.append(f"\nPersonal bests:  WPM: {best_wpm:.1f}  Accuracy: {best_acc:.1f}%")
    return "\n".join(lines)


def _load_custom_words(path: str) -> WordPack:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Custom word file not found: {path}")
    words: list[str] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        for word in line.split():
            cleaned = word.strip()
            if cleaned:
                words.append(cleaned)
    if not words:
        raise ValueError(f"Custom word file is empty: {path}")
    return WordPack(
        name=f"custom ({p.name})",
        description=f"Custom words from {p.name}",
        words=tuple(words),
    )


def _build_parser(word_packs: dict[str, WordPack]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="koalatype",
        description="Offline CLI typing test.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              koalatype --list
              koalatype --pack english-1000 --words 25
              koalatype --pack python --time 60
              koalatype --pack python-code
              koalatype --zen --pack rust
              koalatype --file ~/mywords.txt --words 20
              koalatype --difficulty hard --time 60
              koalatype --history
            """
        ).strip(),
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available word packs.",
    )
    parser.add_argument(
        "--history", action="store_true",
        help="Show recent test history and personal bests.",
    )
    parser.add_argument(
        "--pack", default=None,
        choices=sorted(word_packs.keys()),
        help="Word pack to use (default: english-1000).",
    )
    parser.add_argument(
        "--words", type=int, default=None,
        help="Number of words to generate (default: 30).",
    )
    parser.add_argument(
        "--time", type=int, default=None,
        choices=[15, 30, 60, 120],
        help="Test duration in seconds (default: 30).",
    )
    parser.add_argument(
        "--zen", action="store_true",
        help="Zen mode: no timer, press Escape when done.",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Optional RNG seed for repeatable tests.",
    )
    parser.add_argument(
        "--file", type=str, default=None,
        help="Path to a custom word list file.",
    )
    parser.add_argument(
        "--difficulty", default=None,
        choices=["easy", "medium", "hard"],
        help="Filter words by difficulty (easy: <=4 chars, medium: 5-7, hard: 8+).",
    )
    return parser


def _render_pack_list(word_packs: dict[str, WordPack]) -> str:
    lines = ["Available word packs:"]
    for key in sorted(word_packs.keys()):
        pack = word_packs[key]
        lines.append(f"  {pack.name:<15s} {pack.description}")
    return "\n".join(lines)


def _generate_prompt(pack: WordPack, count: int, seed: int | None) -> str:
    if count <= 0:
        raise ValueError("word count must be positive")
    rng = random.Random(seed)
    if pack.snippets:
        available = list(pack.snippets)
        rng.shuffle(available)
        selected: list[str] = []
        total_tokens = 0
        for snippet in available:
            selected.append(snippet)
            total_tokens += len(snippet.split())
            if total_tokens >= count:
                break
        return "\n\n".join(selected)
    return " ".join(rng.choices(pack.words, k=count))


def _score(
    prompt: str, typed: str, elapsed_seconds: float, stats: TestStats
) -> dict[str, float]:
    prompt_words = prompt.split()
    typed_words = typed.split()

    correct = sum(
        1 for expected, actual in zip(prompt_words, typed_words) if expected == actual
    )
    total = max(len(prompt_words), 1)
    accuracy = correct / total

    minutes = max(elapsed_seconds / 60.0, 1e-9)
    wpm = len(typed_words) / minutes
    raw_wpm = (stats.total_keystrokes / 5.0) / minutes if stats.total_keystrokes else wpm

    return {
        "accuracy": accuracy * 100.0,
        "wpm": wpm,
        "raw_wpm": raw_wpm,
        "correct": float(correct),
        "total": float(total),
        "backspaces": float(stats.backspace_count),
    }


def _layout_prompt(prompt: str, width: int) -> tuple[list[str], list[tuple[int, int]]]:
    lines: list[str] = []
    positions: list[tuple[int, int]] = []
    row = 0
    col = 0
    current_line: list[str] = []

    words = prompt.split(" ")

    for word_idx, word in enumerate(words):
        word_len = len(word)
        space_len = 1 if col > 0 else 0

        if col > 0 and col + space_len + word_len > width:
            lines.append("".join(current_line))
            current_line = []
            row += 1
            col = 0
            positions.append((row, col))

        if col > 0:
            current_line.append(" ")
            positions.append((row, col))
            col += 1

        for ch in word:
            current_line.append(ch)
            positions.append((row, col))
            col += 1

    if current_line or not lines:
        lines.append("".join(current_line))

    return lines, positions


def _build_rendered_text(
    prompt_words: list[str], typed_words: list[list[str]]
) -> tuple[str, list[int]]:
    rendered_words: list[str] = []
    starts: list[int] = []
    index = 0
    for w_idx, word in enumerate(prompt_words):
        starts.append(index)
        typed_word = typed_words[w_idx] if w_idx < len(typed_words) else []
        extra_len = max(len(typed_word) - len(word), 0)
        rendered_word = word + (" " * extra_len)
        rendered_words.append(rendered_word)
        index += len(rendered_word) + 1
    return " ".join(rendered_words), starts


def _progress_bar(completed: int, total: int, width: int) -> str:
    if total == 0:
        return ""
    bar_width = max(10, width - 12)
    filled = int(bar_width * completed / total)
    bar = "#" * filled + "-" * (bar_width - filled)
    pct = completed * 100 // total
    return f"[{bar}] {pct:3d}%"


# ---------------------------------------------------------------------------
#  Shared curses setup
# ---------------------------------------------------------------------------

def _init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)   # correct
    curses.init_pair(2, curses.COLOR_RED, -1)      # wrong
    curses.init_pair(3, curses.COLOR_CYAN, -1)     # chrome
    curses.init_pair(4, curses.COLOR_YELLOW, -1)   # progress


_LOGO_EMOJI = "\U0001f428"  # koala emoji

_LOGO_TITLE = r"""
    __               __      __
   / /______  ____ _/ /___ _/ /___  ______  ___
  / //_/ __ \/ __ `/ / __ `/ __/ / / / __ \/ _ \
 / ,< / /_/ / /_/ / / /_/ / /_/ /_/ / /_/ /  __/
/_/|_|\____/\__,_/_/\__,_/\__/\__, / .___/\___/
                             /____/_/
"""


def _show_splash(stdscr: curses.window) -> None:
    """Show koala logo splash screen; press any key to continue."""
    _init_colors()
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    title_lines = _LOGO_TITLE.strip("\n").splitlines()
    footer = "press any key to start | Esc to quit"

    total_lines = 1 + 2 + len(title_lines) + 2
    start_row = max(0, (height - total_lines) // 2)

    # Render koala emoji centered
    emoji_col = max(0, (width - 2) // 2)
    try:
        stdscr.addstr(start_row, emoji_col, _LOGO_EMOJI,
                      curses.color_pair(4) | curses.A_BOLD)
    except curses.error:
        pass

    # Render title in cyan
    max_title_w = max(len(line) for line in title_lines)
    title_left = max(0, (width - max_title_w) // 2)
    title_start = start_row + 2

    for i, line in enumerate(title_lines):
        row = title_start + i
        if row >= height - 1:
            break
        try:
            stdscr.addstr(row, title_left, line[: width - title_left - 1],
                          curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass

    footer_row = title_start + len(title_lines) + 1
    if footer_row < height:
        col = max(0, (width - len(footer)) // 2)
        try:
            stdscr.addstr(footer_row, col, footer[: width - col - 1],
                          curses.color_pair(4))
        except curses.error:
            pass

    stdscr.refresh()
    key = stdscr.getch()
    if key == 27:  # Esc
        raise SystemExit(0)


# ---------------------------------------------------------------------------
#  Interactive setup menu
# ---------------------------------------------------------------------------

_MENU_MODES = [
    ("Words", "words", True),
    ("Code", "code", True),
    ("Quotes", "quotes", False),
    ("Multiplayer", "multiplayer", False),
]

_MENU_WORDS_LANGS = [
    ("English", "english-1000", True),
    ("Python", "python", True),
    ("JavaScript", "javascript", True),
    ("Rust", "rust", True),
    ("Go", "go", True),
    ("SQL", "sql", True),
    ("TypeScript", "typescript", False),
    ("Java", "java", True),
    ("C++", "cpp", False),
]

_MENU_CODE_LANGS = [
    ("Python", "python-code", True),
    ("JavaScript", "javascript-code", True),
    ("Rust", "rust-code", False),
    ("Go", "go-code", True),
    ("TypeScript", "typescript-code", False),
    ("Java", "java-code", True),
]

_MENU_DURATIONS = [
    ("15 seconds", 15, True),
    ("30 seconds", 30, True),
    ("60 seconds", 60, True),
    ("120 seconds", 120, True),
    ("Zen  (no timer, Esc to end)", 0, True),
]

_MENU_WORD_COUNTS = [
    ("10 words", 10, True),
    ("20 words", 20, True),
    ("30 words", 30, True),
    ("50 words", 50, True),
    ("100 words", 100, True),
]

_MENU_DIFFICULTIES = [
    ("Any", "any", True),
    ("Easy   (short words, \u22644 chars)", "easy", True),
    ("Medium (5\u20137 chars)", "medium", True),
    ("Hard   (long words, 8+ chars)", "hard", True),
]


def _curses_menu(
    stdscr: curses.window,
    title: str,
    options: list[tuple[str, object, bool]],
    default: int = 0,
) -> object | None:
    """Arrow-key menu. Returns selected value, or None on Esc."""
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.keypad(True)

    # Start on the default (or first enabled) option
    sel = default
    if not options[sel][2]:
        for i, (_, _, enabled) in enumerate(options):
            if enabled:
                sel = i
                break

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()

        stdscr.addstr(1, 2, title[: width - 3], curses.color_pair(3) | curses.A_BOLD)

        base = 3
        for i, (label, _, enabled) in enumerate(options):
            row = base + i
            if row >= height - 2:
                break
            if not enabled:
                tag = f"  (coming soon)"
                display = f"    {label}{tag}"
                attr = curses.A_DIM
            elif i == sel:
                display = f"  > {label}"
                attr = curses.color_pair(3) | curses.A_BOLD
            else:
                display = f"    {label}"
                attr = curses.A_NORMAL
            try:
                stdscr.addstr(row, 0, display[: width - 1], attr)
            except curses.error:
                pass

        footer = "\u2191/\u2193/j/k navigate  |  l/Enter select  |  h/Esc back"
        try:
            stdscr.addstr(height - 1, 2, footer[: width - 3], curses.color_pair(4))
        except curses.error:
            pass

        stdscr.refresh()
        key = stdscr.getch()

        if key in (curses.KEY_UP, ord("k")):
            for i in range(sel - 1, -1, -1):
                if options[i][2]:
                    sel = i
                    break
        elif key in (curses.KEY_DOWN, ord("j")):
            for i in range(sel + 1, len(options)):
                if options[i][2]:
                    sel = i
                    break
        elif key in (10, 13, curses.KEY_ENTER, ord("l"), curses.KEY_RIGHT):
            if options[sel][2]:
                return options[sel][1]
        elif key in (27, ord("h"), curses.KEY_LEFT):
            return None


def _run_interactive_setup(
    word_packs: dict[str, WordPack],
) -> dict[str, object] | None:
    """Multi-step curses menu. Returns config dict or None if user quit."""
    result: dict[str, object] = {}

    def _setup(stdscr: curses.window) -> None:
        nonlocal result
        _init_colors()

        # --- Step 1: Mode ---
        while True:
            mode = _curses_menu(stdscr, "Choose a mode", _MENU_MODES)
            if mode is None:
                result = {}
                return

            # --- Step 2: Language / Pack ---
            if mode == "words":
                lang_opts = _MENU_WORDS_LANGS
            else:
                lang_opts = _MENU_CODE_LANGS
            pack = _curses_menu(stdscr, "Choose a language", lang_opts)
            if pack is None:
                continue  # back to mode

            # --- Step 3: Duration ---
            dur = _curses_menu(stdscr, "Choose a duration", _MENU_DURATIONS, default=1)
            if dur is None:
                continue  # back to mode

            zen = dur == 0

            if mode == "words":
                # --- Step 4: Word count ---
                wc = _curses_menu(
                    stdscr, "How many words?", _MENU_WORD_COUNTS, default=2
                )
                if wc is None:
                    continue

                # --- Step 5: Difficulty ---
                diff = _curses_menu(
                    stdscr, "Choose difficulty", _MENU_DIFFICULTIES
                )
                if diff is None:
                    continue
            else:
                wc = 30
                diff = "any"

            result = {
                "pack": pack,
                "words": wc,
                "time": dur if not zen else None,
                "zen": zen,
                "difficulty": diff if diff != "any" else None,
            }
            return

    curses.wrapper(_setup)
    return result if result else None


_BACKSPACE_KEYS = (curses.KEY_BACKSPACE, "\b", "\x7f", 127, 8)
_ENTER_KEYS = ("\n", "\r", 10, 13)


# ---------------------------------------------------------------------------
#  Word-mode test  (english, python keywords, etc.)
# ---------------------------------------------------------------------------

def _run_curses_test(
    prompt: str, duration_seconds: float, zen_mode: bool = False
) -> tuple[str, float, TestStats]:
    result: dict[str, float | str] = {"typed": "", "elapsed": 0.0}
    stats = TestStats()
    prompt_words = prompt.split(" ")

    def _curses_main(stdscr: curses.window) -> None:
        curses.curs_set(1)
        stdscr.keypad(True)
        _init_colors()

        typed_words: list[list[str]] = [[]]
        word_index = 0
        start_time: float | None = None
        stdscr.nodelay(True)

        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            usable_width = max(20, width - 2)
            rendered_text, prompt_starts = _build_rendered_text(
                prompt_words, typed_words
            )
            prompt_lines, positions = _layout_prompt(rendered_text, usable_width)

            now = time.perf_counter()
            elapsed = (now - start_time) if start_time else 0.0

            title = "koalatype"
            stdscr.addstr(0, 0, title[: width - 1], curses.color_pair(3))

            if zen_mode:
                header = f"Zen mode -- {elapsed:.1f}s" if start_time else "Zen mode -- start typing, press Esc when done"
            else:
                remaining = max(duration_seconds - elapsed, 0.0)
                header = f"Time left: {remaining:4.1f}s"
            stdscr.addstr(1, 0, header[: width - 1], curses.color_pair(3))

            words_done = sum(
                1 for i in range(min(word_index, len(prompt_words)))
                if i < len(typed_words) and "".join(typed_words[i]) == prompt_words[i]
            )
            pbar = _progress_bar(words_done, len(prompt_words), usable_width)
            stdscr.addstr(2, 0, pbar[: width - 1], curses.color_pair(4))

            base_row = 4
            max_lines = max(0, height - base_row - 2)
            for idx, line in enumerate(prompt_lines[:max_lines]):
                stdscr.addstr(base_row + idx, 0, line)

            for w_idx, typed_word in enumerate(typed_words):
                if w_idx >= len(prompt_words):
                    break
                expected_word = prompt_words[w_idx]
                word_start = prompt_starts[w_idx]

                for i, ch in enumerate(typed_word):
                    char_index = word_start + i
                    if char_index >= len(positions):
                        break
                    row, col = positions[char_index]
                    if row >= max_lines:
                        continue
                    expected_char = (
                        expected_word[i] if i < len(expected_word) else None
                    )
                    color = (
                        curses.color_pair(1)
                        if expected_char is not None and ch == expected_char
                        else curses.color_pair(2)
                    )
                    stdscr.addstr(base_row + row, col, ch, color)

            if word_index < len(prompt_words) and positions:
                cursor_base = prompt_starts[word_index]
                cursor_offset = len(typed_words[word_index])
                cursor_index = min(
                    cursor_base + cursor_offset, len(positions) - 1
                )
                cursor_row, cursor_col = positions[cursor_index]
                if cursor_row < max_lines:
                    stdscr.move(base_row + cursor_row, cursor_col)

            stdscr.refresh()

            if not zen_mode and start_time is not None:
                remaining = max(duration_seconds - elapsed, 0.0)
                if remaining <= 0:
                    break

            try:
                key = stdscr.get_wch()
            except curses.error:
                time.sleep(0.01)
                continue

            if start_time is None and key != curses.KEY_RESIZE:
                start_time = time.perf_counter()

            if key == "\x1b":
                break

            if key in _BACKSPACE_KEYS:
                stats.backspace_count += 1
                stats.total_keystrokes += 1
                if typed_words[word_index]:
                    typed_words[word_index].pop()
                elif word_index > 0:
                    word_index -= 1
                    typed_words.pop()
                continue
            if key == curses.KEY_RESIZE:
                continue
            if key == " ":
                stats.total_keystrokes += 1
                if word_index == len(prompt_words) - 1:
                    typed_word_str = "".join(typed_words[word_index])
                    expected_word = prompt_words[word_index]
                    if typed_word_str == expected_word:
                        break

                if word_index < len(prompt_words) - 1:
                    word_index += 1
                    if len(typed_words) <= word_index:
                        typed_words.append([])
                continue
            if isinstance(key, str) and key.isprintable():
                stats.total_keystrokes += 1
                current_word = typed_words[word_index]
                char_pos = len(current_word)
                if word_index < len(prompt_words):
                    expected_word = prompt_words[word_index]
                    if char_pos < len(expected_word):
                        expected_char = expected_word[char_pos]
                        if key != expected_char:
                            stats.char_misses[expected_char] = (
                                stats.char_misses.get(expected_char, 0) + 1
                            )
                typed_words[word_index].append(key)

        actual_elapsed = (
            (time.perf_counter() - start_time) if start_time is not None else 0.0
        )
        if not zen_mode:
            actual_elapsed = min(actual_elapsed, duration_seconds)
        result["typed"] = " ".join("".join(word) for word in typed_words)
        result["elapsed"] = actual_elapsed

    curses.wrapper(_curses_main)
    return result["typed"], float(result["elapsed"]), stats


# ---------------------------------------------------------------------------
#  Code-mode test  (python-code — real snippets with indentation)
# ---------------------------------------------------------------------------

def _code_line_col(cl: CodeLine, word_idx: int, char_offset: int) -> int:
    """Column position for a character within a code line."""
    col = cl.indent
    for i in range(word_idx):
        col += len(cl.tokens[i]) + 1  # token + trailing space
    return col + char_offset


def _run_code_test(
    code: str, duration_seconds: float, zen_mode: bool = False
) -> tuple[str, float, TestStats]:
    result: dict[str, float | str] = {"typed": "", "elapsed": 0.0}
    stats = TestStats()
    code_lines = _parse_code_lines(code)
    total_tokens = sum(len(cl.tokens) for cl in code_lines)

    def _curses_main(stdscr: curses.window) -> None:
        curses.curs_set(1)
        stdscr.keypad(True)
        _init_colors()

        # typed_words[line_idx] = list of word buffers for that line
        typed_words: list[list[list[str]]] = [[[]]]
        line_idx = 0
        word_idx = 0
        start_time: float | None = None
        stdscr.nodelay(True)

        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            usable_width = max(20, width - 2)

            now = time.perf_counter()
            elapsed = (now - start_time) if start_time else 0.0

            # -- chrome --
            stdscr.addstr(0, 0, "koalatype"[: width - 1], curses.color_pair(3))

            if zen_mode:
                hdr = f"Zen -- {elapsed:.1f}s  [Enter=next line, Esc=done]" if start_time else "Zen -- start typing  [Enter=next line, Esc=done]"
            else:
                remaining = max(duration_seconds - elapsed, 0.0)
                hdr = f"Time left: {remaining:4.1f}s  [Enter=next line]"
            stdscr.addstr(1, 0, hdr[: width - 1], curses.color_pair(3))

            # progress
            done = 0
            for li in range(len(code_lines)):
                tw = typed_words[li] if li < len(typed_words) else []
                for wi, tok in enumerate(code_lines[li].tokens):
                    if wi < len(tw) and "".join(tw[wi]) == tok:
                        done += 1
            pbar = _progress_bar(done, total_tokens, usable_width)
            stdscr.addstr(2, 0, pbar[: width - 1], curses.color_pair(4))

            base_row = 4
            max_vis = max(0, height - base_row - 2)

            # scroll so current line is visible
            scroll = max(0, line_idx - max_vis + 3)

            # -- render code lines --
            for vis_i, li in enumerate(range(scroll, min(scroll + max_vis, len(code_lines)))):
                cl = code_lines[li]
                display_str = " " * cl.indent + " ".join(cl.tokens)
                row = base_row + vis_i
                try:
                    stdscr.addstr(row, 0, display_str[: width - 1])
                except curses.error:
                    pass

                # -- colour typed chars --
                tw = typed_words[li] if li < len(typed_words) else []
                for wi, tok in enumerate(cl.tokens):
                    typed_buf = tw[wi] if wi < len(tw) else []
                    col_start = _code_line_col(cl, wi, 0)
                    for ci, ch in enumerate(typed_buf):
                        c = col_start + ci
                        if c >= width - 1:
                            break
                        expected = tok[ci] if ci < len(tok) else None
                        color = (
                            curses.color_pair(1)
                            if expected is not None and ch == expected
                            else curses.color_pair(2)
                        )
                        try:
                            stdscr.addstr(row, c, ch, color)
                        except curses.error:
                            pass

            # -- cursor --
            if line_idx < len(code_lines):
                cl = code_lines[line_idx]
                vis_line = line_idx - scroll
                if 0 <= vis_line < max_vis:
                    tw = typed_words[line_idx] if line_idx < len(typed_words) else [[]]
                    cur_buf = tw[word_idx] if word_idx < len(tw) else []
                    cursor_col = _code_line_col(cl, word_idx, len(cur_buf))
                    cursor_col = min(cursor_col, width - 2)
                    try:
                        stdscr.move(base_row + vis_line, cursor_col)
                    except curses.error:
                        pass

            stdscr.refresh()

            # time check
            if not zen_mode and start_time is not None:
                if duration_seconds - elapsed <= 0:
                    break

            try:
                key = stdscr.get_wch()
            except curses.error:
                time.sleep(0.01)
                continue

            if start_time is None and key != curses.KEY_RESIZE:
                start_time = time.perf_counter()

            if key == "\x1b":
                break

            if key == curses.KEY_RESIZE:
                continue

            # -- backspace --
            if key in _BACKSPACE_KEYS:
                stats.backspace_count += 1
                stats.total_keystrokes += 1
                tw = typed_words[line_idx]
                if tw[word_idx]:
                    tw[word_idx].pop()
                elif word_idx > 0:
                    word_idx -= 1
                    tw.pop()
                elif line_idx > 0:
                    line_idx -= 1
                    tw_prev = typed_words[line_idx]
                    word_idx = max(0, len(tw_prev) - 1)
                continue

            # -- enter: next line --
            if key in _ENTER_KEYS:
                stats.total_keystrokes += 1
                # check if last token of last line completed -> done
                if line_idx == len(code_lines) - 1:
                    cl = code_lines[line_idx]
                    tw = typed_words[line_idx]
                    if word_idx == len(cl.tokens) - 1:
                        typed_str = "".join(tw[word_idx]) if word_idx < len(tw) else ""
                        if typed_str == cl.tokens[-1]:
                            break
                if line_idx < len(code_lines) - 1:
                    line_idx += 1
                    word_idx = 0
                    while len(typed_words) <= line_idx:
                        typed_words.append([[]])
                continue

            # -- space: next word within line --
            if key == " ":
                stats.total_keystrokes += 1
                cl = code_lines[line_idx]
                if word_idx < len(cl.tokens) - 1:
                    word_idx += 1
                    tw = typed_words[line_idx]
                    while len(tw) <= word_idx:
                        tw.append([])
                continue

            # -- printable char --
            if isinstance(key, str) and key.isprintable():
                stats.total_keystrokes += 1
                tw = typed_words[line_idx]
                cur_buf = tw[word_idx]
                char_pos = len(cur_buf)
                cl = code_lines[line_idx]
                if word_idx < len(cl.tokens):
                    tok = cl.tokens[word_idx]
                    if char_pos < len(tok) and key != tok[char_pos]:
                        stats.char_misses[tok[char_pos]] = (
                            stats.char_misses.get(tok[char_pos], 0) + 1
                        )
                tw[word_idx].append(key)

        # -- build flat typed string for scoring --
        all_typed: list[str] = []
        for tw_line in typed_words:
            for buf in tw_line:
                word = "".join(buf)
                if word:
                    all_typed.append(word)

        actual_elapsed = (
            (time.perf_counter() - start_time) if start_time is not None else 0.0
        )
        if not zen_mode:
            actual_elapsed = min(actual_elapsed, duration_seconds)
        result["typed"] = " ".join(all_typed)
        result["elapsed"] = actual_elapsed

    curses.wrapper(_curses_main)
    return result["typed"], float(result["elapsed"]), stats


# ---------------------------------------------------------------------------
#  Results & main
# ---------------------------------------------------------------------------

def _render_results(
    results: dict[str, float], stats: TestStats, pack_name: str
) -> str:
    lines = [
        "\nResults:",
        f"  WPM:            {results['wpm']:.1f}",
        f"  Raw WPM:        {results['raw_wpm']:.1f}",
        f"  Accuracy:       {results['accuracy']:.1f}%",
        f"  Correct words:  {int(results['correct'])}/{int(results['total'])}",
        f"  Backspaces:     {int(results['backspaces'])}",
        f"  Keystrokes:     {stats.total_keystrokes}",
    ]
    if stats.char_misses:
        worst = sorted(stats.char_misses.items(), key=lambda x: -x[1])[:5]
        miss_str = ", ".join(f"'{ch}' ({n}x)" for ch, n in worst)
        lines.append(f"  Most missed:    {miss_str}")
    return "\n".join(lines)


def _run_test_loop(
    pack: WordPack, word_count: int, duration: float, zen: bool, seed: int | None
) -> None:
    """Run the test-play-again loop."""
    is_code = bool(pack.snippets)

    while True:
        prompt = _generate_prompt(pack, word_count, seed)

        if is_code:
            typed, elapsed, test_stats = _run_code_test(
                prompt, duration, zen_mode=zen
            )
        else:
            typed, elapsed, test_stats = _run_curses_test(
                prompt, duration, zen_mode=zen
            )

        results = _score(prompt, typed, elapsed, test_stats)
        print(_render_results(results, test_stats, pack.name))

        _save_history({
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            "pack": pack.name,
            "wpm": round(results["wpm"], 1),
            "raw_wpm": round(results["raw_wpm"], 1),
            "accuracy": round(results["accuracy"], 1),
            "words": word_count,
            "duration": round(elapsed, 1),
        })

        while True:
            choice = input(
                "\nEnter 'r' to repeat, 'n' for new test, or 'q'/Esc to quit: "
            ).strip()
            if choice in ("q", "Q", "\x1b"):
                return
            elif choice.lower() == "r":
                break
            elif choice.lower() == "n":
                seed = None
                break
            else:
                print("Invalid choice. Please enter 'r', 'n', or 'q'.")


def main() -> None:
    word_packs = _build_word_packs()
    config = _load_config()
    parser = _build_parser(word_packs)
    args = parser.parse_args()

    # --- Handle --list / --history early ---
    if args.list:
        print(_render_pack_list(word_packs))
        return
    if args.history:
        print(_render_history(_load_history()))
        return

    # --- No CLI args → interactive setup ---
    no_args = len(sys.argv) == 1
    if no_args:
        curses.wrapper(_show_splash)
        setup = _run_interactive_setup(word_packs)
        if setup is None:
            return
        pack_name = str(setup["pack"])
        word_count = int(setup["words"])  # type: ignore[arg-type]
        zen = bool(setup["zen"])
        difficulty = setup["difficulty"]
        duration = float(setup["time"]) if setup["time"] else 9999.0
        seed = None
    else:
        # --- CLI arg flow (unchanged) ---
        if args.pack is None:
            args.pack = config.get("pack", "english-1000")
        if args.words is None:
            args.words = config.get("words", 30)
        if args.time is None and not args.zen:
            args.time = config.get("time", 30)
        if args.difficulty is None:
            args.difficulty = config.get("difficulty", None)

        curses.wrapper(_show_splash)

        pack_name = args.pack
        word_count = args.words
        zen = args.zen
        difficulty = args.difficulty
        duration = float(args.time) if args.time and not zen else 9999.0
        seed = args.seed

    # --- Resolve pack ---
    if not no_args and args.file:
        pack = _load_custom_words(args.file)
    else:
        pack = word_packs[pack_name]

    if difficulty:
        filtered_words = _filter_by_difficulty(pack.words, str(difficulty))
        pack = WordPack(
            name=pack.name,
            description=f"{pack.description} ({difficulty})",
            words=filtered_words,
        )

    _run_test_loop(pack, word_count, duration, zen, seed)


if __name__ == "__main__":
    main()
