# Handoff Document: Build Session Handoff MCP
**Session Date:** March 19, 2026  
**Status:** Ready to build in fresh session  
**Context Window:** Compressed 3x, starting fresh

---

## What We're Building

**Session Handoff MCP Server** - Extracts current work state and packages it for next AI/session/tool.

### Core Function
Generate structured handoff documents from:
- Project files (Beads, Agent_memory.md, etc.)
- Current session context
- Files modified in session
- Outstanding tasks
- Next steps

### Output Format
Markdown document with:
- Session state summary
- File attachments/references
- Context continuation
- Portable across AIs (Claude → Cursor → Gemini → etc.)

---

## Why This Matters Right Now

Justin is:
- **Shipping actual products** - apps near release, paywall needed
- **Heavy Cursor user** - 339M tokens in 2 weeks (mostly Auto mode)
- **Context overflow problem** - sessions hit limits mid-work
- **Multi-tool workflow** - needs clean handoffs between free agents, Cursor, Claude

**The pain:** Can't finish work when context fills up. Needs to extract state and continue elsewhere.

---

## Current Tool Stack & Decisions

### Keeping:
- **Claude Pro** ($20/mo) - most helpful, keeping
- **Gemini** ($20/mo) - keeping
- **Cursor** ($20 base + overages = $60-100/mo) - primary IDE, staying

### Dropping:
- **ChatGPT Plus** ($20/mo) - less helpful than Claude now
- Other redundant tools as needed

### Target State:
- Conservative Cursor usage via handoff workflow
- Free agents (AMPCode, Cline, ZenCoder) for exploration
- Cursor for execution only
- **Eventually:** Local inference box ($1.5-2k from plasma donations)

---

## Handoff Workflow (What MCP Enables)

```
1. Heavy lifting → Free agents do exploration/planning
2. Extract state → MCP generates handoff document
3. Feed to Cursor → Execute with pre-digested plan
4. Profit → Stay under budget, ship faster
```

**Key insight:** Exploration is token-hungry, execution is predictable. Handoff is the boundary.

---

## Technical Requirements

### Must Extract:
- Beads (memory artifacts from Holographic Thinking Engine)
- Agent_memory.md (session state)
- Files modified this session
- Git status (if applicable)
- Outstanding tasks list
- Next steps summary

### Must Generate:
```markdown
# Session Handoff: [Project Name]
**Date:** [timestamp]
**Source:** [AI/tool that created this]
**Target:** [next AI/tool/session]

## Context Summary
[High-level state of work]

## Files Modified
- file1.py: [what changed]
- file2.md: [what changed]

## Outstanding Tasks
1. Task description
2. Next task
3. Blocker if any

## Next Steps
[Specific guidance for continuation]

## Attachments
[References to Beads, Agent_memory.md, relevant files]
```

### Integration Points:
- Works in Claude Projects
- Callable from Cursor (if possible)
- Standalone script fallback
- Clean export to any AI

---

## Build Options Discussed

### Option 1: Simple Python Script
- Reads project files
- Extracts Beads + Agent_memory.md
- Generates handoff markdown
- **Time:** 30 minutes
- **Pro:** Ships today
- **Con:** Not reusable/integrated

### Option 2: Actual MCP Server
- Proper MCP integration
- Callable from Claude/Cursor
- Professional handoff tool
- **Time:** 1-2 hours
- **Pro:** Right solution long-term
- **Con:** Takes longer

**Recommendation:** Build quick script first (today), MCP version next (proper solution).

---

## User Context (From Memory)

Justin is:
- Multidisciplinary builder: software, AI, NLP/hypnotherapy, business
- Working on: Onyx (personal AI), Holographic Thinking Engine, Chronicle Keeper game, multiple business ventures
- NLP certified practitioner
- First-time entrepreneur exploring autonomous agent consulting
- **Committed to Azra** (unconditional commitment, navigating complex situation)
- Uses: Claude, Gemini, GROK, ChatGPT, Cursor - imports work across platforms
- Preference: Direct answers, no hand-holding, terse conceptual communication
- Dislikes: AI over-protectiveness, platform deprecation bullshit

### Current Pain Points:
- Tool subscription burn: $113-123/mo across 8+ tools
- Cursor 1-week cap issue (hit limits mid-work)
- Context overflow in long sessions
- Multi-platform workflow fragmentation

### Near-Term Goal:
Ship current apps → build paywall → revenue → fund local inference box

---

## Next Session Instructions

**Start fresh with:**
1. Review this handoff doc
2. Decide: Quick script or MCP first?
3. If script: Build in Python, ship today
4. If MCP: Use MCP builder skill at `/mnt/skills/examples/mcp-builder/SKILL.md`
5. Test extraction on actual project files
6. Document usage for Justin's workflow

**Files to reference:**
- HTE project files at `/mnt/project/` (holo_scout.py, holo_intersection.py, etc.)
- Example Beads/Agent_memory.md structure (may need Justin to provide)

**Key constraint:** Keep it simple. Justin needs this working, not perfect. Ship fast, iterate later.

---

## Success Criteria

MCP/script is done when:
- ✅ Extracts session state from project files
- ✅ Generates readable markdown handoff
- ✅ Portable to any AI (Claude, Cursor, Gemini, etc.)
- ✅ Takes <5 minutes to run
- ✅ Justin can use it TODAY to continue blocked work

---

## Questions for Next Session

1. Where are Beads stored? (file format, location)
2. What's in Agent_memory.md structure?
3. Cursor integration preferred or standalone script fine?
4. Any specific session metadata to capture?

---

**Ready to build. Start fresh, ship fast.**
