# Skill Registry — MELI Manager

Generated: 2026-06-04
Source: user skills at `~/.config/opencode/skills/`

## Contract

This registry is an index — it maps trigger descriptions to skill paths. Each
subagent reads the exact `SKILL.md` at the given path for full instructions.
Do not treat this as a summary or compiler.

## Indexed Skills (11)

| # | Skill | Trigger / Description | Scope | Path |
|---|-------|----------------------|-------|------|
| 1 | `branch-pr` | Create Gentle AI pull requests with issue-first checks. Trigger: creating, opening, or preparing PRs for review. | user | `~/.config/opencode/skills/branch-pr/SKILL.md` |
| 2 | `chained-pr` | Trigger: PRs over 400 lines, stacked PRs, review slices. Split oversized changes into chained PRs that protect review focus. | user | `~/.config/opencode/skills/chained-pr/SKILL.md` |
| 3 | `cognitive-doc-design` | Design docs that reduce cognitive load. Trigger: writing guides, READMEs, RFCs, onboarding, architecture, or review-facing docs. | user | `~/.config/opencode/skills/cognitive-doc-design/SKILL.md` |
| 4 | `comment-writer` | Write warm, direct collaboration comments. Trigger: PR feedback, issue replies, reviews, Slack messages, or GitHub comments. | user | `~/.config/opencode/skills/comment-writer/SKILL.md` |
| 5 | `customize-opencode` | Use ONLY when the user is editing or creating opencode's own configuration: opencode.json, opencode.jsonc, files under .opencode/, or files under ~/.config/opencode/. Also use when creating or fixing opencode agents, subagents, skills, plugins, MCP servers, or permission rules. Do not use for the user's own application code, or for any project that is not configuring opencode itself. | user | `~/.config/opencode/skills/customize-opencode/SKILL.md` |
| 6 | `go-testing` | Trigger: Go tests, go test coverage, Bubbletea teatest, golden files. Apply focused Go testing patterns. | user | `~/.config/opencode/skills/go-testing/SKILL.md` |
| 7 | `issue-creation` | Create Gentle AI issues with issue-first checks. Trigger: creating GitHub issues, bug reports, or feature requests. | user | `~/.config/opencode/skills/issue-creation/SKILL.md` |
| 8 | `judgment-day` | Trigger: judgment day, dual review, adversarial review, juzgar. Run blind dual review, fix confirmed issues, then re-judge. | user | `~/.config/opencode/skills/judgment-day/SKILL.md` |
| 9 | `skill-creator` | Trigger: new skills, agent instructions, documenting AI usage patterns. Create LLM-first skills with valid frontmatter. | user | `~/.config/opencode/skills/skill-creator/SKILL.md` |
| 10 | `skill-improver` | Trigger: improve skills, audit skills, refactor skills, skill quality. Audit and upgrade existing LLM-first skills. | user | `~/.config/opencode/skills/skill-improver/SKILL.md` |
| 11 | `work-unit-commits` | Plan commits as reviewable work units. Trigger: implementation, commit splitting, chained PRs, or keeping tests and docs with code. | user | `~/.config/opencode/skills/work-unit-commits/SKILL.md` |

## Convention Files Scanned

None found (no AGENTS.md, CLAUDE.md, .cursorrules, or GEMINI.md in project).

## Skipped

- `sdd-*` skills (9): sdd-apply, sdd-archive, sdd-design, sdd-explore, sdd-init, sdd-onboard, sdd-propose, sdd-spec, sdd-tasks, sdd-verify
- `_shared` (support library)
- `skill-registry` (self)
- Duplicates: none

## Project Skills

None found under project skill directories.
