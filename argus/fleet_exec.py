"""Fleet execute / wave batching (upgrade-wave rails)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from argus.action_ledger import append_action, brief_ledger_dir, write_brief_receipt
from argus.fleet import is_halted, load_actions, load_fleet_config
from argus.paths import ensure_runtime_dirs


def wave_batches(repos: list[str], caps: dict[str, Any] | None = None) -> list[list[str]]:
    caps = caps or (load_fleet_config().get("caps") or {})
    canary = max(1, int(caps.get("canary_size") or 1))
    after = max(0, int(caps.get("batch_after_canary") or 3))
    size = max(1, int(caps.get("batch_size") or 5))
    items = list(repos)
    out: list[list[str]] = []
    if not items:
        return out
    out.append(items[:canary])
    rest = items[canary:]
    if after and rest:
        out.append(rest[:after])
        rest = rest[after:]
    while rest:
        out.append(rest[:size])
        rest = rest[size:]
    return out


def execute_plan(
    brief_id: str,
    *,
    approve: bool = False,
    dist_dir: Path | None = None,
    root: Path | None = None,
    client: Any | None = None,
    wait_checks: bool = True,
) -> dict[str, Any]:
    from argus.fleet import halt
    from argus.fleet_apply import apply_wave, pr_checks_green
    from argus.rules_sync import block_mutations

    ensure_runtime_dirs()
    if is_halted(root):
        return {"status": "halted", "brief_id": brief_id}
    if block_mutations(root):
        return {"status": "RULES-STALE", "brief_id": brief_id}
    cfg = load_fleet_config()
    plan_path = brief_ledger_dir(brief_id, dist_dir=dist_dir) / "plan.json"
    if not plan_path.is_file():
        return {"status": "missing_plan", "brief_id": brief_id}
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if not (plan.get("verify") or "").strip():
        return {"status": "verify_required", "brief_id": brief_id}
    waves = wave_batches(list(plan.get("repos") or []), cfg.get("caps") or {})
    if not (approve and cfg.get("enabled")):
        result = {
            "status": "dry_run",
            "brief_id": brief_id,
            "verify": plan.get("verify"),
            "waves": [{"repos": w, "ok": True} for w in waves],
            "auto": bool(plan.get("auto")),
        }
        write_brief_receipt(brief_id, {"kind": "execute", **result}, dist_dir=dist_dir)
        return result

    if client is None:
        return {"status": "client_required", "brief_id": brief_id}

    wave_results: list[dict[str, Any]] = []
    for i, wave in enumerate(waves):
        if is_halted(root):
            wave_results.append({"repos": wave, "ok": False, "status": "halted"})
            break
        applied = apply_wave(client, wave, brief_id=brief_id, root=root)
        entry: dict[str, Any] = {
            "repos": wave,
            "opened": applied.opened,
            "skipped": applied.skipped,
            "errors": applied.errors,
            "digest": applied.digest,
            "ok": not applied.errors,
        }
        if applied.errors:
            wave_results.append(entry)
            break
        if wait_checks and applied.opened and i == 0:
            # Canary: require green (or no checks) before later waves
            for item in applied.opened:
                url = item.split(":", 1)[-1] if "http" in item else ""
                if not url.startswith("http"):
                    continue
                check = pr_checks_green(client, url)
                if check is False:
                    halt(f"canary checks red: {url}", root=root)
                    entry["ok"] = False
                    entry["status"] = "canary_red"
                    wave_results.append(entry)
                    result = {
                        "status": "halted_canary",
                        "brief_id": brief_id,
                        "waves": wave_results,
                    }
                    write_brief_receipt(brief_id, {"kind": "execute", **result}, dist_dir=dist_dir)
                    return result
                entry["canary_check"] = "green" if check else "pending_or_none"
        wave_results.append(entry)

    result = {
        "status": "executed",
        "brief_id": brief_id,
        "verify": plan.get("verify"),
        "waves": wave_results,
        "auto": bool(plan.get("auto")),
    }
    write_brief_receipt(brief_id, {"kind": "execute", **result}, dist_dir=dist_dir)
    append_action(
        actor="fleet",
        repo="-",
        action="execute",
        detail=brief_id,
        brief_id=brief_id,
        verify_result=result["status"],
        dist_dir=dist_dir,
    )
    return result


def drift_report(brief_id: str, *, dist_dir: Path | None = None) -> dict[str, Any]:
    d = brief_ledger_dir(brief_id, dist_dir=dist_dir)
    plan = d / "plan.json"
    if not plan.is_file():
        return {"brief_id": brief_id, "drift": True, "reason": "no_plan"}
    actions = [r for r in load_actions(dist_dir) if r.get("brief_id") == brief_id]
    return {
        "brief_id": brief_id,
        "drift": len(actions) == 0,
        "action_count": len(actions),
        "plan": json.loads(plan.read_text(encoding="utf-8")),
    }
