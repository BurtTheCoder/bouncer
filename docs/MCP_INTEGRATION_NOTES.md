# MCP Integration Notes

## Key Findings from Agent SDK Documentation

### How MCP Works in Agent SDK

1. **Configuration via .mcp.json**
   - MCP servers are configured in a `.mcp.json` file at project root
   - Can specify command, args, env variables
   - Supports stdio, HTTP/SSE, and SDK (in-process) transports

2. **Usage in Python Agent SDK**
   ```python
   from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
   
   options = ClaudeAgentOptions(
       cwd=str(codebase_dir),
       mcp_servers={
           "github": {
               "command": "npx",
               "args": ["-y", "@modelcontextprotocol/server-github"],
               "env": {
                   "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
               }
           }
       },
       allowed_tools=["mcp__github__create_pull_request"]
   )
   ```

3. **Tool Naming Convention**
   - MCP tools are prefixed: `mcp__<server_name>__<tool_name>`
   - Example: `mcp__github__create_pull_request`
   - Must be explicitly allowed in `allowed_tools`

4. **Available MCP Servers**
   - **GitHub**: Create PRs, issues, search repos, etc.
   - **GitLab**: Similar to GitHub
   - **Linear**: Create/update issues
   - **Jira**: Create/update tickets
   - **Filesystem**: Read/write files
   - **Database**: Query databases
   - Many more in the MCP ecosystem

### MCP Server Configuration Examples

#### GitHub MCP Server
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

#### GitLab MCP Server
```json
{
  "mcpServers": {
    "gitlab": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gitlab"],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "${GITLAB_TOKEN}"
      }
    }
  }
}
```

#### Linear MCP Server
```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-linear"],
      "env": {
        "LINEAR_API_KEY": "${LINEAR_API_KEY}"
      }
    }
  }
}
```

### Integration Strategy for Bouncer

1. **Configuration Layer**
   - Add `integrations` section to `bouncer.yaml`
   - Support GitHub, GitLab, Linear, Jira
   - Each integration can be enabled/disabled

2. **MCP Server Management**
   - Dynamically configure MCP servers based on enabled integrations
   - Pass MCP configuration to ClaudeAgentOptions
   - Handle authentication via environment variables

3. **Post-Bouncer Actions**
   - After bouncers find issues, offer to create:
     - **GitHub PR** with fixes
     - **GitLab MR** with fixes
     - **Linear issue** with investigation details
     - **Jira ticket** with findings
   
4. **Tool Selection**
   - Dynamically build `allowed_tools` list based on:
     - Enabled integrations
     - Bouncer results (issues vs fixes)
     - User preferences

5. **Workflow**
   ```
   Bouncer finds issues
   → Check enabled integrations
   → Ask Claude to create PR/issue
   → Use MCP tools to execute
   → Report results to user
   ```

### Example Integration Flow

```python
# After bouncer completes
if bouncer_result.fixes_applied:
    # Check if GitHub integration is enabled
    if config['integrations']['github']['enabled']:
        # Configure MCP server
        mcp_servers = {
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_TOKEN")
                }
            }
        }
        
        # Create PR with fixes
        options = ClaudeAgentOptions(
            cwd=str(codebase_dir),
            mcp_servers=mcp_servers,
            allowed_tools=[
                "mcp__github__create_pull_request",
                "mcp__github__create_or_update_file"
            ]
        )
        
        # Ask Claude to create PR
        prompt = f"""
        Create a GitHub PR with these fixes:
        {bouncer_result.fixes_applied}
        
        Title: Fix issues found by {bouncer_result.bouncer_name}
        Branch: bouncer/{bouncer_result.bouncer_name}/{timestamp}
        """
```

## Implementation Plan

### Phase 1: Configuration
- Add `integrations` section to config
- Support GitHub, GitLab, Linear, Jira
- Environment variable management

### Phase 2: MCP Manager
- Create `MCPManager` class
- Handle MCP server configuration
- Manage tool permissions

### Phase 3: Integration Actions
- Create `IntegrationActions` class
- Implement PR creation
- Implement issue creation
- Implement ticket creation

### Phase 4: Bouncer Integration
- Add post-bouncer hooks
- Offer integration actions after results
- Handle user confirmation

### Phase 5: Documentation
- Configuration guide
- Integration examples
- Troubleshooting

## Notes

- MCP servers run as external processes (npx commands)
- Authentication via environment variables
- Tools must be explicitly allowed
- Can run multiple MCP servers simultaneously
- Docker-friendly (no git credentials needed in container)
