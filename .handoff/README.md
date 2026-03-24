# PM ↔ Dev Handoff Directory

This directory is the communication bridge between PM and Dev agents.

## Workflow

### PM → Dev (需求下发)
1. PM writes requirements to `pm-to-dev.md`
2. Dev reads `pm-to-dev.md` and implements

### Dev → PM (进度反馈)  
1. Dev writes status/questions to `dev-to-pm.md`
2. PM reads `dev-to-pm.md` and responds

### Shared Documents
- `PRD.md` - Product Requirements Document (PM maintains)
- `TECH_SPEC.md` - Technical Specification (Dev maintains)
- `DECISIONS.md` - Architecture/product decisions log (both append)
- `STATUS.md` - Current sprint status (Dev updates, PM reviews)

## Convention
- Always append timestamps when writing
- Use `## [YYYY-MM-DD HH:MM] Title` format for entries
- Mark items as `[PENDING]`, `[IN_PROGRESS]`, `[DONE]`, `[BLOCKED]`
