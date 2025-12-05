# 🔐 Authentication & Model Configuration

This guide covers all the authentication methods and model options available for Bouncer through the Claude Agent SDK.

---

## 📋 Table of Contents

- [Authentication Methods](#authentication-methods)
  - [Anthropic API Key](#1-anthropic-api-key-recommended)
  - [AWS Bedrock](#2-aws-bedrock)
  - [Google Vertex AI](#3-google-vertex-ai)
  - [Microsoft Foundry](#4-microsoft-foundry)
  - [OAuth (Not Supported for Bouncer)](#5-oauth-not-supported-for-bouncer)
- [Model Selection](#model-selection)
- [Configuration Summary](#configuration-summary)

---

## 🔐 Authentication Methods

The Claude Agent SDK supports multiple authentication methods. Here’s how to configure each one for Bouncer.

### 1. **Anthropic API Key** (Recommended)

This is the simplest and most common method.

**How it works:**
- You use a standard Anthropic API key.
- Bouncer communicates directly with the Anthropic API.

**Setup:**

1.  **Get your API key** from the [Anthropic Console](https://console.anthropic.com/dashboard).
2.  **Set the environment variable** in your `.env` file:

    ```
    ANTHROPIC_API_KEY=your_api_key_here
    ```

**Pros:**
- ✅ Simple to set up
- ✅ Direct access to Anthropic models
- ✅ Full feature support

**Cons:**
- ❌ You are responsible for API key management

---

### 2. **AWS Bedrock**

Use Claude models through AWS Bedrock. This is a great option for teams already using AWS.

**How it works:**
- Bouncer uses your AWS credentials to invoke Claude models via the Bedrock API.
- Authentication is handled by the AWS SDK (IAM roles, profiles, etc.).

**Setup:**

1.  **Enable Claude access** in the [AWS Bedrock Console](https://aws.amazon.com/bedrock/).
2.  **Configure your AWS credentials**. The SDK will automatically detect them from:
    - IAM roles for EC2 instances
    - Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
    - Your AWS config file (`~/.aws/credentials`)

3.  **Set the Bedrock environment variable** in your `.env` file:

    ```
    # Use AWS Bedrock for authentication
    USE_BEDROCK=true
    
    # Optional: Specify your AWS region
    # AWS_REGION=us-east-1
    ```

**Pros:**
- ✅ Integrated with your AWS environment
- ✅ Centralized billing and management in AWS
- ✅ Enhanced security with IAM roles

**Cons:**
- ❌ Model availability and features may differ from the direct Anthropic API
- ❌ Requires AWS setup and configuration

---

### 3. **Google Vertex AI**

Use Claude models through Google Cloud's Vertex AI.

**How it works:**
- Bouncer uses your Google Cloud credentials to invoke Claude models via the Vertex AI API.
- Authentication is handled by the Google Cloud SDK.

**Setup:**

1.  **Enable Claude access** in the [Google Cloud Console](https://console.cloud.google.com/vertex-ai).
2.  **Configure your Google Cloud credentials**:
    - Use `gcloud auth application-default login`
    - Set up a service account

3.  **Set the Vertex AI environment variable** in your `.env` file:

    ```
    # Use Google Vertex AI for authentication
    USE_VERTEX=true
    
    # Specify your Google Cloud project and region
    # GOOGLE_CLOUD_PROJECT=your-gcp-project
    # GOOGLE_CLOUD_REGION=us-central1
    ```

**Pros:**
- ✅ Integrated with your Google Cloud environment
- ✅ Centralized billing and management in GCP

**Cons:**
- ❌ Model availability and features may differ

---

### 4. **Microsoft Foundry**

Use Claude models through Microsoft Azure.

**Setup:**

1.  **Enable Claude access** in the Azure portal.
2.  **Configure your Azure credentials**.
3.  **Set the Foundry environment variable** in your `.env` file:

    ```
    # Use Microsoft Foundry for authentication
    USE_FOUNDRY=true
    ```

---

### 5. **OAuth (Not Supported for Bouncer)**

The Claude Code CLI (which the SDK uses) supports OAuth for interactive use, but this method is **not suitable for a background service like Bouncer**.

**Why not?**
- OAuth requires a user to log in via a web browser.
- Bouncer runs as a non-interactive background process.
- API keys or cloud provider authentication are the correct methods for automated services.

---

## 🧠 Model Selection

You can specify which Claude model Bouncer should use.

**How it works:**

Set the `CLAUDE_MODEL` environment variable in your `.env` file. If not set, it defaults to the latest recommended model.

**Available Models:**

- `claude-3-opus-20240229` (Most powerful)
- `claude-3-sonnet-20240229` (Balanced)
- `claude-3-haiku-20240307` (Fastest)

**Example:**

```
# .env file

# Use Claude 3 Haiku for speed and cost-effectiveness
CLAUDE_MODEL=claude-3-haiku-20240307
```

**Recommendation:**
- For most Bouncer tasks, **Haiku** is an excellent choice. It's fast, affordable, and powerful enough for quality checks.
- For complex analysis (e.g., deep security reviews), consider using **Sonnet** or **Opus**.

---

## ⚙️ Configuration Summary

Here’s a summary of all the environment variables you can use in your `.env` file to configure authentication and model selection.

```
# --- Authentication --- 
# Choose ONE of the following methods

# Option 1: Anthropic API Key (Recommended)
ANTHROPIC_API_KEY=your_api_key_here

# Option 2: AWS Bedrock
# USE_BEDROCK=true
# AWS_REGION=us-east-1

# Option 3: Google Vertex AI
# USE_VERTEX=true
# GOOGLE_CLOUD_PROJECT=your-gcp-project
# GOOGLE_CLOUD_REGION=us-central1

# Option 4: Microsoft Foundry
# USE_FOUNDRY=true

# --- Model Selection --- 
# Optional: Defaults to the latest recommended model

# Use Haiku for speed and cost
CLAUDE_MODEL=claude-3-haiku-20240307

# Or use Sonnet for more power
# CLAUDE_MODEL=claude-3-sonnet-20240229

# Or use Opus for maximum power
# CLAUDE_MODEL=claude-3-opus-20240229

# --- Other Settings ---
SLACK_WEBHOOK_URL=your_slack_webhook_url
```

---

## 🔐 Security Best Practices

- **Never commit your `.env` file** to version control.
- Use a secrets management system (like AWS Secrets Manager, Google Secret Manager, or HashiCorp Vault) for production environments.
- When using AWS or GCP, prefer IAM roles or service accounts over long-lived access keys.

---

## 📚 Additional Resources

- [Deployment Guide](DEPLOYMENT.md)
- [Configuration Guide](../bouncer.yaml)
- [Anthropic API Documentation](https://docs.anthropic.com/)
-)
