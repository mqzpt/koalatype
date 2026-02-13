from __future__ import annotations

import argparse
import curses
import random
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WordPack:
    name: str
    description: str
    words: tuple[str, ...]


ENGLISH_WORDS_FILE = Path(__file__).with_name("1000-most-common-words.txt")


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


def _build_word_packs() -> dict[str, WordPack]:
    packs: dict[str, WordPack] = {
        "python": WordPack(
            name="python",
            description="Python keywords and common identifiers",
            words=(
                "def",
                "class",
                "import",
                "from",
                "return",
                "yield",
                "lambda",
                "async",
                "await",
                "with",
                "as",
                "try",
                "except",
                "finally",
                "raise",
                "None",
                "True",
                "False",
                "list",
                "dict",
                "set",
                "tuple",
                "str",
                "int",
                "float",
                "bool",
                "len",
                "range",
                "print",
                "enumerate",
            ),
        )
    }
    english_words = _load_english_words()
    packs["english-1000"] = WordPack(
        name="english-1000",
        description=f"Common English words ({len(english_words)} words)",
        words=english_words,
    )
    return packs


def _build_parser(word_packs: dict[str, WordPack]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="koalatype",
        description="Offline CLI typing test.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              typetest --list
              typetest --pack english-1000 --words 25
              typetest --pack python --words 40
            """
        ).strip(),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available word packs.",
    )
    parser.add_argument(
        "--pack",
        default="english-1000",
        choices=sorted(word_packs.keys()),
        help="Word pack to use.",
    )
    parser.add_argument(
        "--words",
        type=int,
        default=30,
        help="Number of words to generate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for repeatable tests.",
    )
    return parser


def _render_pack_list(word_packs: dict[str, WordPack]) -> str:
    lines = ["Available word packs:"]
    for key in sorted(word_packs.keys()):
        pack = word_packs[key]
        lines.append(f"- {pack.name}: {pack.description}")
    return "\n".join(lines)


def _generate_prompt(pack: WordPack, count: int, seed: int | None) -> str:
    if count <= 0:
        raise ValueError("word count must be positive")
    rng = random.Random(seed)
    return " ".join(rng.choices(pack.words, k=count))


def _score(prompt: str, typed: str, elapsed_seconds: float) -> dict[str, float]:
    prompt_words = prompt.split()
    typed_words = typed.split()

    correct = sum(
        1 for expected, actual in zip(prompt_words, typed_words) if expected == actual
    )
    total = max(len(prompt_words), 1)
    accuracy = correct / total

    minutes = max(elapsed_seconds / 60.0, 1e-9)
    wpm = len(typed_words) / minutes

    return {
        "accuracy": accuracy * 100.0,
        "wpm": wpm,
        "correct": float(correct),
        "total": float(total),
    }


def _layout_prompt(prompt: str, width: int) -> tuple[list[str], list[tuple[int, int]]]:
    lines: list[str] = []
    positions: list[tuple[int, int]] = []
    row = 0
    col = 0
    current_line: list[str] = []
    
    words = prompt.split(" ")
    
    for word_idx, word in enumerate(words):
        # Check if word fits on current line
        word_len = len(word)
        space_len = 1 if col > 0 else 0  # Space before word (unless at start of line)
        
        if col > 0 and col + space_len + word_len > width:
            # Word doesn't fit, move to next line
            lines.append("".join(current_line))
            current_line = []
            row += 1
            col = 0
        
        # Add space before word (if not at start of line)
        if col > 0:
            current_line.append(" ")
            positions.append((row, col))
            col += 1
        
        # Add word
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


def _run_curses_test(prompt: str, duration_seconds: float) -> tuple[str, float]:
    result: dict[str, float | str] = {"typed": "", "elapsed": 0.0}

    prompt_words = prompt.split(" ")

    def _curses_main(stdscr: curses.window) -> None:
        curses.curs_set(1)
        stdscr.keypad(True)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_CYAN, -1)

        typed_words: list[list[str]] = [[]]
        word_index = 0
        start_time = time.perf_counter()
        stdscr.nodelay(True)

        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            usable_width = max(20, width - 2)
            rendered_text, prompt_starts = _build_rendered_text(
                prompt_words, typed_words
            )
            prompt_lines, positions = _layout_prompt(rendered_text, usable_width)

            elapsed = time.perf_counter() - start_time
            remaining = max(duration_seconds - elapsed, 0.0)
            
            title = "🐨 koalatype 🐨"
            stdscr.addstr(0, 0, title[: width - 1], curses.color_pair(3))
            
            header = f"Time left: {remaining:4.1f}s"
            stdscr.addstr(1, 0, header[: width - 1], curses.color_pair(3))

            base_row = 3
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

            if remaining <= 0:
                break

            try:
                key = stdscr.get_wch()
            except curses.error:
                time.sleep(0.01)
                continue
            if key in (curses.KEY_BACKSPACE, "\b", "\x7f", 127, 8):
                if typed_words[word_index]:
                    typed_words[word_index].pop()
                elif word_index > 0:
                    word_index -= 1
                    typed_words.pop()
                continue
            if key == curses.KEY_RESIZE:
                continue
            if key == " ":
                # Check if we just completed the last word correctly
                if word_index == len(prompt_words) - 1:
                    typed_word = "".join(typed_words[word_index])
                    expected_word = prompt_words[word_index]
                    if typed_word == expected_word:
                        # early exit iff words completed correctly
                        break
                
                if word_index < len(prompt_words) - 1:
                    word_index += 1
                    if len(typed_words) <= word_index:
                        typed_words.append([])
                continue
            if isinstance(key, str) and key.isprintable():
                typed_words[word_index].append(key)

        result["typed"] = " ".join("".join(word) for word in typed_words)
        result["elapsed"] = min(time.perf_counter() - start_time, duration_seconds)

    curses.wrapper(_curses_main)
    return result["typed"], float(result["elapsed"])


def main() -> None:
    word_packs = _build_word_packs()
    parser = _build_parser(word_packs)
    args = parser.parse_args()

    if args.list:
        print(_render_pack_list(word_packs))
        return

    pack = word_packs[args.pack]
    
    while True:
        prompt = _generate_prompt(pack, args.words, args.seed)

        typed, elapsed = _run_curses_test(prompt, duration_seconds=30.0)

        results = _score(prompt, typed, elapsed)
        print("\nResults:")
        print(f"- WPM: {results['wpm']:.1f}")
        print(f"- Accuracy: {results['accuracy']:.1f}%")
        print(f"- Correct words: {int(results['correct'])}/{int(results['total'])}")
        
        while True:
            choice = input("\Enter 'r' to repeat, 'n' for new test, or 'q' to quit: ").lower().strip()
            if choice == "r":
                break
            elif choice == "n":
                prompt = _generate_prompt(pack, args.words, None)
                break
            elif choice == "q":
                return
            else:
                print("Invalid choice. Please enter 'r', 'n', or 'q'.")


if __name__ == "__main__":
    main()
