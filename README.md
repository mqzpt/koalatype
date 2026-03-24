# koalatype

Offline CLI typing test. Pure Python, zero dependencies, runs in any terminal.

Includes a **code mode** where you type real functions with proper indentation and line breaks — not just random keywords.

## Install

```bash
pip install -e .
```

Requires Python 3.11+.

## Usage

```bash
koalatype                                    # interactive setup menu
koalatype --pack python-code                 # real Python snippets with indentation
koalatype --pack javascript-code --zen       # no timer, Esc when done
koalatype --pack java-code --time 60         # 60 second test
koalatype --pack rust-code --time 60         # real Rust code
koalatype --pack go-code --time 60           # real Go code
koalatype --pack typescript-code --time 60   # real TypeScript code
koalatype --difficulty hard --time 120       # long words only
koalatype --file ~/mywords.txt --words 20    # custom word list
koalatype --list                             # show all packs
koalatype --history                          # past results + personal bests
```

Running `koalatype` with no arguments launches an interactive menu where you pick mode, language, duration, word count, and difficulty. Supports arrow keys and vim bindings (h/j/k/l).

## Word Packs

| Pack | Description |
|------|-------------|
| `english-1000` | Common English words (default) |
| `python` | Python keywords and builtins |
| `python-code` | Real Python code — 94 snippets |
| `javascript` | JavaScript keywords |
| `javascript-code` | Real JavaScript code — 92 snippets |
| `typescript` | TypeScript keywords |
| `typescript-code` | Real TypeScript code — 107 snippets |
| `java` | Java keywords |
| `java-code` | Real Java code — 107 snippets |
| `rust` | Rust keywords |
| `rust-code` | Real Rust code — 104 snippets |
| `go` | Go keywords |
| `go-code` | Real Go code — 101 snippets |
| `sql` | SQL keywords |

`--difficulty easy/medium/hard` filters by word length (<=4, 5-7, 8+ chars). Works with any word pack.

`--file` lets you bring your own word list (one word per line or space-separated).

## Code Mode

Code packs have you type real functions instead of random words:

```
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in seen:
            return [seen[diff], i]
        seen[num] = i
```

- **Space** advances to the next token within a line
- **Enter** moves to the next line (indentation is handled for you)
- **Backspace** goes back through chars, words, and up to previous lines
- **Esc** exits the test early and scores what you've typed

605 code snippets across six languages covering sorting, searching, dynamic programming, graph algorithms, data structures, and more.

## Features

- **Interactive setup** — run with no args to pick mode, language, and settings via a menu
- **Timed or zen mode** — pick 15/30/60/120s or zen (no timer, Esc to finish)
- **Timer starts on first keypress** — no time lost reading the prompt
- **Live stats** — WPM, raw WPM (keystroke-based), accuracy, backspace count, most-mistyped characters
- **Persistent history** — results saved to `~/.koalatype/history.json`, view with `--history`
- **Config file** — `~/.koalatype/config.toml` for defaults (pack, words, time, difficulty)
- **Seeded RNG** — `--seed` for repeatable tests
- **Post-test loop** — repeat same prompt, new prompt, or quit

## Config

Create `~/.koalatype/config.toml` to set defaults:

```toml
pack = "python-code"
words = 40
time = 60
difficulty = "medium"
```

## Future

- Quote mode
- Themes / color schemes
- Multiplayer

## Credits

**Word lists:**
- English word list from [powerlanguage/word-lists](https://github.com/powerlanguage/word-lists/blob/master/1000-most-common-words.txt)

**Code snippets sourced from:**
- Python — LeetCode editorial solutions, [TheAlgorithms/Python](https://github.com/TheAlgorithms/Python)
- JavaScript — [trekhleb/javascript-algorithms](https://github.com/trekhleb/javascript-algorithms), [30secondsofcode.org](https://www.30secondsofcode.org), [TheAlgorithms/JavaScript](https://github.com/TheAlgorithms/JavaScript)
- TypeScript — [TheAlgorithms/TypeScript](https://github.com/TheAlgorithms/TypeScript)
- Java — [TheAlgorithms/Java](https://github.com/TheAlgorithms/Java)
- Go — [TheAlgorithms/Go](https://github.com/TheAlgorithms/Go)
- Rust — [TheAlgorithms/Rust](https://github.com/TheAlgorithms/Rust)
