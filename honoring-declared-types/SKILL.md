---
name: honoring-declared-types
description: Use when designing typed APIs, writing specs or implementation plans, implementing functions that take a supertype or interface, or reviewing code that downcasts, uses `as`, recovers a narrower type from a parameter, cites Liskov, or scopes a cut with a subtype cast such as this-cut-only.
---

# Honoring Declared Types

Declared types are contracts. Every `PrimaryPayable` must work.

The Liskov Substitution Principle requires every subtype to work without runtime narrowing: the declared type must be true.

## Implementation rule

Subtype-specific work stays at the typed call site, or it becomes polymorphic: a member on the declared type, or a sealed exhaustive `when` on the parameter.

YAGNI: skip playlist locking by calling `lockReservationId` from `processReservationPriceEvent`; do not write `(event as ReservationPriceEvent)` in the shared method.

## Allowed recoveries

- Tests, fixture type known
- Trust boundaries: JSON, JDBC, Java `Any` / `Object`
- Sealed exhaustive `when` on the parameter

Equivalent lies: `as` on a production parameter; `as?` whose else skips, returns, or throws; smart casts; `require(x is T)`; `when` with `else throw`; "playlist is a non-goal" as a reason.

`as?` with else that handles every other subtype matches sealed exhaustive `when`. A silent skip does not.

## Example

Wrong:

```kotlin
fun processPrimaryPayableInTransaction(event: PrimaryPayable): PayableTrack? {
    lockDao.lockReservationId((event as ReservationPriceEvent).reservationId)
}
```

Right:

```kotlin
fun processReservationPriceEvent(event: ReservationPriceEvent): PayableTrack? {
    lockDao.lockReservationId(event.reservationId)
    return processPrimaryPayableInTransaction(event)
}
```

`PrimaryPayable` lock identity also works when truly shared; not needed for a reservation-only cut.

## Design and plans

Do not downcast in spec or plan example code to scope a cut. Call from the typed entry, add to the declared type, or keep it out of the shared method.

When a cut skips a subtype, its non-goal MUST state what that subtype does not do yet: for example, "playlist posting does not take this lock yet" or "playlist posting does not call `lockPlaylistEventId`." "Leave X unchanged" is not explicit enough. Never encode a downcast.

## Implementation

Do not copy a plan-mandated downcast. Move the call, make it polymorphic, or keep the parameter as the type you need.

## Review

A parameter downcast is Important even when the plan specified it. Name the declared type, the recovered type, and a concrete future subtype that breaks (for example, `PlaylistReservationEvent`), not just a vague future implementation. Not Minor. Sealed exhaustive `when`, test casts, and trust-boundary casts are not findings. The human may defer the product fix. The review still calls the lie.

## Excuses that still fail

- "This cut only."
- "The plan specified it."
- "Playlist does not call this yet."
- "I'll add a `when` with else throw."
- "`is` plus smart cast is type-safe."
- "Nearby code already casts."
- "Reviewer said Important, plan-mandated, skip."
- "Preserves the reusable API without inventing lock identity."
- "Transaction scope requires the lock in the shared method."
- "Deferred playlist locking is not a blocker."
- "No findings; ready to merge."

## Red flags

Stop and apply the implementation rule:

- `as ConcreteType` in spec or plan example code
- Downcasting a production parameter
- `is` plus smart cast on a production parameter
- `when` with else throw
- Treating a plan-mandated downcast as a review pass
- "This cut only" or "playlist does not call this yet" as the reason for a cast
