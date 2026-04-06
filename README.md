# lreview

Lightweight local LLM code review CLI. No cloud. No token bills. Works on private repos.

## Features
- Review git diffs with a local Ollama model
- Structured JSON issue output (file, line, severity, suggestion)
- Interactive patch selection via Rich UI
- `git apply --check` dry-run before any write
- Auto-rollback via `git apply -R` if `--test-cmd` fails
- Pre-commit hook compatible (`--staged`)

## Install

```bash
uv pip install -e .
```

## Config

```bash
mkdir -p ~/.config/lreview
cp config.default.toml ~/.config/lreview/config.toml
```

## Usage

```bash
# Review last commit
lreview

# Review staged changes only (pre-commit)
lreview --staged

# Review with auto-test and rollback
lreview --test-cmd "pytest -x"

# Review specific range
lreview HEAD~3

# JSON output for CI
lreview --output json
```

## Models (Ollama)

Defaults to `gemma4:e2b` for review pass and `qwen3.5:4b` for patch generation.

```bash
ollama pull gemma4:e2b
ollama pull qwen3.5:4b
```
