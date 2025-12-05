# 🧠 Obsidian Bouncer

The **Obsidian Bouncer** is a specialized bouncer for [Obsidian](https://obsidian.md) markdown notes and knowledge bases. It helps maintain a healthy, well-connected Personal Knowledge Management (PKM) system.

---

## 🎯 What It Checks

### 1. **Wikilinks & Connections** 🔗

- **Broken wikilinks**: Detects `[[links]]` to non-existent notes
- **Orphaned notes**: Finds notes with no incoming or outgoing links
- **Circular dependencies**: Identifies problematic link cycles
- **Connection suggestions**: Recommends related notes to link

**Example Issues:**
```markdown
❌ [[Non-existent Note]] - broken link
❌ Note with zero connections - orphaned
✅ [[Existing Note]] - valid link
```

---

### 2. **Frontmatter Validation** 📋

Ensures YAML frontmatter is valid and complete.

**Required Fields** (configurable):
```yaml
---
tags: [knowledge-management, pkm]
created: 2024-12-05
status: active
---
```

**Checks:**
- Valid YAML syntax
- Required fields present
- Date format validation
- Consistent metadata schema

---

### 3. **Tag Management** 🏷️

Maintains consistent, organized tagging.

**Tag Format Options:**
- `kebab-case`: `#machine-learning`
- `camelCase`: `#machineLearning`
- `snake_case`: `#machine_learning`

**Checks:**
- Tag format consistency
- Duplicate/similar tags (`#todo` vs `#TODO`)
- Tag hierarchy validation (`#project/work/client`)
- Maximum tags per note
- Orphaned tags

---

### 4. **Content Quality** ✍️

Ensures notes are valuable and well-structured.

**Checks:**
- Minimum note length (default: 50 characters)
- Empty or stub notes
- Proper heading hierarchy (H1 → H2 → H3)
- Markdown syntax validity
- Code block language tags

---

### 5. **Obsidian-Specific Syntax** 🔮

Validates Obsidian's unique markdown extensions.

**Embeds & Transclusions:**
```markdown
![[Other Note]]  # Embed entire note
![[Other Note#Section]]  # Embed specific section
```

**Block References:**
```markdown
Some important text ^block-id

[[Note#^block-id]]  # Reference that block
```

**Callouts:**
```markdown
> [!note] Title
> Content here

> [!warning]
> Be careful!
```

**Dataview Queries** (if plugin installed):
```dataview
TABLE file.ctime as Created
FROM #project
SORT file.ctime DESC
```

---

### 6. **Knowledge Graph Health** 🕸️

Analyzes the overall structure of your knowledge base.

**Checks:**
- Isolated note clusters
- Over-connected hub notes (>50 links)
- Bidirectional linking
- MOC (Map of Content) recommendations

**Smart Suggestions:**
- "This note mentions 'Python' 5 times - link to [[Python MOC]]?"
- "Found 10 notes about machine learning - consider creating an ML MOC"

---

### 7. **Daily Notes & Templates** 📅

Ensures consistency in daily notes and templates.

**Checks:**
- Daily note naming convention
- Template usage consistency
- Required sections present
- Periodic note structure

---

### 8. **Attachments & Media** 🖼️

Manages attachments and media files.

**Checks:**
- Unused attachments
- Broken image links
- Large media files
- Attachment folder organization

---

## 🔧 Configuration

Add to your `bouncer.yaml`:

```yaml
bouncers:
  obsidian:
    enabled: true
    file_types:
      - .md
    auto_fix: true
    
    # Frontmatter settings
    required_fields:
      - tags
      - created
      - status
    
    # Tag settings
    tag_format: kebab-case  # kebab-case, camelCase, snake_case
    max_tags: 10
    
    # Link settings
    check_broken_links: true
    suggest_connections: true
    min_connections: 1  # Warn about isolated notes
    
    # Content settings
    min_note_length: 50  # characters
    require_headings: true
    
    # Vault structure
    attachment_folder: attachments
    template_folder: templates
    daily_notes_folder: daily
```

---

## 🎨 Use Cases

### Personal Knowledge Base
Monitor your Zettelkasten or personal wiki for broken links and orphaned notes.

### Team Documentation
Ensure team wikis maintain consistent formatting and complete metadata.

### Research Notes
Keep academic notes well-organized with proper citations and connections.

### Project Management
Maintain project documentation with consistent templates and tags.

---

## 🚀 Auto-Fix Capabilities

When `auto_fix: true`, Obsidian Bouncer can:

✅ Fix broken wikilinks (suggest alternatives)  
✅ Add missing frontmatter fields  
✅ Standardize tag formats  
✅ Create stub notes for missing links  
✅ Fix markdown syntax errors  
✅ Add missing heading hierarchies  
✅ Organize attachments into proper folders  

---

## 📊 Vault Health Report

Obsidian Bouncer provides insights into your knowledge base:

```
📊 Vault Health Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Notes: 342
Total Links: 1,247
Total Tags: 89
Orphaned Notes: 12 (3.5%)
Most Connected: [[Machine Learning MOC]] (47 links)
Average Connections: 3.6 per note
Tag Distribution: #project (89), #idea (67), #reference (45)
```

---

## 🧩 Integration with Obsidian Plugins

### Dataview
Validates Dataview query syntax and suggests optimizations.

### Templater
Checks Templater syntax and template consistency.

### Excalidraw
Validates embedded Excalidraw drawings.

### Kanban
Checks Kanban board structure and task formatting.

---

## 💡 Tips & Best Practices

### 1. Start with Warnings Only
```yaml
auto_fix: false  # Review issues first
```

### 2. Gradually Increase Standards
```yaml
min_note_length: 20  # Start low
# Later increase to 50, 100, etc.
```

### 3. Customize for Your Workflow
```yaml
required_fields:
  - tags
  - created
  # Add your own: author, project, status, etc.
```

### 4. Use with Git
Bouncer works great with version-controlled vaults:
```bash
# Watch your Obsidian vault
bouncer start --watch ~/Documents/ObsidianVault
```

---

## 🎯 Example Notifications

### Slack Notification
```
🧠 Obsidian Bouncer Report

📝 Note: Machine Learning Basics.md
Status: ⚠️ Issues Found

Issues:
• Missing frontmatter field: created
• Broken wikilink: [[Deep Learning]]
• Only 1 connection (min: 3)
• Tag format inconsistent: #ML vs #machine-learning

Suggestions:
• Link to [[Machine Learning MOC]]
• Consider adding: [[Neural Networks]], [[Supervised Learning]]

Auto-fixes applied:
✅ Standardized tags to kebab-case
✅ Added missing frontmatter template
```

---

## 🤝 Contributing

Have ideas for Obsidian-specific checks? Open an issue or PR!

**Potential additions:**
- Canvas file validation
- Plugin compatibility checks
- Vault backup verification
- Note aging analysis
- Reading time estimates

---

## 📚 Resources

- [Obsidian Documentation](https://help.obsidian.md/)
- [Linking Your Thinking](https://www.linkingyourthinking.com/)
- [Zettelkasten Method](https://zettelkasten.de/)
- [Building a Second Brain](https://www.buildingasecondbrain.com/)

---

**Happy note-taking!** 🧠✨
