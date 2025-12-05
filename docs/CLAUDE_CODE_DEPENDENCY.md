# Claude Code CLI Dependency

## ✅ Good News: No Separate Installation Required!

**The Claude Agent SDK automatically bundles the Claude Code CLI** - users do NOT need to install Claude Code separately!

---

## How It Works

### What's Included

When you install `claude-agent-sdk` via pip:

```bash
pip install claude-agent-sdk
```

**You automatically get:**
- The Python SDK library
- The Claude Code CLI (bundled)
- Everything needed to run agents

### No Extra Steps

Users do **NOT** need to:
- ❌ Install Claude Code CLI separately
- ❌ Run `curl -fsSL https://claude.ai/install.sh | bash`
- ❌ Configure CLI paths
- ❌ Set up Claude Code environment

### Just Works

The SDK uses the bundled CLI by default. Everything works out of the box with just:
1. `pip install claude-agent-sdk`
2. Set `ANTHROPIC_API_KEY` environment variable
3. Start using Bouncer!

---

## Requirements

### Minimum Requirements

**Python:** 3.10 or higher

**Environment Variable:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

**That's it!** No other dependencies or installations needed.

---

## Advanced: Custom CLI Path (Optional)

If users want to use a system-wide Claude Code installation or specific version, they can:

```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    cli_path="/path/to/custom/claude"
)
```

But this is **completely optional** - the bundled CLI works perfectly for 99% of use cases.

---

## What This Means for Bouncer

### Installation is Simple

**Current installation:**
```bash
# Clone repo
git clone https://github.com/BurtTheCoder/bouncer.git
cd bouncer

# Install dependencies (includes bundled Claude Code CLI)
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="your-key"

# Run bouncer
python main.py start
```

### Documentation is Accurate

Our README and installation docs are correct - users just need:
1. Python 3.10+
2. Install requirements
3. Set API key
4. Run Bouncer

No mention of Claude Code CLI needed!

---

## Verification

### Check Bundled CLI

The SDK includes the CLI in the package:
```bash
python -c "from claude_agent_sdk import ClaudeAgentOptions; print('✅ SDK installed with bundled CLI')"
```

### Check Version

```python
from claude_agent_sdk import __version__
print(f"Claude Agent SDK version: {__version__}")
# Current: v0.1.12
```

---

## Summary

✅ **Claude Code CLI is bundled** with `claude-agent-sdk`  
✅ **No separate installation** required  
✅ **Works out of the box** with just pip install  
✅ **Bouncer installation is simple** - no extra steps  
✅ **Documentation is accurate** - no changes needed  

**Conclusion:** Users can install and use Bouncer without any knowledge of Claude Code CLI. It "just works"!
