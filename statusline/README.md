# Claude Code Status Line

A curated, opinionated status line for Claude Code — pre-designed for readability so you don't end up with a wall of unformatted text.

<img width="612" height="151" alt="image" src="https://github.com/user-attachments/assets/fd9cc417-56e8-4c57-b7d1-2527d4b8e914" />


```
context: 28.8k  |  5h: 0%  |  7d: 28%  |  Opus 4.6 (1M context)
```

## Why not the built-in `/statusline`?

The official command generates a status line with no layout constraints — font weight, spacing, information density are all uncontrolled. The result usually looks like an afterthought.

This one gives you pre-designed presets with curated typography, and lets you customize through selection rather than free-form prompting.

## Install & Run

One command to install, one slash command to configure, zero cleanup needed:

```bash
mkdir -p ~/.claude/agents && curl -sL https://raw.githubusercontent.com/kirisawa-subaru/claude-code-sharing/main/statusline/skill/statusline-setup.md -o ~/.claude/agents/statusline-setup.md
```

Then in any Claude Code session:

```
/statusline-setup
```

The skill walks you through 4 selections with live previews, writes your config, then **deletes itself** — no leftover files. Re-run the install one-liner to reconfigure anytime.

## What's configurable

| Step | Options |
|------|---------|
| **Layout** | Minimal (labels stripped), Standard (labeled), Full (+ timestamps + cost), or design your own |
| **Colors** | Moonlight (blue), Mono (gray), Clean (white), or create your own with live terminal preview |
| **Separator** | Pipe `\|`, dot `·`, slim, or any character you like |
| **Precision** | Whole numbers (`29k`) or one decimal (`28.8k`) |

Every option comes with a visual preview. Colors get a live ANSI preview in your terminal.

## Manual install

If you prefer not to use the skill, copy the config from [`settings-snippet.json`](./settings-snippet.json) directly into `~/.claude/settings.json`.

## Requirements

- `jq` (`brew install jq` / `apt install jq`)
