# MCPleasant: The ONE Command AI Coding Assistant

## 🎯 The Promise

**ONE command. Working AI in VSCode. Done.**

No setup, no config, no second step, no bullshit.

## The ONE Command

```bash
python mcpleasant.py
```

That's it. Seriously.

## What Happens

1. ✅ Installs Continue.dev extension automatically
2. ✅ Configures everything automatically  
3. ✅ Starts AI servers automatically
4. ✅ Opens VSCode automatically
5. ✅ Ready to code with AI immediately

## Test It Works

After running `python mcpleasant.py`:

1. VSCode opens automatically
2. Create new Python file
3. Type: `def fibonacci(n):`
4. See AI completion appear instantly

## What You Get

- **Code completion**: AI suggests code as you type
- **Code explanation**: Select code, ask "what does this do?"
- **Debugging help**: Paste errors, get fix suggestions
- **100% offline**: Your code never leaves your machine
- **Zero config**: No files to edit, no settings to change

## Requirements

- Python 3.9+
- VSCode installed
- Internet (for initial setup only)

## How It Works

MCPleasant creates:
- Lightweight MCP server for AI logic
- HTTP API wrapper (OpenAI-compatible)
- Auto-configured Continue.dev extension
- Everything runs locally on port 8000

## Stop MCPleasant

Press `Ctrl+C` in the terminal where you ran `python mcpleasant.py`

## Troubleshooting

**No AI completions?**
- Check terminal shows "MCPleasant READY!"
- Restart VSCode if needed
- Make sure port 8000 isn't blocked

**Extension not installed?**
- Run manually: `code --install-extension Continue.continue`
- Restart VSCode

**Still not working?**
- Check Continue.dev output panel in VSCode
- Verify config at `~/.continue/config.json`

## The Real Test

If you can't get AI completions working in VSCode within 2 minutes of running `python mcpleasant.py`, then we failed.

But if it works, then we actually delivered: **Easy to use out of the box.**

---

## Comparison

**Before MCPleasant:**
1. Install dependencies
2. Download models  
3. Configure servers
4. Install VSCode extension
5. Edit config files
6. Restart VSCode
7. Start servers manually
8. Hope it works

**With MCPleasant:**
1. `python mcpleasant.py`

**That's the difference.**

---

**Bottom Line**: One command, two minutes, working AI in VSCode. No exceptions.

🚀 **Try it now**: `python mcpleasant.py`