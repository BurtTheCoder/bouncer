# Creating Custom Bouncers

This guide provides a step-by-step walkthrough for creating your own custom bouncers to extend Bouncer's capabilities. With a modular, plugin-based architecture, you can easily add new checks for any file type or quality criteria.

## 🎯 Why Create a Custom Bouncer?

- **Domain-Specific Logic**: Check for quality criteria unique to your industry (e.g., legal documents, scientific data, financial reports).
- **Proprietary File Formats**: Analyze custom file formats specific to your tools or workflow.
- **New Technologies**: Add support for new languages, frameworks, or technologies not covered by the built-in bouncers.
- **Custom Workflows**: Enforce team-specific conventions, project standards, or unique quality checks.

## 🏗️ Bouncer Architecture

Bouncer is designed to be extensible:

1.  **Orchestrator**: The core engine that watches for file changes.
2.  **Bouncers**: Specialized agents that check files for specific quality criteria.
3.  **Notifiers**: Send results to different channels (Slack, Discord, etc.).

When you create a new bouncer, you're creating a new specialized agent that the orchestrator can use.

## 🚀 Quick Start: 5 Steps to Create a Bouncer

### Step 1: Copy the Template

Copy the `bouncers/template.py` file and rename it to reflect your new bouncer's purpose.

```bash
cp bouncers/template.py bouncers/jupyter_bouncer.py
```

### Step 2: Customize Your Bouncer Class

Open your new file (`bouncers/jupyter_bouncer.py`) and customize it:

1.  **Rename the class**: `CustomBouncer` -> `JupyterBouncer`
2.  **Update the docstring**: Describe what your bouncer does.
3.  **Add custom configuration**: In `__init__`, add any new configuration options you need from `bouncer.yaml`.
4.  **Define file types**: In `__init__`, set the `file_types` your bouncer should check (e.g., `[".ipynb"]`).

```python
# bouncers/jupyter_bouncer.py

class JupyterBouncer:
    """Checks Jupyter notebooks for quality and best practices"""
    
    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get("enabled", False)
        self.file_types = config.get("file_types", [".ipynb"])
        self.auto_fix = config.get("auto_fix", False)
        
        # Custom config
        self.max_cells = config.get("max_cells", 50)
        self.clear_outputs = config.get("clear_outputs", True)
```

### Step 3: Write Your System & User Prompts

This is the most important step! You need to tell Claude how to act as your specialized bouncer.

-   **`_build_system_prompt()`**: Define the bouncer's role, expertise, and goals.
-   **`_build_user_prompt()`**: Provide the file context and specific instructions for the check.

```python
# In JupyterBouncer

def _build_system_prompt(self) -> str:
    return """You are a Jupyter Bouncer - an expert in data science and notebook best practices.

Your job:
1. Read the Jupyter notebook (.ipynb) file
2. Check for reproducibility, clarity, and performance
3. Fix issues automatically when safe (e.g., clear outputs)
4. Ensure notebooks are clean and easy to review
"""

def _build_user_prompt(self, file_path: Path, event_type: str) -> str:
    return f"""File changed: {file_path.name}

Please review this Jupyter notebook.

Configuration:
- Auto-fix enabled: {self.auto_fix}
- Clear outputs on save: {self.clear_outputs}
- Max cells: {self.max_cells}

Check for:
1. Missing markdown documentation
2. Unused imports and variables
3. Large cell outputs that bloat the file
4. Cell execution order issues
5. Reproducibility problems (e.g., missing random seeds)

Provide a report of issues, fixes, and suggestions in the structured JSON format.
"""
```

### Step 4: Add to `bouncer.yaml`

Add a new section for your bouncer in `bouncer.yaml` so you can configure it:

```yaml
# bouncer.yaml

bouncers:
  # ... (other bouncers)
  
  # Jupyter Bouncer
  jupyter:
    enabled: true
    file_types:
      - .ipynb
    auto_fix: true
    max_cells: 50
    clear_outputs: true
```

### Step 5: Register Your Bouncer

Finally, add your new bouncer to `bouncers/__init__.py` so the orchestrator can find it:

```python
# bouncers/__init__.py

# ... (other imports)
from .jupyter_bouncer import JupyterBouncer

BOUNCERS = {
    "code_quality": CodeQualityBouncer,
    "security": SecurityBouncer,
    # ... (other bouncers)
    "jupyter": JupyterBouncer,  # Add your bouncer here
}
```

That's it! Bouncer will now automatically use your new Jupyter Bouncer for `.ipynb` files.

## 🤖 Prompt Engineering Best Practices

-   **Be specific**: Clearly define the bouncer's role and what it should check for.
-   **Use structured instructions**: Numbered lists and clear headings help the agent understand.
-   **Provide context**: Tell the agent about the file type, event, and configuration.
-   **Leverage `auto_fix`**: Use conditional instructions based on whether `auto_fix` is enabled.
-   **Use `structured_output`**: Rely on the `BOUNCER_OUTPUT_SCHEMA` to get clean, predictable JSON responses.

## 🔧 Advanced Customization

### Custom Tools

If you need to run external tools (e.g., a linter, a compiler), you can create custom tools and add them to the `allowed_tools` in your bouncer's `check` method.

See `checks/tools.py` for examples.

### Custom Logic

Your bouncer is just a Python class - you can add any custom logic you need:

-   Read other files for context
-   Connect to databases or APIs
-   Perform complex calculations
-   Use third-party libraries

### Bouncer Result Schema

Your bouncer **must** return a dictionary that conforms to the `BOUNCER_OUTPUT_SCHEMA` defined in `bouncers/schemas.py`. This ensures that the orchestrator and notifiers can understand the results.

## 🤝 Contributing Your Bouncer

If you create a bouncer that could be useful to others, please consider contributing it back to the project!

1.  **Fork the repository** on GitHub.
2.  **Create a new branch** for your bouncer.
3.  **Add your bouncer** and any related documentation.
4.  **Submit a pull request**.

We welcome contributions of all kinds!

## 📚 See Also

-   [Bouncer Template](template.py) - The starting point for your custom bouncer.
-   [Bouncer Schemas](schemas.py) - The structured output schema.
-   [Existing Bouncers](.) - See how the built-in bouncers are implemented.
