# koalatype

Offline CLI typing test. Pure Python, zero dependencies, runs in any terminal.

The killer feature: **code mode**. Type real Python solutions (LeetCode editorial-style) with proper indentation and line breaks — not just random keywords mashed together.

## Install

```bash
pip install -e .
```

Requires Python 3.11+.

## Usage

```bash
koalatype                                    # english words, 30s
koalatype --pack python-code                 # real Python snippets with indentation
koalatype --pack python-code --zen           # no timer, Esc when done
koalatype --pack rust --time 60              # 60 second test
koalatype --difficulty hard --time 120       # long words only
koalatype --file ~/mywords.txt --words 20    # custom word list
koalatype --list                             # show all packs
koalatype --history                          # past results + personal bests
```

## Word Packs

| Pack | Description |
|------|-------------|
| `english-1000` | Common English words (default) |
| `python` | Python keywords and builtins |
| `python-code` | Real Python code — 31 LeetCode solutions with indentation |
| `javascript` | JavaScript keywords |
| `rust` | Rust keywords |
| `go` | Go keywords |
| `sql` | SQL keywords |

`--difficulty easy/medium/hard` filters by word length (<=4, 5-7, 8+ chars). Works with any word pack.

`--file` lets you bring your own word list (one word per line or space-separated).

## Code Mode

`python-code` is different from the other packs. Instead of random words, you type real functions:

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

31 snippets covering classic problems: Two Sum, Valid Parentheses, Binary Search, LRU Cache, Merge Intervals, Trie, Number of Islands, Trapping Rain Water, etc.

## Features

- **Timed or zen mode** — pick 15/30/60/120s or `--zen` for no timer (Esc to finish)
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

- More code packs: JavaScript, Rust, Go, SQL snippets with real code (not just keywords)
- Quote mode — type real sentences and paragraphs
- Themes / color schemes
- Live WPM sparkline graph during the test
- Progressive difficulty — words get harder as you go
- Multiplayer ghost mode — race against your previous best
- Persistent leaderboard

## Credits

English word list from [powerlanguage/word-lists](https://github.com/powerlanguage/word-lists/blob/master/1000-most-common-words.txt).
