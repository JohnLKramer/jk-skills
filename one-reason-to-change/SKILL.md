---
name: one-reason-to-change
description: Use when designing modules, writing specs or implementation plans, implementing a cut that adds behavior, or reviewing code that adds methods, dependencies, or logic to an existing class, cites Single Responsibility Principle or SRP, scopes a cut by expanding an existing class such as this-cut-only, or says the class already has the context.
---

# One Reason to Change

Each module has one reason to change. Posting rules and compliance audit rules are not the same reason.

The Single Responsibility Principle: a separate reason lives in a separate module. Name the reason before adding code.

## Implementation rule

New-reason work goes in a module whose reason to change is that work. Call it from the cut site. Do not embed foreign logic in an existing class as a private helper or new dependencies.

YAGNI: skip audit alerting by not adding `PostingAuditAlerter` yet; do not express the skip as `recordPostingFailure` inside `ReservationPostingLogic`.

## Allowed shapes

- Collaborator call: `postingFailureAuditor.record(...)`
- Module that already owns that reason
- Tests and fixtures combining types for brevity

Same lie as embedding: private helper for a foreign concern; new foreign dependencies; plan that says add to `ExistingClass`; "it already has the context."

A new method or dependency for the class's existing reason is allowed. A second reason because the call site is nearby is not.

## Example

Wrong:

```kotlin
class ReservationPostingLogic(private val auditDao: AuditDao, private val clock: Clock) {
    private fun recordPostingFailure(...) { auditDao.insert(/* compliance fields */) }
}
```

Right:

```kotlin
class PostingFailureAuditor(private val auditDao: AuditDao, private val clock: Clock) {
    fun record(...) { /* ... */ }
}

class ReservationPostingLogic(private val auditor: PostingFailureAuditor) {
    fun postReservationPrice(...) { try { /* post */ } catch (e: Exception) { auditor.record(..., e); throw e } }
}
```

## Design and plans

Do not expand an existing class in plan example code to scope a cut. Name the matching module or omit foreign work. Non-goal: "audit alerting does not run on insert failure yet." Never encode embedding in `ReservationPostingLogic`. Implementers copy plans faithfully; do not copy plan-mandated embedding.

## Review

Foreign private helper or new foreign dependencies on an existing class: Important even when the plan specified them. Name the class, its existing reason, the new reason, and what policy will churn it next. Not Minor. Thin call to a module whose reason already matches is not a finding. The human may defer the fix. The review still calls the lie.

## Excuses that still fail

- "This cut only."
- "The plan specified it."
- "The class already has the context."
- "It's just one private helper."
- "A new service is over-engineering."
- "YAGNI means no new class."
- "Minimal surface area for shipping today."
- "Ready to merge with acknowledged debt."
- "No findings; ready to merge."

## Red flags

Stop and apply the implementation rule:

- Private helper for a foreign concern in plan or production code
- New foreign dependencies on a class whose reason did not include them
- Plan says add to the existing class instead of naming the right module
- Treating a plan-mandated expansion as a review pass
- "This cut only" or "already has the context" as the reason to embed
