# Claude Code Status Line

方便的设置claude code statusline / Easy setup for Claude Code status line

### 预览 / Preview:  
<img width="612" height="151" alt="image" src="https://github.com/user-attachments/assets/fd9cc417-56e8-4c57-b7d1-2527d4b8e914" />

```
context: 28.8k  |  5h: 0%  |  7d: 28%  |  Opus 4.6 (1M context)
```

### 设置过程 / Setup process: 
<img width="1175" height="308" alt="image" src="https://github.com/user-attachments/assets/c84d5531-9abd-4502-b9cf-ffe7c8e9a447" /><br>
<img width="631" height="310" alt="image" src="https://github.com/user-attachments/assets/8143bdf8-4414-46e9-9dad-4f35d2673da9" />

### 使用方式 / Usage

打开**新的 Claude Code session** (Sonnet or Opus), 粘贴链接并告诉 Claude **"请按照该链接设置 statusline"** or **"Set up my status line using this link"**:

Open a **new Claude Code session** (Sonnet or Opus), paste this link and say **"Set up my status line using this link"**:

```
https://raw.githubusercontent.com/kirisawa-subaru/claude-code-sharing/main/statusline/skill/statusline-setup.md
```

然后交给 Claude, 通过交互式的操作进行设置就好.

Then let Claude walk you through the interactive setup.

<details>
<summary>为什么不用官方的 /statusline？/ Why not the built-in /statusline?</summary>

官方命令生成的 status line 没有排版约束——字重、间距、信息密度都不受控。出来的效果通常像是临时凑的。

这个工具提供预设好的排版方案，通过选择而不是自由输入来定制。

The official command generates a status line with no layout constraints — font weight, spacing, information density are all uncontrolled. The result usually looks like an afterthought.

This one gives you pre-designed presets with curated typography, and lets you customize through selection rather than free-form prompting.

</details>

<details>
<summary>备选：安装为 slash command / Alternative: install as a slash command</summary>

如果你想要一个可复用的 `/statusline-setup` 命令：

If you prefer a reusable `/statusline-setup` command:

```bash
mkdir -p ~/.claude/agents && curl -sL https://raw.githubusercontent.com/kirisawa-subaru/claude-code-sharing/main/statusline/skill/statusline-setup.md -o ~/.claude/agents/statusline-setup.md
```

Skill 会在写入配置后自动删除。重新运行上述命令即可重新配置。

The skill self-deletes after writing your config. Re-run the command above to reconfigure.

</details>

<details>
<summary>可配置项 / What's configurable</summary>

| 步骤 / Step | 选项 / Options |
|------|---------|
| **布局 / Layout** | Minimal（去标签）、Standard（带标签）、Full（+时间戳+费用）、或自行设计 |
| **颜色 / Colors** | Moonlight（蓝）、Mono（灰）、Clean（白）、或自定义并实时终端预览 |
| **分隔符 / Separator** | 竖线 `\|`、点 `·`、紧凑、或任意字符 |
| **精度 / Precision** | 整数（`29k`）或一位小数（`28.8k`） |

每个选项都有视觉预览。颜色会在终端中显示实时 ANSI 预览。

Every option comes with a visual preview. Colors get a live ANSI preview in your terminal.

</details>

<details>
<summary>手动安装 / Manual install</summary>

如果你不想用交互式设置，直接把 [`settings-snippet.json`](./settings-snippet.json) 的配置复制到 `~/.claude/settings.json`。

If you prefer not to use the interactive setup, copy the config from [`settings-snippet.json`](./settings-snippet.json) directly into `~/.claude/settings.json`.

</details>

<details>
<summary>依赖 / Requirements</summary>

- `jq` (`brew install jq` / `apt install jq`)

</details>
