# When the fields move

Everything the status line reads is undocumented surface owned by someone else. Buckets get renamed, models get added, projections change. This is how to find the new truth quickly instead of rediscovering it from scratch.

Read this before changing `bin/usage-poll.py` or the jq in `settings-snippet-model-usage.json`.

## The two data paths, and why they disagree

They are not the same source, and confusing them wastes the most time.

| | Status line payload | `/usage` panel |
|---|---|---|
| Delivered by | JSON on the command's **stdin** | usage endpoint response |
| Rate-limit content | `rate_limits.five_hour`, `rate_limits.seven_day` — **that is all** | `five_hour`, `seven_day`, `seven_day_opus`, `seven_day_sonnet`, `seven_day_oauth_apps`, `cinder_cove`, `extra_usage`, `limits[]`, plus codenamed buckets |
| Per-model numbers | none | `limits[]` entries with `kind: "weekly_scoped"` and `scope.model.display_name` |

The status line builder hardcodes the two-bucket projection and drops the rest. That is the entire reason this directory exists. If a future release widens that projection, delete the poller — check the payload first.

Note the client applies one more filter the raw response does not: `/usage` only renders a model-scoped bar whose `display_name` is in a remote-config allowlist (`tengu_usage_overage_included_models`). `limits[]` can legitimately contain models the panel refuses to show, so **the panel is not ground truth** — the endpoint is.

## First move: ask the API

Covers almost all drift, costs one request:

```bash
~/.claude/bin/usage-poll.py --raw
```

Compare against what `project()` in `bin/usage-poll.py` expects:

| Reads | Currently |
|---|---|
| `limits[]` | array of limit objects |
| `limits[].kind` | `session`, `weekly_all`, `weekly_scoped` |
| `limits[].percent` | integer (note: `five_hour.utilization` is a float — both must survive the same formatter) |
| `limits[].resets_at` | ISO 8601 with offset, e.g. `2026-08-26T21:00:00.094726+00:00` |
| `limits[].scope.model.display_name` | e.g. `Fable`; `scope.model.id` has been null in practice |

`project()` is written to tolerate additions: unknown non-null top-level objects land in `other_buckets`, and any `limits[]` entry carrying a `scope.model.display_name` becomes a `models` key regardless of `kind`. Renames and type changes are what break it.

## Second move: read the CLI binary

Needed when the endpoint itself moves, when the status line payload changes, or when you need to know what the client does with a field rather than what it contains.

The CLI ships as a single ~330 MB executable with readable JavaScript and its own documentation embedded:

```
$(dirname $(readlink -f $(command -v claude)))/../node_modules/@anthropic-ai/claude-code-<platform>/claude
```

`readlink -f $(command -v claude)` gets you there directly.

**The technique that works.** Get byte offsets with a fixed-string search, then read around them:

```bash
B=<path to the binary>
grep -abo -F 'exceeds_200k_tokens' "$B"          # -> 180824224:exceeds_200k_tokens
dd if="$B" bs=1 skip=180823200 count=2600 2>/dev/null | tr -d '\0'
```

**Two traps.** A regex with wide context (`grep -oE '.{600}TARGET.{600}'`) takes minutes or never finishes on a file this size — always `grep -abo -F` first, then `dd`. And `strings` may not be installed; `grep -a` works without it.

**Known anchors.** These were the useful ones; they are stable enough to be worth trying first.

| Search for | Lands on |
|---|---|
| `exceeds_200k_tokens` | the status line payload builder — the definitive list of fields a command can receive |
| `"rate_limits": {` | the bundled status line schema docs, with per-field comments |
| `statusLine command will receive` | the bundled status line setup docs, including platform notes |
| `/api/oauth/usage` | the usage fetch, with its headers and retry behaviour |
| `seven_day_opus` | the rate-limit header bucket names, and the full bucket list constant |
| `weekly_scoped` | the model-scoped projection and the allowlist gate that filters it |
| `cinder_cove` | the `/usage` panel renderer, including the codenamed one-off credit bars |

The embedded docs are worth checking before the code: they are prose, they are current, and they state things the minified code does not, such as which shell the command runs under on each platform.

## Third move: check whether this is still needed

If the status line payload ever grows model-scoped limits, or if a `claude usage --json` subcommand appears, this whole directory becomes redundant. Both are cheap to check:

```bash
claude --help | sed -n '/^Commands:/,$p'
```
