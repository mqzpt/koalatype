# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Koalatype is an offline CLI typing test built with Python's curses library. Single-file app (`main.py`) with zero external dependencies — pure stdlib only. Python 3.11+ required.

## Commands

```bash
pip install -e .

koalatype                                    # default: english-1000, 30 words, 30s
koalatype --pack python --words 40 --time 60
koalatype --zen --pack rust                  # no timer, Escape to end
koalatype --file ~/mywords.txt --words 20    # custom word list
koalatype --difficulty hard --time 60        # filter by word length
koalatype --list                             # show available packs
koalatype --history                          # show past results + personal bests
```

No test framework is configured. Testable pure functions: `_score()`, `_generate_prompt()`, `_layout_prompt()`, `_build_rendered_text()`, `_filter_by_difficulty()`, `_progress_bar()`.

## Architecture

All logic lives in `main.py`. The flow is:

1. **Config** — optional `~/.koalatype/config.toml` sets defaults for pack, words, time, difficulty
2. **Word packs** (`WordPack` frozen dataclass) — english-1000, python, javascript, rust, go, sql, or custom via `--file`
3. **Difficulty filter** (`_filter_by_difficulty`) — easy (<=4 chars), medium (5-7), hard (8+)
4. **Prompt generation** (`_generate_prompt`) — seeded `random.Random.choices` from a pack
5. **Curses UI** (`_run_curses_test`) — real-time typing with color feedback, progress bar, zen/timed modes. Timer starts on first keypress.
6. **Scoring** (`_score`) — WPM, raw WPM (keystroke-based), word-level accuracy
7. **Stats** (`TestStats`) — tracks backspaces, per-character miss counts, total keystrokes
8. **History** — results saved to `~/.koalatype/history.json`
9. **Post-test loop** — repeat same prompt, new prompt, or quit

## Conventions

- Type hints throughout, using `str | None` style unions (not `Optional`)
- Frozen dataclasses for config objects
- Private `_` prefix on all helper functions
- Entry point registered in `pyproject.toml` as `koalatype = "main:main"`
