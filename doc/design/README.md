# Design Documentation

This directory contains technical design specifications for Stock Pal features. Design documents describe **HOW** features will be built, including architecture, APIs, data models, and implementation details.

## Structure

```
design/
├── [active_design_docs].md    # Design documents for upcoming/current features
└── done/                       # Completed and implemented designs
    └── [completed_designs].md
```

## When to Create a Design Document

Create a design doc when:
- Building a new feature with significant complexity
- Making architectural changes
- Designing new APIs or data models
- Refactoring existing systems
- Implementing features that will affect multiple components

**Don't create design docs for:**
- Simple bug fixes
- Minor UI tweaks
- Configuration changes
- Trivial enhancements

## Design Document Structure

A good design document should include:

### 1. Overview
- **Purpose**: What problem does this solve?
- **Goals**: What are we trying to achieve?
- **Non-goals**: What's explicitly out of scope?

### 2. Background/Context
- Current state of the system
- Related features or systems
- Why this design is needed now

### 3. Proposed Solution

#### Architecture
- High-level architecture diagram
- Component interactions
- Data flow

#### API Design
- Endpoint specifications (for backend features)
- Request/response formats
- Error handling

#### Data Models
- Database schema changes
- Data structures
- Validation rules

#### Frontend Design (if applicable)
- Component structure
- State management
- UI/UX mockups or wireframes

### 4. Implementation Plan
- Phases or milestones
- Dependencies
- Timeline estimate

### 5. Testing Strategy
- Unit tests
- Integration tests
- Manual testing scenarios

### 6. Alternative Approaches
- Other solutions considered
- Why they were rejected

### 7. Open Questions
- Unresolved issues
- Items needing discussion

## Design Document Template

```markdown
# [Feature Name] - Design Document

## Overview

### Purpose
What problem does this solve?

### Goals
- Goal 1
- Goal 2

### Non-Goals
- Explicitly out of scope

## Background

Current state and context...

## Proposed Solution

### Architecture

[Diagram or description of system architecture]

### API Design

#### Endpoint: POST /api/v1/example
**Request:**
```json
{
  "param1": "value",
  "param2": 123
}
```

**Response:**
```json
{
  "result": "success",
  "data": {}
}
```

### Data Models

```python
class ExampleModel:
    field1: str
    field2: int
```

### Frontend Components

- ComponentA: Purpose
- ComponentB: Purpose

### Data Flow

1. User action
2. API call
3. Processing
4. Response

## Implementation Plan

### Phase 1: [Name]
- Task 1
- Task 2

### Phase 2: [Name]
- Task 3
- Task 4

## Testing Strategy

### Unit Tests
- Test case 1
- Test case 2

### Integration Tests
- Scenario 1
- Scenario 2

## Alternative Approaches

### Approach A
**Pros:** ...
**Cons:** ...
**Decision:** Rejected because...

## Open Questions

- [ ] Question 1?
- [ ] Question 2?

## References

- Related design doc: [link]
- External reference: [link]
```

## Workflow

### 1. Before Implementation

1. **Research**: Understand the problem and existing system
2. **Draft design**: Create initial design document
3. **Review**: Share with team for feedback
4. **Iterate**: Refine based on feedback
5. **Approve**: Get design approved before implementation

### 2. During Implementation

1. **Reference**: Use design doc as implementation guide
2. **Update**: If implementation differs from design, update the doc
3. **Document decisions**: Add notes about important decisions

### 3. After Implementation

1. **Final update**: Ensure doc reflects actual implementation
2. **Move to done**: Move completed design to `done/` folder
3. **Create summary**: Add completion summary to `/doc/development/done/`

## Best Practices

### Writing Good Designs

**Be specific, not vague:**
- ❌ "We'll use a database to store data"
- ✅ "We'll add a `backtest_results` table with columns: id, user_id, strategy_id, created_at, results_json"

**Include diagrams:**
- Architecture diagrams
- Data flow diagrams
- UI mockups
Use Mermaid for diagrams when possible

**Consider edge cases:**
- Error scenarios
- Performance implications
- Scalability concerns

**Link to related docs:**
- Reference backlog item that triggered this
- Link to related design docs
- Reference external resources

### Keeping Designs Current

**During implementation:**
- Update design if you discover better approaches
- Document why changes were made
- Keep API specs accurate

**After implementation:**
- Move to `done/` folder
- Add "Implementation Notes" section if implementation differs from original design
- Link to the completion summary in `/doc/development/done/`

### Design Review

Before finalizing a design:
1. Self-review against this checklist:
   - [ ] Clear goals and non-goals?
   - [ ] Architecture diagram included?
   - [ ] API specs are complete?
   - [ ] Data models defined?
   - [ ] Testing strategy outlined?
   - [ ] Alternative approaches considered?

2. Get feedback from:
   - Other developers
   - Product/stakeholders (for user-facing features)
   - DevOps (for deployment/infrastructure changes)

## Active Design Documents

Current design documents in this folder:

- [backtest_post_mvp_enhancements.md](backtest_post_mvp_enhancements.md) - Post-MVP backtest enhancements
- [risk_manager_detailed_design.md](risk_manager_detailed_design.md) - Risk manager backend design
- [risk_manager_frontend_design.md](risk_manager_frontend_design.md) - Risk manager frontend design

## Completed Designs (`done/`)

Designs that have been fully implemented:

- [backtest_engine_upgrade_design.md](done/backtest_engine_upgrade_design.md) - Backtest engine V2 upgrade
- [frontend_metrics_enhancement_design.md](done/frontend_metrics_enhancement_design.md) - Enhanced metrics display
- [multi_market_trading_rules_design.md](done/multi_market_trading_rules_design.md) - A-share trading rules

## Related Documentation

- **Backlog** (`/doc/backlog/`): Feature ideas that may need design docs
- **Development** (`/doc/development/`): Implementation progress and summaries
- **Requirements** (`/doc/requirements/`): Product-level specifications
- **API Docs** (`/doc/api/`): API usage documentation

## Common Design Patterns

### API Design Pattern
All Stock Pal APIs follow REST conventions:
- Use proper HTTP methods (GET, POST, PUT, DELETE)
- Return consistent JSON structure
- Include proper error handling
- Version APIs (`/api/v1/...`)

### Frontend Component Pattern
React components should:
- Be functional components with hooks
- Use TypeScript for type safety
- Follow single responsibility principle
- Use Ant Design components when possible

### Service Layer Pattern
Backend services should:
- Be stateless and testable
- Have clear single responsibilities
- Return pandas DataFrames for data processing
- Use type hints for parameters and returns

---

**Need help?** See the main documentation README at `/doc/README.md`
