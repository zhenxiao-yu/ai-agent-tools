# AI Agent Instructions

This is a web app project.

## Rules

- Make small, reviewable changes.
- Prefer fixing validation errors before adding new features.
- Do not modify secrets, .env files, tokens, auth config, payment config, production deployment config, or database migrations.
- Do not touch node_modules, dist, build, .next, coverage, .git, cache folders, or generated files.
- Do not push to main.
- Work on AI branches only.
- Stop after one small task.

## Workflow

1. Inspect package.json.
2. Identify framework and scripts.
3. Run validation commands.
4. Fix one issue at a time.
5. Re-run validation.
6. Write a report.

## Preferred commands

- npm run lint
- npm run typecheck
- npm run build
- npm run test
- npx playwright test

## Good unattended tasks

- Fix TypeScript errors
- Fix lint errors
- Improve one component
- Add one test
- Improve accessibility
- Improve error handling
- Improve README

## Human approval required

- Auth changes
- Payment changes
- Database migrations
- Framework upgrades
- Dependency upgrades
- Large rewrites
- Deployment config changes
