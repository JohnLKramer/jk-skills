# jk-skills

LLM skills that I have created.

Each skill is a directory holding a single `SKILL.md`: YAML frontmatter with a
`name` and a `description`, followed by the guidance itself. The `description`
is the trigger — it states the conditions under which an agent should load the
skill, so most harnesses can decide on their own when a skill is relevant.

The guidance is written for JVM services (Kotlin and Java) backed by Postgres,
with a bias toward review-time enforcement: each skill names the wrong shape,
the right shape, and the excuses that still fail.

## Skills

| Skill | Load it when | Core rule |
|-------|--------------|-----------|
| [honoring-declared-types](honoring-declared-types/SKILL.md) | Designing typed APIs, or reviewing code that downcasts, uses `as`, or recovers a narrower type from a parameter | If a function takes a supertype, every subtype must work. Keep subtype-specific work at the typed call site or make it polymorphic. |
| [jvm-structured-logging](jvm-structured-logging/SKILL.md) | Writing or editing a log call in a repo with logstash-logback `StructuredArguments` on the classpath | The message is a string literal. Values go in snake_case `StructuredArguments` fields, and a `Throwable` is the last argument. |
| [liquibase-postgres-migrations](liquibase-postgres-migrations/SKILL.md) | Writing Liquibase formatted SQL for Postgres, or debugging `Unterminated dollar quote` failures | Any changeset containing dollar quotes (`$$`, `$BODY$`) needs `splitStatements:false`. |
| [mock-behavior-not-data](mock-behavior-not-data/SKILL.md) | Introducing mocks in unit tests, or choosing between a real instance and a mock for a collaborator | Mock behavior you need to control. Construct values — DTOs, data classes, exceptions — with their real constructor or builder. |
| [one-reason-to-change](one-reason-to-change/SKILL.md) | Designing modules, or reviewing code that adds methods, dependencies, or logic to an existing class | A separate reason to change lives in a separate module. Call it from the cut site instead of embedding foreign logic. |
| [writing-code-comments](writing-code-comments/SKILL.md) | Writing or editing comments — inline, KDoc, Javadoc, SQL, or notes beside Liquibase SQL | A comment documents the code, not the change. Say why, and drop anything that only helps someone carrying the current ticket. |

## Using the skills

Clone once, then point your harness at the clone:

```bash
git clone git@github.com:JohnLKramer/jk-skills.git ~/src/jk-skills
```

Every harness below reads plain markdown, but each one discovers it differently.
Claude Code loads `SKILL.md` as-is; Cursor and GitHub Copilot need the same body
under a different frontmatter; Codex and Gemini CLI need a pointer from their
context file.

### Claude Code

Claude Code discovers skills from `~/.claude/skills/<name>/SKILL.md` (personal,
every project) or `.claude/skills/<name>/SKILL.md` (one project). Symlink so
`git pull` in the clone updates them:

```bash
mkdir -p ~/.claude/skills
for dir in ~/src/jk-skills/*/; do
  [ -f "$dir/SKILL.md" ] || continue
  ln -sfn "${dir%/}" ~/.claude/skills/"$(basename "${dir%/}")"
done
```

Restart Claude Code, then confirm with `/help` or by asking for a skill by name.
Claude reads each `description` and invokes the skill itself when the work
matches; you can also force one with `/jvm-structured-logging` or "use the
mock-behavior-not-data skill".

### Cursor

Cursor reads project rules from `.cursor/rules/*.mdc`. An `.mdc` file needs
`globs` and `alwaysApply` alongside the description, so convert rather than
copy. Run this from the repo you want the rules in:

```bash
mkdir -p .cursor/rules
for file in ~/src/jk-skills/*/SKILL.md; do
  name=$(basename "$(dirname "$file")")
  awk -v extra='globs: ["**/*.kt", "**/*.java", "**/*.sql"]\nalwaysApply: false' '
    NR == 1 && $0 == "---" { print; next }
    !seen && $0 == "---" { print extra; print; seen = 1; next }
    { print }
  ' "$file" > ".cursor/rules/$name.mdc"
done
```

`alwaysApply: false` plus a description makes each one an Agent Requested rule:
Cursor picks it up when the description matches the task. Narrow or widen the
`globs` to the languages in that repo. For rules you want everywhere, paste the
same files into Cursor's user rules instead. Cursor also reads a root
`AGENTS.md`, so the Codex layout below works there as a fallback.

### Codex

Codex has no skill loader; it reads `AGENTS.md` — `~/.codex/AGENTS.md` for every
session, or `AGENTS.md` at a repo root for that repo. Give it the trigger and
the path, and let it open the file when the trigger fires:

```markdown
## Skills

Before doing the matching work, read the skill file and follow it exactly.

- `~/src/jk-skills/jvm-structured-logging/SKILL.md` — writing or editing a log call in Kotlin or Java.
- `~/src/jk-skills/liquibase-postgres-migrations/SKILL.md` — writing Liquibase formatted SQL for Postgres.
- `~/src/jk-skills/mock-behavior-not-data/SKILL.md` — introducing mocks in a unit test.
- `~/src/jk-skills/one-reason-to-change/SKILL.md` — adding methods, dependencies, or logic to an existing class.
- `~/src/jk-skills/honoring-declared-types/SKILL.md` — designing a typed API, or reviewing a downcast.
- `~/src/jk-skills/writing-code-comments/SKILL.md` — writing or editing a comment.
```

Codex can only read paths it is allowed to reach. If the clone sits outside the
working directory and your sandbox blocks it, copy the skills into the repo (for
example `docs/skills/`) and use relative paths.

### Gemini CLI

Gemini CLI assembles context from `GEMINI.md` — `~/.gemini/GEMINI.md` globally,
or `GEMINI.md` at the project root — and `@` imports pull other markdown files
into that context:

```markdown
# Coding skills

@./skills/jvm-structured-logging/SKILL.md
@./skills/liquibase-postgres-migrations/SKILL.md
@./skills/mock-behavior-not-data/SKILL.md
@./skills/one-reason-to-change/SKILL.md
@./skills/honoring-declared-types/SKILL.md
@./skills/writing-code-comments/SKILL.md
```

Import paths resolve relative to the file that contains them, so keep the skills
beside `GEMINI.md`:

```bash
mkdir -p ~/.gemini/skills
for dir in ~/src/jk-skills/*/; do
  [ -f "$dir/SKILL.md" ] || continue
  cp -R "${dir%/}" ~/.gemini/skills/
done
```

Imports are unconditional — every imported skill is in context for every turn.
Import the two or three that fit the repo rather than all six, and use `/memory
show` to see what actually loaded.

### GitHub Copilot

Copilot reads `.github/copilot-instructions.md` for repo-wide guidance and
`.github/instructions/*.instructions.md` for path-specific guidance. The
path-specific form takes an `applyTo` glob, so convert the frontmatter:

```bash
mkdir -p .github/instructions
for file in ~/src/jk-skills/*/SKILL.md; do
  name=$(basename "$(dirname "$file")")
  awk -v extra='applyTo: "**/*.kt,**/*.java,**/*.sql"' '
    NR == 1 && $0 == "---" { print; next }
    !seen && $0 == "---" { print extra; print; seen = 1; next }
    { print }
  ' "$file" > ".github/instructions/$name.instructions.md"
done
```

Set `applyTo` per skill — `**/*.sql` for `liquibase-postgres-migrations`,
`**/*Test.kt` for `mock-behavior-not-data` — because Copilot applies an
instructions file whenever an edited file matches the glob, not when the
description matches the task. Copilot code review picks these up too, which is
where the review sections of each skill earn their keep.
