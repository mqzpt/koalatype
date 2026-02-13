# Koalatype Copilot Instructions

## Project Overview
Koalatype is an offline CLI typing test tool built with Python's `curses` library. It presents timed word prompts to users and scores their accuracy and WPM (words per minute).

## Architecture

### Core Components
- **Word Packs System**: Manages collections of words via the `WordPack` dataclass. Currently includes:
  - `python`: Keywords and built-in functions for code typing practice
  - `english-1000`: Common English words loaded from external file at runtime
- **Prompt Generation**: Uses seeded random selection from word packs for repeatable tests
- **Scoring Engine**: Calculates accuracy and WPM based on character-by-character comparison
- **Terminal UI**: Uses `curses` to display real-time typing feedback with color-coded correctness

### Data Flow
1. User selects word pack via CLI args → `_build_word_packs()`
2. Prompt generated → `_generate_prompt()`
3. Curses UI launches → `_run_curses_test()` captures input in real-time
4. Scoring calculates metrics → `_score()`
5. Results printed to console

## Developer Workflows

### Running the Tool
```bash
# Development: pip install -e .
# Run typing test: koalatype [--pack PACK] [--words N] [--seed SEED]
# List available packs: koalatype --list
```

### Testing
Add tests directly using the public functions like `_score()`, `_generate_prompt()`, and `_layout_prompt()`. The `--seed` flag ensures deterministic test word sequences.

## Key Patterns & Conventions

### Data Structures
- Use frozen dataclasses (`@dataclass(frozen=True)`) for immutable configuration objects like `WordPack`
- Type hints required throughout (Python 3.11+), including union types (`str | None`)

### Helper Functions
- All major logic extracted into `_` prefixed private functions organized by responsibility
- `_layout_prompt()` and `_build_rendered_text()` handle terminal positioning: return tuples of (content, metadata) for flexible rendering
- Character positions mapped to (row, col) for precise cursor placement

### Curses Usage Specifics
- Use `curses.start_color()` and `curses.init_pair()` for color setup (Green=1 correct, Red=2 incorrect, Cyan=3 timer)
- Handle terminal resizing via `curses.KEY_RESIZE` event
- Use `stdscr.nodelay(True)` for non-blocking input with `time.sleep(0.01)` fallback
- Color pairs applied via `curses.color_pair(n)` in `addstr()` calls
- Cursor position managed with `stdscr.move()` after character coloring

### Input Handling
- Backspace supports multiple key codes: `KEY_BACKSPACE`, `"\b"`, `"\x7f"`, 127, 8
- Space key advances word index and initializes new word buffer
- Printable characters appended to current word via `isprintable()`

## Critical Files
- [main.py](main.py): Single monolithic entry point with all logic
- [1000-most-common-words.txt](1000-most-common-words.txt): Word data file (required at runtime)
- [pyproject.toml](pyproject.toml): Package config with entry point definition

## External Dependencies
- **None** for core functionality - pure stdlib (curses, argparse, random, time, pathlib, dataclasses)
- Requires Python 3.11+ for pattern matching syntax and union types
