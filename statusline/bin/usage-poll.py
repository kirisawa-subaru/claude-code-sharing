#!/usr/bin/env python3
"""Fetch a model's weekly quota percentage (Fable, say) for the Claude Code status line.

Polls once, caches the number to ~/.claude/usage-cache.json, exits. The status
line reads that file and never touches the network itself.

Why this exists
---------------
Claude Code's status line payload only exposes two rate-limit buckets:
`rate_limits.five_hour` and `rate_limits.seven_day`. The per-model bars you see
in `/usage` come from a different source -- the usage endpoint's `limits[]`
array, whose model-scoped entries the status line projection drops.

This polls that endpoint out of band and writes a small JSON cache the status
line can read for free, so rendering never waits on the network.

What it does with your credentials
----------------------------------
Reads your existing Claude Code OAuth token (env var, credentials file, or
macOS Keychain -- in that order) and sends it to https://api.anthropic.com in
exactly one request, the same one the CLI itself makes. It never writes to your
credentials, and never refreshes the token: refresh tokens rotate, and racing
the CLI for one would break its stored credentials. If the token is expired it
reports that and keeps serving the last good numbers until the CLI refreshes.

Usage
-----
    usage-poll.py                 one shot, write cache, exit
    usage-poll.py --print         one shot, also print a summary
    usage-poll.py --list          print the model names available to display
    usage-poll.py --raw           dump the untouched API response
    usage-poll.py --max-age 600   skip the fetch if the cache is newer than N seconds
    usage-poll.py --loop 600      poll on an interval until killed

The status line snippet in this repo calls the no-argument form in the
background, so you normally never run this by hand.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

CLAUDE_DIR = os.path.expanduser("~/.claude")
CREDS = os.path.join(CLAUDE_DIR, ".credentials.json")
CACHE = os.path.join(CLAUDE_DIR, "usage-cache.json")
KEYCHAIN_SERVICE = "Claude Code-credentials"
ENDPOINT = "https://api.anthropic.com/api/oauth/usage"
OAUTH_BETA = "oauth-2025-04-20"
TIMEOUT = 10
MIN_INTERVAL = 60
STALE_AFTER = 6 * 3600


# --------------------------------------------------------------------------
# credentials
# --------------------------------------------------------------------------

def _from_env():
    tok = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    return (tok, None) if tok else None


def _from_file():
    try:
        with open(CREDS) as f:
            oauth = json.load(f)["claudeAiOauth"]
    except (OSError, KeyError, ValueError):
        return None
    tok = oauth.get("accessToken")
    return (tok, oauth.get("expiresAt")) if tok else None


def _from_keychain():
    if sys.platform != "darwin":
        return None
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    try:
        oauth = json.loads(out.stdout)["claudeAiOauth"]
    except (ValueError, KeyError, TypeError):
        return None
    tok = oauth.get("accessToken")
    return (tok, oauth.get("expiresAt")) if tok else None


def load_token():
    """Return (token, expires_at_ms|None), or None if no credentials found."""
    for source in (_from_env, _from_file, _from_keychain):
        got = source()
        if got:
            return got
    return None


# --------------------------------------------------------------------------
# fetch + projection
# --------------------------------------------------------------------------

def fetch(token):
    req = urllib.request.Request(
        ENDPOINT,
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": OAUTH_BETA,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())


def epoch(iso):
    """ISO8601-with-offset -> unix seconds, or None."""
    if not iso:
        return None
    try:
        return int(datetime.fromisoformat(iso).timestamp())
    except (ValueError, TypeError):
        return None


def bucket(b):
    if not isinstance(b, dict):
        return None
    return {
        "pct": b.get("utilization"),
        "resets_at": b.get("resets_at"),
        "resets_at_epoch": epoch(b.get("resets_at")),
    }


def project(raw):
    """Flatten the API response into the shape a status line actually wants."""
    models = {}
    for lim in raw.get("limits") or []:
        model = ((lim.get("scope") or {}).get("model") or {})
        name = model.get("display_name")
        if not name:
            continue
        models[name] = {
            "pct": lim.get("percent"),
            "kind": lim.get("kind"),
            "group": lim.get("group"),
            "severity": lim.get("severity"),
            "is_active": lim.get("is_active"),
            "resets_at": lim.get("resets_at"),
            "resets_at_epoch": epoch(lim.get("resets_at")),
            "model_id": model.get("id"),
        }

    extra = raw.get("extra_usage") or {}
    spend = raw.get("spend") or {}

    # Any other non-null top-level bucket, so new ones show up without a code change.
    known = {"five_hour", "seven_day", "extra_usage", "limits", "spend",
             "member_dashboard_available"}
    other = {k: bucket(v) for k, v in raw.items()
             if k not in known and isinstance(v, dict)}

    return {
        "ok": True,
        "fetched_at": int(time.time()),
        "five_hour": bucket(raw.get("five_hour")),
        "seven_day": bucket(raw.get("seven_day")),
        "models": models,
        "other_buckets": other,
        "extra_usage": {
            "enabled": extra.get("is_enabled"),
            "pct": extra.get("utilization"),
            "used_credits": extra.get("used_credits"),
            "monthly_limit": extra.get("monthly_limit"),
        },
        "spend": {
            "pct": spend.get("percent"),
            "enabled": spend.get("enabled"),
            "used_minor": (spend.get("used") or {}).get("amount_minor"),
            "currency": (spend.get("used") or {}).get("currency"),
        },
    }


# --------------------------------------------------------------------------
# cache
# --------------------------------------------------------------------------

def read_cache():
    try:
        with open(CACHE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def write_cache(payload):
    os.makedirs(CLAUDE_DIR, exist_ok=True)
    tmp = CACHE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, CACHE)  # atomic: readers never see a torn file


def degrade(reason, detail=None):
    """Keep last-good numbers, flag them stale, so the status line doesn't flicker."""
    prev = read_cache() or {}
    prev.update({
        "ok": False,
        "error": reason,
        "error_detail": detail,
        "last_error_at": int(time.time()),
    })
    prev.setdefault("fetched_at", None)
    return prev


def poll_once():
    creds = load_token()
    if not creds:
        return degrade("no_credentials",
                       "set CLAUDE_CODE_OAUTH_TOKEN or sign in with the CLI")
    token, expires_at = creds

    if expires_at and expires_at / 1000 <= time.time():
        # The CLI refreshes on its own next API call; we re-read the file then.
        return degrade("token_expired", "run any claude command to refresh")

    try:
        raw = fetch(token)
    except urllib.error.HTTPError as e:
        return degrade(f"http_{e.code}", e.reason)
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        return degrade("fetch_failed", str(e))

    if not isinstance(raw, dict):
        return degrade("bad_response", type(raw).__name__)

    return project(raw)


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def render(p):
    if not p.get("ok"):
        age = ""
        if p.get("fetched_at"):
            age = f" (last good {int(time.time()) - p['fetched_at']}s ago)"
        return f"error: {p.get('error')} -- {p.get('error_detail')}{age}"

    stale = ""
    if p.get("fetched_at") and time.time() - p["fetched_at"] > STALE_AFTER:
        # Same threshold the status line uses before it falls back to "--%".
        hours = (time.time() - p["fetched_at"]) / 3600
        stale = f"  (stale: last fetched {hours:.1f}h ago)"

    def line(label, b):
        if not b or b.get("pct") is None:
            return f"  {label:<30} --"
        resets = ""
        if b.get("resets_at_epoch"):
            mins = (b["resets_at_epoch"] - time.time()) / 60
            resets = f"  resets in {mins/60:.1f}h" if mins >= 60 else f"  resets in {mins:.0f}m"
        return f"  {label:<30} {b['pct']:>5.1f}%{resets}"

    out = []
    if stale:
        out.append(stale.strip())
    out += [line("current session (5h)", p["five_hour"]),
            line("current week (all models)", p["seven_day"])]
    for name, m in sorted(p["models"].items()):
        out.append(line(f"current week ({name})", m))
    for name, b in sorted(p.get("other_buckets", {}).items()):
        if b and b.get("pct") is not None:
            out.append(line(f"[{name}]", b))
    eu = p.get("extra_usage") or {}
    tail = f" {eu['pct']:.1f}%" if eu.get("pct") is not None else ""
    out.append(f"  {'extra usage credits':<30} "
               f"{'enabled' if eu.get('enabled') else 'disabled'}{tail}")
    return "\n".join(out)


def cache_age():
    try:
        return time.time() - os.path.getmtime(CACHE)
    except OSError:
        return None


def main():
    ap = argparse.ArgumentParser(
        description="Fetch a model's weekly quota percentage (Fable, say) and cache "
                    "it for the Claude Code status line, which reads the cache "
                    "instead of the network.")
    ap.add_argument("--loop", type=int, metavar="SECONDS",
                    help=f"poll forever at this interval (min {MIN_INTERVAL})")
    ap.add_argument("--max-age", type=int, metavar="SECONDS",
                    help="do nothing if the cache is newer than this")
    ap.add_argument("--print", dest="show", action="store_true",
                    help="also print every quota this account has, as text")
    ap.add_argument("--list", action="store_true",
                    help="list which models have their own weekly quota here")
    ap.add_argument("--raw", action="store_true",
                    help="print the untouched API response and exit")
    args = ap.parse_args()

    if args.raw:
        creds = load_token()
        if not creds:
            print("no credentials found", file=sys.stderr)
            return 1
        json.dump(fetch(creds[0]), sys.stdout, indent=2)
        print()
        return 0

    if args.list:
        p = read_cache()
        if not p or not p.get("models"):
            p = poll_once()
            write_cache(p)
        names = sorted((p.get("models") or {}).keys())
        if not names:
            print("no model-scoped limits in this account's usage response")
            return 1
        for n in names:
            print(f"{n}\t{p['models'][n].get('pct')}%")
        return 0

    if args.loop:
        interval = max(args.loop, MIN_INTERVAL)
        while True:
            p = poll_once()
            write_cache(p)
            if args.show:
                print(f"[{datetime.now():%H:%M:%S}]")
                print(render(p), flush=True)
            time.sleep(interval)

    if args.max_age is not None:
        age = cache_age()
        if age is not None and age < args.max_age:
            if args.show:
                print(render(read_cache() or {}))
            return 0

    p = poll_once()
    write_cache(p)
    if args.show:
        print(render(p))
    return 0 if p.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
