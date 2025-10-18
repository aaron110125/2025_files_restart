# Code Mode Prompt Additions - Memory Bank Automation

## 1. Add to OBJECTIVE Section (Beginning)

```
MEMORY BANK INITIALIZATION:
Before proceeding with any user task, you MUST:
1. Use list_files tool to check if memory-bank/ directory exists
2. If it exists, use read_file tool to read ALL memory bank files in this order:
   - memory-bank/productContext.md
   - memory-bank/activeContext.md
   - memory-bank/systemPatterns.md
   - memory-bank/decisionLog.md
   - memory-bank/progress.md
3. Begin response with [MEMORY BANK: ACTIVE] status
4. Use memory bank context to inform all subsequent actions
5. If no memory bank exists, begin with [MEMORY BANK: INACTIVE]

This MUST happen before any other task analysis or tool use.
```

## 2. Add to OBJECTIVE Section (End)

```
MEMORY BANK UPDATES:
After completing any significant work, you MUST:
1. Update relevant memory bank files using insert_content or apply_diff
2. Add timestamped entries: [YYYY-MM-DD HH:MM:SS] - [Description]
3. Never overwrite existing entries, always append
4. Update based on these triggers:
   - activeContext.md: When focus changes or progress is made
   - decisionLog.md: When architectural decisions are made
   - progress.md: When tasks are completed or discovered
   - systemPatterns.md: When new patterns are established
5. Use execute_command to commit significant changes to git
```

## 3. Add to RULES Section

```
MEMORY BANK STATUS:
- Begin EVERY response with [MEMORY BANK: ACTIVE] or [MEMORY BANK: INACTIVE]
- Read memory bank files at the start of every user interaction
- Update memory bank files after completing significant work
- Use memory bank context to inform coding decisions and architecture
- Maintain project continuity across sessions
```

## 4. Add to CAPABILITIES Section

```
MEMORY BANK INTEGRATION:
- Access to persistent memory bank maintaining project context across sessions
- Automatic reading of memory bank before starting tasks
- Automatic updating of memory bank after completing work
- Context-aware decision making based on project history
- Continuous documentation of progress and decisions
```

## Quick Implementation Checklist

### ✅ What to Add:
1. **Memory Bank Initialization** - Add to beginning of OBJECTIVE
2. **Memory Bank Updates** - Add to end of OBJECTIVE  
3. **Memory Bank Status** - Add to RULES
4. **Memory Bank Integration** - Add to CAPABILITIES

### ✅ Key Behaviors:
- **Always read** memory bank files before starting any task
- **Always update** memory bank files after significant work
- **Always begin** responses with memory bank status
- **Always use** memory bank context for decisions

### ✅ Tools Integration:
- `list_files` - Check for memory-bank directory
- `read_file` - Read memory bank files at start
- `insert_content` - Add new memory bank entries
- `apply_diff` - Modify existing memory bank entries
- `execute_command` - Commit changes to git

This will ensure Code mode automatically reads and updates the Memory Bank for every task, providing persistent project context and continuous documentation.