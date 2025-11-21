---
title: "Getting Started"
---

## Installation

### Homebrew (macOS)

```bash
brew tap cittamaya/pensieve
brew install pensieve
```

### pip

```bash
pip install pensieve-cli
```

## First Steps

1. **Initialize in a project:**
   ```bash
   cd your-project
   pensieve init
   ```

2. **Create your first memory:**
   ```bash
   pensieve entry create --template problem_solved
   ```

3. **Search past learnings:**
   ```bash
   pensieve entry search --tag debugging
   ```

## Using with Claude Code

Pensieve integrates with Claude Code through skills. When Claude starts a session, it can automatically recall relevant memories from past sessions.
