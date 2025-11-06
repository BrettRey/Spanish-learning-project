# PR Title (Follow Conventional Commits: feat:, fix:, docs:, chore:, refactor:)

## Summary
One sentence on what changed and why.

## Motivation / Context
- What problem does this solve?
- User impact?
- Pedagogy alignment (Four Strands/CEFR)?

## Changes

- [ ] **DB/schema**: {none | details + migration steps}
- [ ] **APIs**: {none | list new/changed functions}
- [ ] **Content**: {e.g., +10 B1 nodes, 2 new constructions}
- [ ] **Tooling**: {Makefile targets, pre-commit, CI}
- [ ] **Documentation**: {README, STATUS, other docs updated}

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| _Example: Data loss during migration_ | _Automatic backup before migration_ |

## Tests / Evidence

**Tests added/updated**:
- {List test files or describe test coverage}

**Local validation**:
```bash
make test              # All tests pass
make kg-server         # Smoke test for KG server (if applicable)
```

**CI status**: {GitHub Actions link or manual validation notes}

## Rollout / Ops

**Deployment steps** (if applicable):
1. Pull latest changes
2. Run migrations: `python state/migrations/migrate.py`
3. Rebuild KG: `python kg/build.py kg/seed kg.sqlite` (if KG changed)
4. Test with: `./LLanguageMe` or `make test`

**Backout plan**:
- Revert commit: `git revert <commit>`
- Restore database: `cp state/mastery.sqlite.backup state/mastery.sqlite`

**Breaking changes?**: {yes/no - describe if yes}

## Checklist

Before requesting review, ensure:

- [ ] Title follows conventional commits format
- [ ] README updated if user-facing behavior changed
- [ ] CHANGELOG.md entry added
- [ ] Tests added/updated; `make test` passes locally
- [ ] CI green (or manual testing documented)
- [ ] Data sources/license notes updated (if new data added)
- [ ] No secrets in code or history
- [ ] Documentation updated (STATUS.md, relevant docs)
- [ ] Migration files included (if schema changed)
- [ ] Backward compatibility maintained (or breaking change noted)

## Related Issues

Closes #[issue number]

Addresses recommendations from: {link to document/review if applicable}

---

**Branch**: `[branch-name]`
**Base**: `main`
**Status**: 🔄 In Review / ✅ Ready to Merge
