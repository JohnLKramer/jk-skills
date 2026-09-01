---
name: jvm-structured-logging
description: >-
  Use when writing or editing a log call (log.info, log.warn, log.error,
  log.debug, logger.*) in Kotlin or Java with logstash-logback
  StructuredArguments on the classpath, including interpolating values into
  the message, SLF4J {}, or kv("exception", ...).
---

# JVM Structured Logging

Search finds a constant message string. Values live in StructuredArgument fields.

Applies only to the log call being written or edited. Neighboring interpolating lines stay.

## The rule

Message: string literal. No `$`, no `+`, no `{}`. For each value put in an ad-hoc map, name its camelCase property or local as it appears in source (`event.startDate` → `startDate`; `event.id` → `id`). Do not invent a compound name from the wrapper object. This does not require naming every field emitted by `toLogEntries()` / `toStructuredArguments()`.

Fields: values as StructuredArguments. Ad-hoc keys are snake_case (`startDate` → `start_date`, `startTrackingDate` → `start_tracking_date`, `id` → `id`). Values do not appear in the message.

```kotlin
log.info(
    "Event startDate is less than startTrackingDate skipping..",
    StructuredArguments.entries(
        mapOf(
            "start_date" to event.startDate,
            "start_tracking_date" to startTrackingDate,
        ),
    ),
)
```

## Attach fields

Use module `entries(...)` as the attachment mechanism when it exists. If a type already has `toLogEntries()` or `toStructuredArguments()`, use that content instead of an ad-hoc map; do not invent a type helper.

Without module `entries(...)`: one field uses `StructuredArguments.kv("start_date", event.startDate)`; multiple fields use `StructuredArguments.entries(mapOf(...))`.

## Throwables

Last argument is the Throwable. Not `kv("exception", e)` or `kv("exception", e.message)`. Structured fields go before it.

```kotlin
log.info(
    "Caught UnprocessableEntityException from MT Treating as a race between two reservation events",
    entries("sequence_no" to sequenceNo),
    e,
)
```

## Objects

Prefer `toLogEntries()` / `toStructuredArguments()`. Otherwise scalars (ids, status, amounts, dates). Not the whole object.

## Wrong

```kotlin
log.warn("Dropping event=$event because it is out of order.")
log.info("Skipping for ${event.idMetadataEntry}")
log.info("SpotBonus id ${id} threshold: $threshold", StructuredArguments.kv("spot_bonus_agreement_id", id))
logger.error("Error creating settlement", venuePayout.toLogEntries(), StructuredArguments.kv("exception", e))
```

## Excuses that still fail

- "The line doesn't read well without the value." Name the code identifier in the sentence; put the value in the map.
- "SLF4J `{}` is structured logging." Fields are StructuredArguments. Message stays constant.
- "I'm matching nearby interpolating logs." Only the call being written or edited changes.
- "It's just a debug line." Same rule at every level.
- "The code uses camelCase identifiers, so field keys should match." Field keys are snake_case even when code identifiers are camelCase.
- "The Throwable is last, so keeping an exception field preserves searchability." Pass it once, only as the last argument.
- "A compared value was only named in the old message, not interpolated." If the message describes a comparison, attach every compared value as a field, including object properties such as `event.startDate`.
- "A wrapper name makes a property clearer." Use the property or local as written in source: `event.id` is `id`.
