---
name: liquibase-postgres-migrations
description: >-
  Use when writing or editing Liquibase formatted SQL migrations for Postgres,
  especially changesets with DO $$ blocks, CREATE FUNCTION, plpgsql, dollar
  quotes, or when seeing "Unterminated dollar quote" / statement-splitting
  migration failures.
---

# Liquibase Postgres migrations

## Overview

Liquibase formatted SQL splits on `;` by default. Postgres dollar-quoted bodies (`$$` / `$BODY$`) contain internal semicolons, so a changeset that defines a function or `DO` block must disable statement splitting.

## Rule

On any changeset whose SQL contains dollar quotes (`$$`, `$tag$`, `$BODY$`, etc.):

```sql
--changeset author:id splitStatements:false
```

Also use `splitStatements:false` when a single changeset intentionally runs multiple statements that must not be split incorrectly (repo precedent: trigger + function in one changeset).

## Examples

**Wrong** (fails with `Unterminated dollar quote started at position … in SQL DO $$`):

```sql
--changeset jkramer:20260820114000:1
DO $$
BEGIN
  RAISE EXCEPTION 'nope';
END $$;
```

**Right:**

```sql
--changeset jkramer:20260820114000:1 splitStatements:false
DO $$
BEGIN
  RAISE EXCEPTION 'nope';
END $$;
```

**Function body** (same flag):

```sql
--changeset payapi:70 splitStatements:false
CREATE OR REPLACE FUNCTION modified_on_update_trigger()
  RETURNS TRIGGER AS
$BODY$
BEGIN
  NEW.modified_on = NOW();
  RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql;
```

Plain DDL without dollar quotes (`CREATE TABLE`, `CREATE INDEX`, `ALTER TABLE`) does **not** need the flag.

## Alternatives

- `endDelimiter:@` (or another delimiter) is valid but rarer in this codebase; prefer `splitStatements:false` for plpgsql/`DO` blocks.
- Prefer simple DDL over `DO $$` guards when empty-table / no-data assumptions already hold.

## Checklist

Before finishing a migration with functions/`DO`:

- [ ] Changeset line includes `splitStatements:false`
- [ ] Dollar-quoted body is complete (`$$` / `$BODY$` pairs match)
- [ ] No unnecessary `DO $$` when a normal statement suffices
