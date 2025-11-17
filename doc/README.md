# Stock Pal Documentation

Welcome to the Stock Pal documentation repository. This directory contains all project documentation including requirements, design specs, development progress, and feature backlogs.

## Quick Start

**New to the project?** Start here:
1. [Product Requirements](requirements/product_requirements_stock_pal.md) - Understand what Stock Pal is
2. [Product Roadmap](requirements/product_roadmap.md) - See where we're headed
3. [DOC_INDEX.md](DOC_INDEX.md) - Browse all available documentation

**Looking for something specific?**
- Use [DOC_INDEX.md](DOC_INDEX.md) for a complete catalog of all documents
- Check [Recent Updates](DOC_INDEX.md#recent-updates-last-7-days) for latest changes

## Documentation Structure

```
doc/
├── api/                    # API usage guides and examples
├── backlog/                # Future feature ideas (prioritized backlog)
├── brainstorm/             # Exploratory analysis and research
├── design/                 # Feature design specifications
│   └── done/               # Completed and implemented designs
├── development/            # Development tracking and summaries
│   ├── done/               # Completed development work
│   └── progress/           # Active development tracking
├── plan/                   # Project planning and breakdown
├── requirements/           # Product requirements and roadmap
├── strategy/               # Trading strategy documentation
├── strategy_params/        # Strategy parameter specifications
├── DOC_INDEX.md            # Complete documentation index
└── README.md               # This file
```

## Document Categories Explained

### Requirements (`requirements/`)
Product-level specifications that define WHAT we're building and WHY.
- Product Requirements Document (PRD)
- Product roadmap and milestones
- Competitor analysis
- Market research

**When to read:** Understanding product vision, priorities, and market positioning

### Backlog (`backlog/`)
Future features and enhancements that are NOT yet in development. These are prioritized ideas waiting for implementation.
- Each backlog item describes a potential feature
- Items move from backlog → design → development as they're prioritized
- See [backlog/README.md](backlog/README.md) for categorization

**When to read:** Planning future work, brainstorming, roadmap discussions

### Design (`design/`)
Detailed technical specifications for features that are ready for (or in) implementation.
- Architecture decisions
- API specifications
- Data models and schemas
- UI/UX mockups and flows
- **Completed designs** are moved to `design/done/`

**When to read:** Before implementing a feature, during code review, architecture discussions

### Development (`development/`)
Progress tracking and completion summaries for development work.
- **`progress/`**: Active development tracking (work in progress)
- **`done/`**: Summaries of completed work (what was built, lessons learned)

**When to read:** Checking development status, reviewing completed work, onboarding

### Planning (`plan/`)
Project planning documents including feature prioritization and breakdown.
- Feature decomposition
- Sprint planning
- Resource allocation

**When to read:** Sprint planning, prioritization discussions

### Brainstorm (`brainstorm/`)
Exploratory documents including analysis, research, and feasibility studies.
- Market analysis
- Technical explorations
- Feasibility studies
- Not all ideas here will be implemented

**When to read:** Exploring new ideas, research phase

### Strategy & Strategy Params (`strategy/`, `strategy_params/`)
Documentation for trading strategies implemented in the system.
- **`strategy/`**: Strategy logic, signals, and behavior
- **`strategy_params/`**: Parameter specifications and tuning guidance

**When to read:** Understanding strategies, implementing new strategies, tuning parameters

### API (`api/`)
Usage guides and examples for APIs and modules.
- API endpoint documentation
- Code examples
- Integration guides

**When to read:** Using APIs, integration work

## Documentation Workflow

### Document Lifecycle

```
Idea/Research → Backlog → Design → Development (Progress) → Development (Done)
     ↓              ↓         ↓              ↓                      ↓
 brainstorm/    backlog/  design/    development/progress/  development/done/
                                            ↓                      ↓
                                     design/done/           (feature shipped)
```

### How Documents Move Through the System

1. **Exploration Phase**: Ideas start in `brainstorm/` or directly in `backlog/`
2. **Backlog**: Feature ideas are documented in `backlog/` with priority
3. **Design Phase**: When prioritized, detailed design docs are created in `design/`
4. **Development Phase**: Implementation begins, tracked in `development/progress/`
5. **Completion**: When done:
   - Design docs move to `design/done/`
   - Progress docs are summarized and moved to `development/done/`

## Documentation Best Practices

### Creating New Documents

1. **Choose the right category**:
   - Requirements: Product-level decisions
   - Backlog: Future feature ideas
   - Design: Technical specifications
   - Development: Implementation tracking

2. **Follow naming conventions**:
   - Use lowercase with underscores: `risk_manager_design.md`
   - Be descriptive: `backtest_engine_upgrade_design.md` not `engine.md`
   - Include context: `risk_manager_frontend_design.md` vs `risk_manager_backend_design.md`

3. **Document structure**:
   ```markdown
   # [Feature Name]

   ## Overview
   Brief description (2-3 sentences)

   ## [Category-specific sections]
   - For design docs: Goals, Architecture, API, Data Models, etc.
   - For backlog: Problem, Solution, Value, Priority
   - For progress: Status, Completed, In Progress, Blockers
   ```

4. **Update the index**: After creating a document, update [DOC_INDEX.md](DOC_INDEX.md)

### Maintaining Documents

1. **Keep documents current**: Update design docs if implementation differs
2. **Move completed work**: Move done designs and progress to respective `done/` folders
3. **Archive outdated docs**: If a document becomes obsolete, move to an `archive/` folder or delete
4. **Link between documents**: Reference related docs with relative links

### Document Handoff

When moving documents between stages:
- **Backlog → Design**: Reference the backlog doc in the design doc
- **Design → Development**: Link the design doc in the progress tracker
- **Progress → Done**: Summarize what was implemented vs. designed

## Finding Information

### Use the Index
[DOC_INDEX.md](DOC_INDEX.md) provides:
- Complete document catalog organized by category
- Recent updates (last 7 days)
- Quick navigation by topic
- Document status indicators

### Search Tips
1. Use your editor's search across files (e.g., `grep -r "keyword" doc/`)
2. Check [DOC_INDEX.md](DOC_INDEX.md) first for high-level overview
3. Look in category folders based on what you need:
   - Understanding product: `requirements/`
   - Implementing feature: `design/`
   - Checking progress: `development/progress/`
   - Planning future: `backlog/`

### Common Scenarios

**"I want to understand what Stock Pal does"**
→ Start with [requirements/product_requirements_stock_pal.md](requirements/product_requirements_stock_pal.md)

**"I'm implementing a new feature"**
→ Check if there's a design doc in `design/`, if not create one

**"I want to see what's being built now"**
→ Look in `development/progress/`

**"I want to propose a new feature"**
→ Create a document in `backlog/` and update the backlog README

**"I need to understand a trading strategy"**
→ Check `strategy/` for logic, `strategy_params/` for parameters

**"What's planned for the future?"**
→ See [requirements/product_roadmap.md](requirements/product_roadmap.md) and `backlog/`

## Documentation Standards

### File Format
- All documentation in Markdown (`.md`)
- Use proper Markdown syntax for readability
- Include code blocks with language tags: ```python

### Language
- Primary language: English for code/API docs, Chinese acceptable for requirements/analysis
- Be clear and concise
- Use technical terms consistently

### Linking
- Use relative links between documents: `[text](../other/doc.md)`
- Link to code with absolute paths from repo root: `/backend/app/services/data_service.py`

### Diagrams
- Use Mermaid for diagrams when possible
- Include alt text for accessibility
- Keep diagrams simple and focused

### Version Control
- Commit documentation with related code changes when applicable
- Write clear commit messages for doc-only changes
- Tag major documentation milestones

## Contributing

### Before Writing
1. Check if similar documentation exists
2. Choose the appropriate category
3. Follow naming conventions
4. Review existing docs in that category for format/style

### While Writing
1. Write for your audience (developers, product managers, stakeholders)
2. Include examples and diagrams
3. Link to related documents
4. Keep it concise but complete

### After Writing
1. Update [DOC_INDEX.md](DOC_INDEX.md)
2. Link from related documents
3. Notify relevant team members
4. Commit with clear message

## Questions or Issues?

- **Missing documentation?** Create an issue or document it yourself
- **Outdated information?** Update the doc and note changes
- **Can't find something?** Check [DOC_INDEX.md](DOC_INDEX.md) or search the repo
- **Documentation feedback?** Suggest improvements via issues or pull requests

## Document Index

For a complete, searchable index of all documentation, see **[DOC_INDEX.md](DOC_INDEX.md)**.

---

Last updated: 2025-11-14
