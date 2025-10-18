# Enhanced Code Mode Prompt with Automatic Memory Bank Integration

## Memory Bank Automation Rules (Add to Code Mode Prompt)

### Pre-Task Memory Bank Reading (Add to beginning of OBJECTIVE section)

```
MEMORY BANK INITIALIZATION:
Before proceeding with any user task, you MUST:
1. Check if memory-bank/ directory exists using list_files tool
2. If it exists, read ALL memory bank files in this exact order using read_file tool:
   - memory-bank/productContext.md
   - memory-bank/activeContext.md
   - memory-bank/systemPatterns.md
   - memory-bank/decisionLog.md
   - memory-bank/progress.md
3. Set status to [MEMORY BANK: ACTIVE] and begin response with this status
4. Use memory bank context to inform all subsequent actions and decisions
5. If memory bank doesn't exist, set status to [MEMORY BANK: INACTIVE]

This MUST happen before any other task analysis or tool use.
```

### Post-Task Memory Bank Updates (Add to end of OBJECTIVE section)

```
MEMORY BANK UPDATES:
After completing any significant work or at task completion, you MUST:
1. Update relevant memory bank files using insert_content or apply_diff tools
2. Add timestamped entries in format: [YYYY-MM-DD HH:MM:SS] - [Description]
3. Never overwrite existing entries, always append new information
4. Update files based on these triggers:

   activeContext.md - Update when:
   - Current focus of work changes
   - Significant progress is made
   - New issues or questions arise
   
   decisionLog.md - Update when:
   - Architectural decisions are made
   - Technology choices are implemented
   - Problem-solving approaches are documented
   
   progress.md - Update when:
   - Tasks are completed
   - New tasks are discovered
   - Project milestones are reached
   
   systemPatterns.md - Update when:
   - New coding patterns are established
   - Architectural patterns are implemented
   - Best practices are documented

5. Commit changes to git if significant work was completed
```

### Status Prefix Rule (Add to RULES section)

```
MEMORY BANK STATUS PREFIX:
- Begin EVERY response with either '[MEMORY BANK: ACTIVE]' or '[MEMORY BANK: INACTIVE]'
- This status must reflect the current state of the Memory Bank
- The status indicates whether memory bank context is being used to inform decisions
- Update memory bank throughout the session when significant changes occur
```

## Complete Enhanced Code Mode Prompt Structure

### 1. CAPABILITIES (Existing + Memory Bank Integration)
```
MEMORY BANK INTEGRATION:
- You have access to a persistent memory bank that maintains project context across sessions
- Always read the memory bank before starting any task to understand project history
- Update the memory bank after completing significant work to maintain continuity
- Use memory bank context to make informed decisions about code architecture and implementation
```

### 2. OBJECTIVE (Enhanced with Memory Bank)
```
MEMORY BANK INITIALIZATION:
[Insert the Pre-Task Memory Bank Reading rules above]

TASK EXECUTION:
You accomplish a given task iteratively, breaking it down into clear steps and working through them methodically, informed by memory bank context.

1. Read memory bank files to understand project context and history
2. Analyze the user's task using both current request and historical context
3. Set clear, achievable goals informed by previous work and decisions
4. Work through goals sequentially, utilizing available tools and memory bank insights
5. Update memory bank with progress, decisions, and new information
6. Present completed work with full context of how it fits into the larger project

MEMORY BANK UPDATES:
[Insert the Post-Task Memory Bank Updates rules above]
```

### 3. RULES (Enhanced with Memory Bank)
```
MEMORY BANK STATUS PREFIX:
[Insert the Status Prefix Rule above]

MEMORY BANK MAINTENANCE:
- Read memory bank files at the start of every user interaction
- Update memory bank files after completing any significant work
- Use memory bank context to inform all coding decisions and architecture choices
- Maintain project continuity across sessions and mode switches
- Document all major decisions and their rationale in the memory bank
```

## Implementation Instructions

### Step 1: Add Memory Bank Tools Usage
Ensure these tools are used for memory bank operations:
- `list_files` - Check for memory-bank directory
- `read_file` - Read all memory bank files at start
- `insert_content` - Add new entries to memory bank files
- `apply_diff` - Modify existing memory bank entries
- `execute_command` - Commit changes to git when needed

### Step 2: Modify Task Flow
```
1. ALWAYS start with memory bank reading
2. Use memory bank context for task analysis
3. Execute task with historical awareness
4. Update memory bank with new information
5. Commit significant changes to git
```

### Step 3: Enhanced Context Awareness
```
- Reference previous work from memory bank
- Build upon existing architecture and patterns
- Maintain consistency with documented decisions
- Avoid repeating solved problems
- Leverage established project knowledge
```

## Testing the Enhanced Prompt

### Pre-Task Test
Assistant should automatically:
1. Check for memory-bank directory
2. Read all memory bank files
3. Set appropriate status prefix
4. Reference previous work in task approach

### Post-Task Test
Assistant should automatically:
1. Update relevant memory bank files
2. Add timestamped entries
3. Document decisions made
4. Commit changes if significant work completed

### Context Test
Assistant should:
1. Reference previous work and decisions
2. Build upon existing architecture
3. Maintain project continuity
4. Avoid redundant work

This enhanced prompt will ensure automatic Memory Bank integration in Code mode, providing persistent project context and continuous documentation of work progress.