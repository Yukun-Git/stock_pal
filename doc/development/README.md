# Development Documentation

This directory tracks all development work for the Stock Pal project, organized into two categories:

## Structure

```
development/
├── progress/    # Active development tracking (work in progress)
└── done/        # Completed development summaries
```

## Progress (`progress/`)

Documents in this folder track **active development work**. These are living documents that get updated as work progresses.

**What goes here:**
- Development status updates
- Implementation progress tracking
- Current blockers and issues
- Next steps and TODOs

**Format:**
Each progress document should include:
- Current status (% complete or phase)
- Completed work
- In-progress work
- Remaining work
- Blockers/issues
- Timeline updates

**When to update:**
- At key milestones (phase completion, major feature done)
- When status changes significantly
- When blockers are identified or resolved
- At least weekly for active projects

**Examples:**
- `backtest_engine_upgrade_progress.md` - Multi-phase upgrade tracking
- `strategy-documentation-feature.md` - Feature implementation progress

## Done (`done/`)

Documents in this folder are **completion summaries** of finished development work.

**What goes here:**
- Summary of what was built
- How it differs from original design (if applicable)
- Implementation decisions and rationale
- Lessons learned
- Performance metrics (if applicable)
- Next steps or follow-up work needed

**When to create:**
When development work is completed, create a summary document here. The corresponding progress document can be either:
- Moved to `done/` (if it's detailed enough)
- Summarized and then archived
- Kept in `progress/` if work continues in phases

**Format:**
```markdown
# [Feature Name] - Development Summary

## Overview
Brief description of what was built

## What Was Implemented
- Feature A
- Feature B
- ...

## Key Decisions
- Decision 1: Why we chose X over Y
- Decision 2: Implementation approach

## Challenges & Solutions
- Challenge: Description
  - Solution: How we solved it

## Metrics
- Performance data
- Test coverage
- Any relevant measurements

## Lessons Learned
- What went well
- What could be improved
- Recommendations for future work

## Follow-up Work
- Known issues
- Future enhancements
- Technical debt to address
```

**Examples:**
- `backend_refactoring_summary.md` - Backend refactoring completion
- `frontend_refactoring_summary.md` - Frontend refactoring completion
- `risk_manager_frontend_complete_summary.md` - Risk manager feature completion

## Workflow

### Starting New Development

1. Check if there's a design document in `/doc/design/`
2. Create a progress tracker in `progress/` if the work will take multiple sessions
3. Update progress regularly as you work

### During Development

1. Update the progress document at key milestones
2. Document decisions and blockers
3. Link to relevant PRs and commits
4. Keep the status current

### Completing Development

1. Create a completion summary in `done/`
2. Move the progress doc to `done/` OR archive it
3. Update the design document if implementation differs
4. Move the design doc to `/doc/design/done/` if fully implemented

## Best Practices

### Progress Documents

- **Be specific**: Include concrete details, not just "working on it"
- **Update regularly**: Stale progress docs are worse than none
- **Track blockers**: Document what's blocking progress
- **Link to code**: Reference PRs, commits, branches
- **Estimate timeline**: Give realistic completion estimates

### Completion Summaries

- **Document decisions**: Explain why you made key choices
- **Include metrics**: Performance, test coverage, etc.
- **Be honest**: Note what didn't go as planned
- **Think forward**: What follow-up work is needed?
- **Share learnings**: Help future developers

### When to Create vs. Update

**Create a new progress doc when:**
- Starting a multi-day/multi-week feature
- Working on something with multiple phases
- Need to track complex dependencies

**Just use commit messages when:**
- Small bug fixes
- Minor enhancements
- Single-session work

**Create a completion summary when:**
- Major feature completed
- Significant refactoring done
- Complex implementation with learnings to share
- Work that others will build upon

## Templates

### Progress Document Template

```markdown
# [Feature Name] - Development Progress

## Overview
Brief description of what's being built

## Status
Current phase: [Design/Implementation/Testing/Complete]
Progress: [X%] or [Phase N of M]
Target completion: [Date]

## Completed
- [x] Task 1
- [x] Task 2

## In Progress
- [ ] Task 3 (50% - working on X)
- [ ] Task 4 (starting next)

## Remaining
- [ ] Task 5
- [ ] Task 6

## Blockers
- None / Blocker description

## Next Steps
1. Complete task 3
2. Start task 4
3. ...

## Notes
Any relevant notes, decisions, or updates
```

### Completion Summary Template

See format in "Done" section above.

## Related Documentation

- **Design documents**: `/doc/design/` - Technical specifications
- **Backlog**: `/doc/backlog/` - Future work not yet started
- **Requirements**: `/doc/requirements/` - Product-level specs
- **Planning**: `/doc/plan/` - Feature breakdown and prioritization

---

**Need help?** See the main documentation README at `/doc/README.md`
