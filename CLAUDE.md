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
2. **Word packs** (`WordPack` frozen dataclass) — english-1000, python, javascript, java, rust, go, sql, or custom via `--file`
3. **Code snippet packs** — python-code (94 snippets), javascript-code (92), java-code (107). Loaded from `*_snippets.txt` files via `_load_snippets()`, separated by `\n---\n`
4. **Splash screen** (`_show_splash`) — koala emoji + figlet title, press any key or Esc to quit
5. **Interactive setup** (`_run_interactive_setup`) — curses menu when no CLI args given. Steps: mode → language → duration → word count → difficulty. Supports arrow keys and vim bindings (h/j/k/l)
6. **Difficulty filter** (`_filter_by_difficulty`) — easy (<=4 chars), medium (5-7), hard (8+)
7. **Prompt generation** (`_generate_prompt`) — seeded `random.Random.choices` from a pack
8. **Curses UI** — `_run_curses_test` for word mode, `_run_code_test` for code mode. Real-time typing with color feedback, progress bar, zen/timed modes. Timer starts on first keypress. Esc exits gracefully.
9. **Scoring** (`_score`) — WPM, raw WPM (keystroke-based), word-level accuracy
10. **Stats** (`TestStats`) — tracks backspaces, per-character miss counts, total keystrokes
11. **History** — results saved to `~/.koalatype/history.json`
12. **Post-test loop** — repeat same prompt, new prompt, or quit (q/Esc)

## Conventions

- Type hints throughout, using `str | None` style unions (not `Optional`)
- Frozen dataclasses for config objects
- Private `_` prefix on all helper functions
- Entry point registered in `pyproject.toml` as `koalatype = "main:main"`
