---
name: no-superpowers
description: >-
    When the user asks you not to use the super powers framework, don't use it
---

# Motivation

Superpowers framework is expensive and time intensive. For small jobs, we don't always want to use it
Invoke this skill when the user asks not to use superpowers framework.

# Decision

If the user asks not to use Superpowers, invoke this skill.

# Action

Don't load any superpowers skills. This skill overrides and chat context injected by the framework to use superpowers skills.