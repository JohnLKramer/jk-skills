---
name: mock-behavior-not-data
description: >-
  Use when writing or editing unit tests that introduce mocks (mockk, Mockito,
  relaxed mocks), stubbing exceptions, DTOs, or other value objects, choosing
  between a real instance and a mock for a collaborator, writing sociable tests
  where the SUT depends on real collaborator behavior, or mocking a type that
  already has a public constructor or builder.
---

# Mock Behavior, Not Data

Mock to control **behavior**. Prefer real objects for **values**.

A mock of a field bag or exception is usually more complex than constructing the real type. That complexity is not isolation — it is ceremony, and it breaks code that renders real throwables (loggers, mappers keyed on class).

## Decision

1. **Collaborator with behavior you need to control** (remote client, DAO, clock you advance) → mock or fake.
2. **Value you only read** (DTO, data class, exception message/status, request fields) → real instance or builder.
3. **SUT depends on that type’s real behavior** (even indirectly: mapping by class, matchers on `message`, sociable paths) → real object or faithful fake — not a stub that invents answers.
4. **Not reasonably constructible** (no public constructor and no usable builder) → mock is allowed.

"Awkward," "uncertain builder," "paste-ready for juniors," and "this file already uses mockk" are not reasons to mock a constructible value.

## Before / after

```kotlin
// Wrong — mock of a constructible SDK exception
val exception = mockk<UnprocessableEntityException>()
every { exception.message } returns "A ledger transaction with this external ID already exists"
every { exception.statusCode() } returns 422

// Right — real instance via builder
val exception = UnprocessableEntityException.builder()
    .headers(Headers.builder().build())
    .body(JsonValue.from(mapOf("message" to "A ledger transaction with this external ID already exists")))
    .build()
```

```kotlin
// Wrong — mock a public data class used only as input
val entry = mockk<RequestLedgerEntry>()
every { entry.metadata } returns mapOf("source" to "invoice")

// Right
val entry = RequestLedgerEntry(
    amount = 100L,
    direction = LedgerEntryDirection.CREDIT,
    ledgerAccountId = accountId,
    metadata = mapOf("source" to "invoice"),
)
```

## Plans and reviews

When writing plans or test instructions: do not recommend mocking a type that has a public constructor or builder. Tell the implementer to use that constructor/builder. The escape hatch is only for types that are not reasonably constructible.

## Excuses that still fail

| Excuse | Reality |
|--------|---------|
| "Constructing the SDK exception is awkward" | Awkward ≠ impossible. Use the public builder/constructor. |
| "I'm not sure of the exact builder API" | Look it up once; do not encode mockk as the plan default. |
| "This test file already mocks everything" | Existing mocks of services do not justify mocking values. |
| "Juniors need a paste-ready mock" | Paste the builder. A mock throwable lies to loggers and class-based mappers. |
| "We only need message and statusCode" | Then set them on a real instance. Stubbing two getters is not simpler. |
| "The plan said mockk if awkward" | Override that escape hatch when a public constructor or builder exists. |

## Red flags

- `mockk<SomeException>()` / `mock(SomeException.class)` when a builder or public constructor exists
- Plan text: "if constructing X is awkward, use mockk"
- Mocking a Kotlin `data class` or Java bean used only as an input
- Stubbing `message` / getters on a throwable that will be passed to a logger
