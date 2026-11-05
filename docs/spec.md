# Spec — Argus

## Problem

Operators with many GitHub repositories need silent, opinionated hygiene with clear human escalations — without embedding a coding agent in every product repo.

## Goals

- Discover portfolio changes (new / removed / parked / archived)
- Score attention deterministically from signals + `config/rubric.yaml`
- Auto-apply only `auto_safe` fixes (PR preference, dry-run default)
- Compose gated agent prompts (≤4 phases, every phase ends with `GATE:`)
- Notify only when human work or critical security remains
- Support third-party report-only scans

## Non-goals

- Living inside product repositories
- Replacing Dependabot/Renovate
- Force-push, history rewrite, or repository deletion
- LLMs in scoring or runbook composition

## Stack

Python 3.11+, Click CLI, YAML config, Jinja HTML, GitHub REST.

## Parent

Child of [agent-project-bootstrap](https://github.com/edwardlthompson/agent-project-bootstrap). See `docs/PARENT_GAP_LIST.md`.
