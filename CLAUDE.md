# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Koalatype is an offline CLI typing test built with Python's curses library. Single-file app (`main.py`) with zero external dependencies — pure stdlib only. Python 3.11+ required.

## Commands

```bash
pip install -e .

koalatype                                    # interactive setup menu (no args)
koalatype --pack python-code --time 60       # real Python code snippets
koalatype --pack javascript-code --zen       # JS code, no timer
koalatype --pack java-code --time 60         # Java code snippets
koalatype --pack quotes --words 50            # famous quotes
koalatype --pack rust --words 40 --time 60   # Rust keywords
koalatype --difficulty hard --time 120       # filter by word length
koalatype --file ~/mywords.txt --words 20    # custom word list
koalatype --list                             # show available packs
koalatype --history                          # show past results + personal bests
```

No test framework is configured. Testable pure functions: `_score()`, `_generate_prompt()`, `_layout_prompt()`, `_build_rendered_text()`, `_filter_by_difficulty()`, `_progress_bar()`.

## Architecture

All logic lives in `main.py`. The flow is:

1. **Config** — optional `~/.koalatype/config.toml` sets defaults for pack, words, time, difficulty
2. **Word packs** (`WordPack` frozen dataclass with `words`, `snippets`, `quotes` fields) — english-1000, python, javascript, java, rust, go, sql, quotes, or custom via `--file`
3. **Code snippet packs** — python-code (94), javascript-code (92), typescript-code (107), java-code (107), go-code (101), rust-code (104). Loaded from `snippets/*_snippets.txt` via `_load_snippets()`, separated by `\n---\n`
4. **Quote pack** — 189 famous quotes loaded from `snippets/quotes.txt`. Uses word-mode test, selects whole quotes
5. **Splash screen** (`_show_splash`) — koala emoji + figlet title, press any key or Esc to quit
6. **Interactive setup** (`_run_interactive_setup`) — curses menu when no CLI args given. Steps: mode → language → duration → word count → difficulty. Supports arrow keys and vim bindings (h/j/k/l)
7. **Difficulty filter** (`_filter_by_difficulty`) — easy (<=4 chars), medium (5-7), hard (8+)
8. **Prompt generation** (`_generate_prompt`) — handles three content types: snippets (code mode), quotes (whole-quote selection), words (random choices)
9. **Curses UI** — `_run_curses_test` for word/quote mode, `_run_code_test` for code mode. Real-time typing with color feedback, progress bar, zen/timed modes. Timer starts on first keypress. Esc exits gracefully.
10. **Scoring** (`_score`) — WPM, raw WPM (keystroke-based), word-level accuracy
11. **Stats** (`TestStats`) — tracks backspaces, per-character miss counts, total keystrokes
12. **History** — results saved to `~/.koalatype/history.json`
13. **Post-test loop** — repeat same prompt, new prompt, or quit (q/Esc)

## Conventions

- Type hints throughout, using `str | None` style unions (not `Optional`)
- Frozen dataclasses for config objects
- Private `_` prefix on all helper functions
- Entry point registered in `pyproject.toml` as `koalatype = "main:main"`
