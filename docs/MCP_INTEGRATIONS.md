# 🔗 MCP Integrations

Bouncer integrates with external services using the **Model Context Protocol (MCP)** to automatically create pull requests, issues, and tickets based on bouncer findings.

This enables a complete workflow:
1. **Bouncer finds issues** in your code
2. **Automatically create PRs** with fixes
3. **Create issues** for problems that need manual review
4. **Track work** in Linear, Jira, or your preferred tool

---

## 🎯 Supported Integrations

| Integration | Create PRs | Create Issues | Auto-fix | Status |
| :--- | :---: | :---: | :---: | :--- |
| **GitHub** | ✅ | ✅ | ✅ | Production |
| **GitLab** | ✅ | ✅ | ✅ | Production |
| **Linear** | ❌ | ✅ | ❌ | Production |
| **Jira** | ❌ | ✅ | ❌ | Production |

---

## ⚙️ Setup

### 1. Install MCP Servers

MCP servers are distributed as npm packages. They run as external processes and don't need to be installed in your project:

```bash
# No installation needed! 
# Bouncer will run them via npx automatically
```

### 2. Configure Environment Variables

Create a `.env` file with your credentials:

```bash
# Copy the example
cp examples/.env.example .env

# Edit with your credentials
nano .env
```

**Required environment variables:**

```bash
# GitHub
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here

# GitLab
GITLAB_PERSONAL_ACCESS_TOKEN=glpat-your_token_here

# Linear
LINEAR_API_KEY=lin_api_your_key_here

# Jira
JIRA_API_TOKEN=your.email@example.com:your_token_here
JIRA_BASE_URL=https://your-domain.atlassian.net
```

### 3. Enable Integrations

Add the `integrations` section to your `bouncer.yaml`:

```yaml
integrations:
  github:
    enabled: true
    auto_create_pr: false  # Ask before creating
    auto_create_issue: false
    branch_prefix: "bouncer"
  
  linear:
    enabled: true
    auto_create_issue: true  # Auto-create for errors
    project_id: "PROJ-123"
    team_id: "TEAM-456"
```

---

## 🚀 Usage

### Automatic PR Creation

When a bouncer finds issues and suggests fixes, you can automatically create a PR:

```bash
# Run bouncer with GitHub integration
bouncer start --config bouncer.yaml

# Or scan once
bouncer scan /path/to/project
```

**What happens:**
1. Bouncer finds issues and generates fixes
2. Creates a new branch (e.g., `bouncer/code_quality/20241205-103045`)
3. Applies fixes to the code
4. Commits changes
5. Pushes branch
6. Creates pull request with description

**Example PR:**
```
Title: Fix: Issues found by code_quality

Description:
This PR addresses issues found by the code_quality bouncer:

- Fixed undefined variable in main.py line 45
- Added null check in process_data() function
- Improved error handling in API client

File: src/main.py
```

### Automatic Issue Creation

For issues that need manual review:

```bash
# Issues are created automatically if auto_create_issue: true
bouncer scan /path/to/project
```

**Example GitHub Issue:**
```
Title: [security] Issues found in api_client.py

Description:
The security bouncer found the following issues:

- **high**: Potential SQL injection vulnerability in query builder
- **medium**: Hardcoded API key in configuration
- **low**: Missing input validation on user data

File: `src/api_client.py`

Labels: bouncer, security, automated
```

### Linear Issue Creation

Automatically create Linear issues for tracking:

```yaml
integrations:
  linear:
    enabled: true
    auto_create_issue: true
    project_id: "PROJ-123"
    team_id: "TEAM-456"
    default_priority: "high"
```

**Example Linear Issue:**
```
Title: [log_investigator] Issues in application.log

Description:
The log_investigator bouncer found the following issues:

- **ERROR**: NullPointerException in UserService.authenticate()
- **CRITICAL**: Database connection pool exhausted

File: `/var/log/myapp/application.log`

Priority: High
Project: Backend
Team: Engineering
```

---

## 📋 Configuration Reference

### GitHub Integration

```yaml
integrations:
  github:
    enabled: true
    
    # Automatic actions
    auto_create_pr: false      # Auto-create PRs without asking
    auto_create_issue: false   # Auto-create issues without asking
    
    # Branch settings
    branch_prefix: "bouncer"   # Prefix for auto-generated branches
    
    # Default labels for issues
    default_labels:
      - "bouncer"
      - "automated"
      - "needs-review"
    
    # Default assignees (GitHub usernames)
    default_assignees:
      - "username1"
      - "username2"
```

**Environment variables:**
- `GITHUB_PERSONAL_ACCESS_TOKEN` - Required, get from [GitHub Settings](https://github.com/settings/tokens)
- Required scopes: `repo`, `workflow`

---

### GitLab Integration

```yaml
integrations:
  gitlab:
    enabled: true
    
    # Automatic actions
    auto_create_mr: false      # Auto-create Merge Requests
    auto_create_issue: false   # Auto-create issues
    
    # Branch settings
    branch_prefix: "bouncer"
    
    # Target project (optional)
    project_id: "12345"
```

**Environment variables:**
- `GITLAB_PERSONAL_ACCESS_TOKEN` - Required, get from [GitLab Settings](https://gitlab.com/-/profile/personal_access_tokens)
- Required scopes: `api`, `write_repository`

---

### Linear Integration

```yaml
integrations:
  linear:
    enabled: true
    
    # Automatic actions
    auto_create_issue: true    # Auto-create issues
    
    # Required: Project and team IDs
    project_id: "PROJ-123"     # Find in Linear project settings
    team_id: "TEAM-456"        # Find in Linear team settings
    
    # Default priority
    default_priority: "medium" # low, medium, high, urgent
    
    # Default labels
    default_labels:
      - "bouncer"
      - "automated"
```

**Environment variables:**
- `LINEAR_API_KEY` - Required, get from [Linear API Settings](https://linear.app/settings/api)

---

### Jira Integration

```yaml
integrations:
  jira:
    enabled: true
    
    # Automatic actions
    auto_create_ticket: false
    
    # Required: Project key
    project_key: "PROJ"        # e.g., "MYAPP"
    
    # Default issue type
    default_issue_type: "Bug"  # Bug, Task, Story, etc.
    
    # Default priority
    default_priority: "Medium" # Lowest, Low, Medium, High, Highest
    
    # Default components
    default_components:
      - "Backend"
      - "API"
```

**Environment variables:**
- `JIRA_API_TOKEN` - Required, get from [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
- `JIRA_BASE_URL` - Required, e.g., `https://your-domain.atlassian.net`

---

## 🎯 Workflows

### Workflow 1: Continuous Monitoring with Auto-PRs

**Use case:** Development team wants automatic PRs for fixable issues.

```yaml
bouncers:
  code_quality:
    enabled: true
    auto_fix: false  # Don't auto-apply, create PR instead

integrations:
  github:
    enabled: true
    auto_create_pr: true   # Automatically create PRs
    auto_create_issue: false
```

```bash
# Start monitoring
bouncer start
```

**Result:** Every time a bouncer finds fixable issues, a PR is automatically created for review.

---

### Workflow 2: Scheduled Scans with Issue Tracking

**Use case:** Run daily scans and track issues in Linear.

```yaml
bouncers:
  security:
    enabled: true
  log_investigator:
    enabled: true

integrations:
  linear:
    enabled: true
    auto_create_issue: true
    project_id: "PROJ-123"
```

```bash
# Add to crontab
0 2 * * * bouncer scan /path/to/project
```

**Result:** Daily scans create Linear issues for any problems found.

---

### Workflow 3: Post-Deployment Checks

**Use case:** Scan logs after deployment and create Jira tickets for errors.

```yaml
bouncers:
  log_investigator:
    enabled: true
    log_dir: "/var/log/myapp"

integrations:
  jira:
    enabled: true
    auto_create_ticket: true
    project_key: "OPS"
```

```bash
# Run after deployment
bouncer scan /var/log/myapp --git-diff --since="1 hour ago"
```

**Result:** Creates Jira tickets for any errors found in recent logs.

---

### Workflow 4: Hybrid Approach (Recommended)

**Use case:** Auto-create PRs for fixes, issues for manual review.

```yaml
integrations:
  github:
    enabled: true
    auto_create_pr: true    # Auto-create PRs for fixes
    auto_create_issue: true # Auto-create issues for problems
  
  linear:
    enabled: true
    auto_create_issue: true # Also track in Linear
```

**Result:**
- **Fixable issues** → GitHub PR created automatically
- **Manual review needed** → GitHub issue + Linear issue created

---

## 🔧 Advanced Configuration

### Custom Branch Names

Control how branches are named:

```yaml
integrations:
  github:
    branch_prefix: "fix"  # Results in: fix/code_quality/timestamp
```

### Conditional Integration

Enable integrations only for specific bouncers:

```yaml
integrations:
  github:
    enabled: true
    # Only create PRs for these bouncers
    enabled_for_bouncers:
      - "code_quality"
      - "security"
  
  linear:
    enabled: true
    # Only create issues for these bouncers
    enabled_for_bouncers:
      - "log_investigator"
      - "performance"
```

### Multiple Repositories

Handle multiple repositories:

```yaml
integrations:
  github:
    enabled: true
    # Specify repository per bouncer
    repositories:
      code_quality: "owner/frontend-repo"
      security: "owner/backend-repo"
```

---

## 🐛 Troubleshooting

### Integration Not Working

**Problem:** Integration is enabled but nothing happens.

**Solutions:**

1. **Check environment variables:**
   ```bash
   echo $GITHUB_PERSONAL_ACCESS_TOKEN
   # Should output your token
   ```

2. **Validate configuration:**
   ```bash
   bouncer validate-config
   ```

3. **Check logs:**
   ```bash
   cat .bouncer/bouncer.log | grep -i integration
   ```

4. **Test MCP server manually:**
   ```bash
   npx -y @modelcontextprotocol/server-github
   ```

### Authentication Errors

**Problem:** "Authentication failed" or "Invalid token"

**Solutions:**

1. **Verify token scopes:**
   - GitHub: `repo`, `workflow`
   - GitLab: `api`, `write_repository`
   - Linear: Full access
   - Jira: Full access

2. **Check token expiration:**
   - Tokens may expire after a certain period
   - Generate a new token if needed

3. **Verify base URL (Jira):**
   ```bash
   echo $JIRA_BASE_URL
   # Should be: https://your-domain.atlassian.net
   ```

### PR/Issue Not Created

**Problem:** Bouncer runs but no PR/issue is created.

**Solutions:**

1. **Check if auto-create is enabled:**
   ```yaml
   integrations:
     github:
       auto_create_pr: true  # Must be true
   ```

2. **Check if bouncer found fixable issues:**
   ```bash
   # Look for "fixes_applied" in output
   bouncer scan /path/to/project
   ```

3. **Check repository permissions:**
   - Ensure token has write access to the repository
   - Verify repository exists and is accessible

### Docker Environment

**Problem:** MCP servers don't work in Docker.

**Solutions:**

1. **Install Node.js in Docker:**
   ```dockerfile
   FROM python:3.11
   
   # Install Node.js for MCP servers
   RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
   RUN apt-get install -y nodejs
   
   # Install Bouncer
   COPY . /app
   WORKDIR /app
   RUN pip install -r requirements.txt
   ```

2. **Pass environment variables:**
   ```bash
   docker run -e GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_TOKEN bouncer
   ```

3. **Use docker-compose:**
   ```yaml
   services:
     bouncer:
       image: bouncer:latest
       environment:
         - GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_TOKEN}
       volumes:
         - ./:/app
   ```

---

## 📊 Best Practices

### 1. Start with Manual Approval

Begin with `auto_create_pr: false` to review PRs before they're created:

```yaml
integrations:
  github:
    auto_create_pr: false  # Review first
```

### 2. Use Labels for Organization

Tag auto-created issues for easy filtering:

```yaml
integrations:
  github:
    default_labels:
      - "bouncer"
      - "automated"
      - "needs-review"
```

### 3. Separate Concerns

Use different integrations for different purposes:

```yaml
integrations:
  github:
    enabled: true  # For code fixes (PRs)
  
  linear:
    enabled: true  # For issue tracking
```

### 4. Monitor Integration Usage

Track how many PRs/issues are created:

```bash
# Check bouncer logs
cat .bouncer/bouncer.json | jq '.integrations'
```

### 5. Set Up Notifications

Get notified when integrations create PRs/issues:

```yaml
notifications:
  slack:
    enabled: true
    notify_on_pr_created: true
    notify_on_issue_created: true
```

---

## 🔮 Future Enhancements

Planned features for MCP integrations:

- **Auto-merge PRs** - Automatically merge PRs that pass CI
- **Comment on existing PRs** - Add bouncer findings to open PRs
- **Link issues to PRs** - Automatically link related issues and PRs
- **Custom MCP servers** - Support for custom/private MCP servers
- **Batch operations** - Create multiple PRs/issues in one run
- **Integration analytics** - Track PR acceptance rate, issue resolution time

---

## 📚 See Also

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Agent SDK MCP Guide](/home/ubuntu/agent_sdk_dataset/11_mcp.md)
- [Creating Custom Bouncers](CREATING_BOUNCERS.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Log Investigator](LOG_INVESTIGATOR.md)
