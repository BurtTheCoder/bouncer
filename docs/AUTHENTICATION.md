# Bouncer Authentication Guide

Complete guide to authenticating Bouncer with Claude AI.

---

## 🔐 Overview

Bouncer uses the [Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview) which supports **two authentication methods**:

1. **Claude Code OAuth** - Unlimited usage for Claude Code subscribers
2. **Anthropic API Key** - Pay-per-use for non-subscribers

The SDK automatically checks for credentials in this order:
1. `ANTHROPIC_API_KEY` environment variable
2. Claude Code OAuth credentials (`~/.claude.json` or macOS Keychain)

---

## 🎯 Method 1: Claude Code OAuth (Recommended)

### Who Should Use This?

✅ **You have a Claude Code subscription** (Pro, Team, or Enterprise)  
✅ **You want unlimited usage** without pay-per-use costs  
✅ **You're running Bouncer locally** on your development machine  

### Benefits

| Benefit | Description |
|---------|-------------|
| **Unlimited Usage** | Included in your Claude Code subscription |
| **No Extra Costs** | No pay-per-use API charges |
| **Automatic** | No manual credential management |
| **Secure** | Encrypted storage (macOS Keychain or file permissions) |
| **Multi-Project** | Works across all your projects automatically |

### Setup Instructions

#### Step 1: Install Claude Code

Download and install Claude Code for your platform:

- **macOS/Linux:** https://code.claude.com/download
- **Windows:** https://code.claude.com/download

Or install via package manager:

```bash
# macOS (Homebrew)
brew install --cask claude-code

# Linux (npm)
npm install -g @anthropic-ai/claude-code

# Windows (Chocolatey)
choco install claude-code
```

#### Step 2: Authenticate Claude Code

Open Claude Code and run the `/login` command:

```
/login
```

This will:
1. Open your browser for authentication
2. Ask you to sign in with your Anthropic account
3. Store OAuth tokens securely on your system

#### Step 3: Verify Authentication

Check that Bouncer can access your credentials:

```bash
bouncer auth-status
```

You should see:

```
✅ AUTHENTICATED

  🔐 OAuth: Active
     Source: Claude Code authentication
     Usage: Unlimited (Claude Code subscription)

✅ Bouncer is ready to use!
```

#### Step 4: Start Using Bouncer

No additional configuration needed! Just run:

```bash
bouncer start
```

Bouncer will automatically use your Claude Code OAuth credentials.

### Where Are Credentials Stored?

| Platform | Storage Location | Security |
|----------|-----------------|----------|
| **macOS** | macOS Keychain (encrypted) | ✅ Highly Secure |
| **Linux** | `~/.claude.json` | ⚠️ File permissions (chmod 600) |
| **Windows** | `%USERPROFILE%\.claude.json` | ⚠️ File permissions |

**macOS users:** Credentials are stored in the encrypted macOS Keychain, which requires user authentication to access.

**Linux/Windows users:** Credentials are stored in a JSON file. Ensure it has restrictive permissions:

```bash
chmod 600 ~/.claude.json  # Linux/macOS
```

### Troubleshooting OAuth

#### "OAuth session not found"

**Cause:** Claude Code not authenticated or credentials expired

**Solution:**
1. Open Claude Code
2. Run `/login` again
3. Complete authentication flow
4. Run `bouncer auth-status` to verify

#### "Permission denied: ~/.claude.json"

**Cause:** Incorrect file permissions

**Solution:**
```bash
chmod 600 ~/.claude.json
```

#### "OAuth token expired"

**Cause:** Token needs refresh

**Solution:**
1. Open Claude Code (this auto-refreshes tokens)
2. Or run `/login` again to re-authenticate

---

## 💡 Method 2: Anthropic API Key

### Who Should Use This?

✅ **You don't have a Claude Code subscription**  
✅ **You're running Bouncer in Docker or CI/CD**  
✅ **You want explicit control over credentials**  

### Setup Instructions

#### Step 1: Get an API Key

1. Go to the [Anthropic Console](https://console.anthropic.com/settings/keys)
2. Sign in or create an account
3. Click "Create Key"
4. Give it a name (e.g., "Bouncer")
5. Copy the key (starts with `sk-ant-...`)

⚠️ **Important:** Save the key immediately - you won't be able to see it again!

#### Step 2: Set Environment Variable

**Option A: Environment Variable (Recommended for Docker/CI/CD)**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Make it permanent by adding to your shell profile:

```bash
# ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY=sk-ant-...
```

**Option B: .env File (Recommended for Local Development)**

Create a `.env` file in your project directory:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
```

⚠️ **Security:** Add `.env` to `.gitignore` to prevent committing secrets!

```bash
# .gitignore
.env
```

#### Step 3: Verify Authentication

```bash
bouncer auth-status
```

You should see:

```
✅ AUTHENTICATED

  🔑 API Key: sk-ant-...xyz
     Source: ANTHROPIC_API_KEY environment variable
     Usage: Pay-per-use

✅ Bouncer is ready to use!
```

#### Step 4: Start Using Bouncer

```bash
bouncer start
```

### API Key Best Practices

✅ **DO:**
- Use environment variables for production
- Rotate keys regularly
- Create separate keys for different environments (dev, staging, prod)
- Revoke unused keys immediately
- Use `.env` files for local development
- Add `.env` to `.gitignore`

❌ **DON'T:**
- Commit API keys to git
- Share keys between team members
- Hardcode keys in code
- Use the same key for all environments
- Leave unused keys active

---

## 🐳 Docker Authentication

### Recommended: API Key

For Docker deployments, **use API keys** instead of OAuth for cleaner separation:

```bash
docker run -e ANTHROPIC_API_KEY=sk-ant-... bouncer
```

Or with docker-compose:

```yaml
# docker-compose.yml
services:
  bouncer:
    image: bouncer:latest
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./bouncer.yaml:/app/bouncer.yaml
```

Then create a `.env` file:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
```

And run:

```bash
docker-compose up
```

### Alternative: Mount OAuth Credentials

You can mount your Claude Code credentials into the container:

```bash
docker run \
  -v ~/.claude.json:/root/.claude.json:ro \
  bouncer
```

**Pros:**
- ✅ Uses your Claude Code subscription (unlimited)
- ✅ No separate API key needed

**Cons:**
- ⚠️ Shares credentials with container
- ⚠️ May have permission issues
- ⚠️ Less secure (credentials accessible to container)

**Recommendation:** Use API keys for Docker unless you specifically need OAuth.

---

## 🔄 CI/CD Authentication

### GitHub Actions

Store your API key in GitHub Secrets:

1. Go to repository Settings → Secrets → Actions
2. Click "New repository secret"
3. Name: `ANTHROPIC_API_KEY`
4. Value: `sk-ant-...`
5. Click "Add secret"

Then use in your workflow:

```yaml
# .github/workflows/bouncer.yml
name: Bouncer Quality Check

on: [pull_request]

jobs:
  bouncer:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install Bouncer
        run: |
          pip install -r requirements.txt
      
      - name: Run Bouncer
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          bouncer scan . --report-only
```

### GitLab CI

Add API key to GitLab CI/CD variables:

1. Go to Settings → CI/CD → Variables
2. Click "Add variable"
3. Key: `ANTHROPIC_API_KEY`
4. Value: `sk-ant-...`
5. Check "Mask variable"
6. Click "Add variable"

Then use in your pipeline:

```yaml
# .gitlab-ci.yml
bouncer:
  image: python:3.10
  before_script:
    - pip install -r requirements.txt
  script:
    - bouncer scan . --report-only
  variables:
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
```

### Other CI/CD Platforms

**Jenkins:**
```groovy
withCredentials([string(credentialsId: 'anthropic-api-key', variable: 'ANTHROPIC_API_KEY')]) {
    sh 'bouncer scan . --report-only'
}
```

**CircleCI:**
```yaml
- run:
    name: Run Bouncer
    command: bouncer scan . --report-only
    environment:
      ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
```

---

## 🔍 Authentication Priority

When both authentication methods are available, the SDK checks in this order:

1. **`ANTHROPIC_API_KEY` environment variable** (highest priority)
2. **Claude Code OAuth credentials** (fallback)

### Example Scenarios

**Scenario 1: Both Available**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# Also have Claude Code authenticated
bouncer start
```
→ Uses API key (environment variable takes priority)

**Scenario 2: Only OAuth**
```bash
# No ANTHROPIC_API_KEY set
# Claude Code authenticated
bouncer start
```
→ Uses Claude Code OAuth

**Scenario 3: Only API Key**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# Claude Code not installed/authenticated
bouncer start
```
→ Uses API key

**Scenario 4: Neither Available**
```bash
# No ANTHROPIC_API_KEY
# No Claude Code authentication
bouncer start
```
→ Error: "Not authenticated"

---

## 🔐 Security Best Practices

### General

✅ **Use OAuth for local development** (if you have Claude Code)  
✅ **Use API keys for automation** (Docker, CI/CD)  
✅ **Never commit credentials to git**  
✅ **Rotate API keys regularly** (every 90 days)  
✅ **Use separate keys per environment**  
✅ **Revoke unused keys immediately**  

### File Permissions

Protect credential files on Linux/Windows:

```bash
# Claude Code OAuth
chmod 600 ~/.claude.json

# .env file
chmod 600 .env
```

### macOS Keychain

macOS users get automatic encryption via Keychain. No additional action needed.

### Docker Security

✅ **DO:**
- Use environment variables for secrets
- Use Docker secrets for Swarm deployments
- Use read-only mounts: `-v ~/.claude.json:/root/.claude.json:ro`
- Never include credentials in Docker images

❌ **DON'T:**
- Hardcode credentials in Dockerfile
- Commit .env files with credentials
- Use the same credentials for all containers

---

## 🆘 Troubleshooting

### "No API key found"

**Symptoms:**
```
❌ NOT AUTHENTICATED
```

**Cause:** Neither OAuth nor API key configured

**Solution:**
1. Run `bouncer auth-status` to check status
2. Either authenticate Claude Code (`/login`) or set `ANTHROPIC_API_KEY`
3. Verify with `bouncer auth-status` again

### "Invalid API key"

**Symptoms:**
```
Error: Invalid authentication credentials
```

**Cause:** API key is incorrect or revoked

**Solution:**
1. Check your API key in the [Anthropic Console](https://console.anthropic.com/settings/keys)
2. Create a new key if needed
3. Update your environment variable or `.env` file

### "Permission denied: ~/.claude.json"

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/home/user/.claude.json'
```

**Cause:** Incorrect file permissions

**Solution:**
```bash
chmod 600 ~/.claude.json
```

### "OAuth token expired"

**Symptoms:**
```
Error: OAuth session expired
```

**Cause:** OAuth token needs refresh

**Solution:**
1. Open Claude Code (auto-refreshes tokens)
2. Or run `/login` again to re-authenticate

### Docker: "Authentication not working"

**Symptoms:**
```
Error: No API key found
```

**Cause:** Environment variable not passed to container

**Solution:**
```bash
# Verify environment variable is set
echo $ANTHROPIC_API_KEY

# Pass it to Docker
docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY bouncer

# Or use docker-compose with .env file
docker-compose up
```

---

## 📊 Quick Reference

| Scenario | Recommended Method | Command |
|----------|-------------------|---------|
| **Local Development (Claude Code subscriber)** | OAuth | `/login` in Claude Code |
| **Local Development (No subscription)** | API Key + .env | `export ANTHROPIC_API_KEY=...` |
| **Docker** | API Key | `docker run -e ANTHROPIC_API_KEY=...` |
| **CI/CD** | API Key (secrets) | Use platform's secret management |

---

## 🔗 Related Documentation

- **[Claude Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview)** - Official SDK documentation
- **[Claude Code IAM](https://code.claude.com/docs/en/iam)** - Identity and access management
- **[Anthropic Console](https://console.anthropic.com/)** - Manage API keys
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Docker and production deployment
- **[WIZARD.md](WIZARD.md)** - Interactive setup wizard

---

## ✅ Summary

**For Claude Code Subscribers:**
1. Install Claude Code
2. Run `/login`
3. Run `bouncer auth-status` to verify
4. Start using Bouncer (unlimited usage!)

**For Non-Subscribers:**
1. Get API key from Anthropic Console
2. Set `ANTHROPIC_API_KEY` environment variable
3. Run `bouncer auth-status` to verify
4. Start using Bouncer (pay-per-use)

**For Docker/CI/CD:**
1. Use API key method
2. Store in secrets/environment variables
3. Never commit credentials to git

**Need Help?**
- Run `bouncer auth-status` to diagnose issues
- Check this guide's troubleshooting section
- Open an issue on GitHub
