# Claude Code Status Line

通过交互式的方式, 方便的设置claude code statusline的格式

### 预览:  
<img width="612" height="151" alt="image" src="https://github.com/user-attachments/assets/fd9cc417-56e8-4c57-b7d1-2527d4b8e914" />

```
context: 28.8k  |  5h: 0%  |  7d: 28%  |  Opus 4.6 (1M context)
```

### 设置过程: 
<img width="1175" height="308" alt="image" src="https://github.com/user-attachments/assets/c84d5531-9abd-4502-b9cf-ffe7c8e9a447" /><br>
<img width="631" height="310" alt="image" src="https://github.com/user-attachments/assets/8143bdf8-4414-46e9-9dad-4f35d2673da9" />

## Why not the built-in `/statusline`?

The official command generates a status line with no layout constraints — font weight, spacing, information density are all uncontrolled. The result usually looks like an afterthought.

This one gives you pre-designed presets with curated typography, and lets you customize through selection rather than free-form prompting.

## Setup

Open a **new Claude Code session** (Sonnet or Opus), paste this link and say **"请按照该链接设置 statusline"** or **"Set up my status line using this link"**:

```
https://raw.githubusercontent.com/kirisawa-subaru/claude-code-sharing/main/statusline/skill/statusline-setup.md
```

Claude will fetch the instructions and walk you through 4 interactive steps. Nothing is installed, nothing to clean up.

### Alternative: install as a slash command

If you prefer a reusable `/statusline-setup` command:

```bash
mkdir -p ~/.claude/agents && curl -sL https://raw.githubusercontent.com/kirisawa-subaru/claude-code-sharing/main/statusline/skill/statusline-setup.md -o ~/.claude/agents/statusline-setup.md
```

The skill self-deletes after writing your config. Re-run the command above to reconfigure.

## What's configurable

| Step | Options |
|------|---------|
| **Layout** | Minimal (labels stripped), Standard (labeled), Full (+ timestamps + cost), or design your own |
| **Colors** | Moonlight (blue), Mono (gray), Clean (white), or create your own with live terminal preview |
| **Separator** | Pipe `\|`, dot `·`, slim, or any character you like |
| **Precision** | Whole numbers (`29k`) or one decimal (`28.8k`) |

Every option comes with a visual preview. Colors get a live ANSI preview in your terminal.

## Manual install

If you prefer not to use the interactive setup, copy the config from [`settings-snippet.json`](./settings-snippet.json) directly into `~/.claude/settings.json`.

## Requirements

- `jq` (`brew install jq` / `apt install jq`)
