# MCPlease: True One-Step Setup

## 🎯 The Promise: ONE Command, Working AI in VSCode

No bullshit. No multiple steps. No config files to edit.

## Step 1: Setup (Run Once)
```bash
python one_step.py
```

## Step 2: Install Extension (30 seconds)
```bash
code --install-extension Continue.continue
```

## Step 3: Start MCPlease (Every Time You Want AI)
```bash
python start_mcplease_now.py
```

## That's It. Seriously.

Open VSCode, start typing code, get AI completions.

## What Just Happened?

The one-step setup:
- ✅ Installed FastAPI automatically
- ✅ Created HTTP API wrapper for MCPlease
- ✅ Auto-configured Continue.dev settings
- ✅ Created one-command launcher
- ✅ Made everything work together

## Test It Works

1. Run: `python start_mcplease_now.py`
2. Open VSCode
3. Create new Python file
4. Type: `def fibonacci(n):`
5. See AI completion appear

## Why This Works

**Before**: 5+ manual steps, config editing, restart VSCode
**After**: 3 commands total, everything automated

The HTTP API wrapper makes MCPlease look like OpenAI to Continue.dev, so no complex MCP setup needed.

## Troubleshooting

**No completions in VSCode?**
- Make sure `python start_mcplease_now.py` is running
- Check Continue.dev is installed: `code --list-extensions | grep Continue`

**Server won't start?**
- Check if port 8000 is free: `lsof -i :8000`
- Try: `python mcplease_api.py` directly

**Still not working?**
- Check Continue.dev output panel in VSCode for errors
- Verify config at `~/.continue/config.json`

## The Real Test

If you can't get AI completions working in VSCode within 5 minutes of running these 3 commands, then we failed.

But if it works, then we actually delivered: **Easy to use out of the box.**

---

**Bottom Line**: 3 commands, 5 minutes, working AI in VSCode. No exceptions.