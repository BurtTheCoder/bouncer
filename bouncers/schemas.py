"""
Shared schemas for structured outputs across all bouncers
"""

# Standard bouncer output schema
BOUNCER_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["clean", "issues_found", "fixed", "denied"],
            "description": "Overall status of the check"
        },
        "issues": {
            "type": "array",
            "description": "List of issues found",
            "items": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category of the issue (e.g., 'syntax', 'security', 'style')"
                    },
                    "type": {
                        "type": "string",
                        "description": "Specific type of issue"
                    },
                    "message": {
                        "type": "string",
                        "description": "Human-readable description of the issue"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["info", "warning", "high", "critical"],
                        "description": "Severity level of the issue"
                    },
                    "line": {
                        "type": "integer",
                        "description": "Line number where the issue occurs (if applicable)"
                    },
                    "suggestion": {
                        "type": "string",
                        "description": "Suggested fix for the issue"
                    }
                },
                "required": ["category", "type", "message", "severity"]
            }
        },
        "fixes": {
            "type": "array",
            "description": "List of fixes applied (only if auto_fix is enabled)",
            "items": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category of the fix"
                    },
                    "action": {
                        "type": "string",
                        "description": "Action taken (e.g., 'added_field', 'fixed_formatting')"
                    },
                    "message": {
                        "type": "string",
                        "description": "Description of what was fixed"
                    },
                    "before": {
                        "type": "string",
                        "description": "State before the fix (optional)"
                    },
                    "after": {
                        "type": "string",
                        "description": "State after the fix (optional)"
                    }
                },
                "required": ["category", "action", "message"]
            }
        },
        "suggestions": {
            "type": "object",
            "description": "Smart suggestions for improvement (bouncer-specific)",
            "additionalProperties": True
        },
        "messages": {
            "type": "array",
            "description": "Summary messages",
            "items": {
                "type": "string"
            }
        },
        "metadata": {
            "type": "object",
            "description": "Additional metadata (bouncer-specific)",
            "additionalProperties": True
        }
    },
    "required": ["status", "issues", "fixes", "messages"]
}


def get_bouncer_schema(bouncer_type: str = "standard") -> dict:
    """
    Get the structured output schema for a specific bouncer type
    
    Args:
        bouncer_type: Type of bouncer (standard, obsidian, security, etc.)
    
    Returns:
        Schema dictionary for structured output
    """
    base_schema = BOUNCER_OUTPUT_SCHEMA.copy()
    
    # Customize schema based on bouncer type
    if bouncer_type == "obsidian":
        base_schema["properties"]["suggestions"] = {
            "type": "object",
            "properties": {
                "connections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "target": {"type": "string"},
                            "reason": {"type": "string"}
                        }
                    }
                },
                "tag_consolidation": {
                    "type": "object",
                    "properties": {
                        "found_tags": {"type": "array", "items": {"type": "string"}},
                        "recommended": {"type": "string"}
                    }
                }
            }
        }
    
    elif bouncer_type == "security":
        base_schema["properties"]["metadata"] = {
            "type": "object",
            "properties": {
                "cve_ids": {"type": "array", "items": {"type": "string"}},
                "risk_score": {"type": "number"},
                "affected_lines": {"type": "array", "items": {"type": "integer"}}
            }
        }
    
    elif bouncer_type == "performance":
        base_schema["properties"]["metadata"] = {
            "type": "object",
            "properties": {
                "complexity_score": {"type": "number"},
                "file_size_bytes": {"type": "integer"},
                "estimated_impact": {"type": "string"}
            }
        }
    
    return base_schema
