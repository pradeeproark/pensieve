---
title: "Getting Started"
---

## Installation

### Homebrew (macOS)

```bash
brew tap cittamaya/pensieve
brew install pensieve
```

**Platform availability:** Currently macOS only. Windows and Linux builds coming soon.

### Build from Source

For other platforms or to build from source, see the [build instructions](https://github.com/pradeeproark/pensieve#building-from-source) on GitHub.

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
