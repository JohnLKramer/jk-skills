---
name: honoring-declared-types
description: Use when designing typed APIs, writing specs or implementation plans, implementing functions that take a supertype or interface, or reviewing code that downcasts, uses `as`, recovers a narrower type from a parameter, cites Liskov, or scopes a cut with a subtype cast such as this-cut-only.
---

# Honoring Declared Types

The declared type is the contract. If a function takes `PrimaryPayable`, every `PrimaryPayable` must work.

That is the Liskov Substitution Principle: a subtype must be usable anywhere the base type is declared, without the callee inspecting or narrowing the runtime type. For agents: the declared type must be true.

## Implementation rule

Subtype-specific work stays at the typed call site, or it becomes polymorphic: a member on the declared type, or a sealed exhaustive `when` on the parameter.

YAGNI: skip playlist locking by calling `lockReservationId` from `processReservationPriceEvent`, which already takes `ReservationPriceEvent`. Do not write `(event as ReservationPriceEvent)` in the shared method.

## Allowed recoveries

- Tests, fixture type known
- Trust boundaries: JSON, JDBC, Java `Any` / `Object`
- Sealed exhaustive `when` on the parameter

Same lie as `as`: `as` on a production parameter; `as?` whose else skips, returns, or throws; `is` plus smart cast; `require(x is T)`; `when` with `else throw`; "playlist is a non-goal" as the reason.

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

Lock identity on `PrimaryPayable` is also right when the work is truly shared. Not required for a reservation-only cut.

## Design and plans

Do not downcast in spec or plan example code to scope a cut. Call from the typed entry, add to the declared type, or keep it out of the shared method. Write "playlist posting does not take this lock yet," not `(event as ReservationPriceEvent)`.

## Implementation

Do not copy a plan-mandated downcast. Move the call, make it polymorphic, or keep the parameter as the type you need.

## Review

A parameter downcast is Important even when the plan specified it. Name the declared type, the recovered type, and which future subtype breaks. Not Minor. Sealed exhaustive `when`, test casts, and trust-boundary casts are not findings. The human may defer the product fix. The review still calls the lie.

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
