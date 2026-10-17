#!/usr/bin/python
# -*- coding: utf-8 -*-
# Standard library only, so it runs unchanged inside any AAP execution environment.
 
from __future__ import absolute_import, division, print_function
 
__metaclass__ = type
 
DOCUMENTATION = r"""
---
module: health_metrics
short_description: Compute automation health metrics from AAP job history and ServiceNow tasks
description:
  - Pure computation, no network access. Feed it job runs (AAP /jobs/ results) and optionally
    ServiceNow task records, and it returns per-template and overall health metrics.
options:
  jobs:
    description:
      - List of job dicts with name, status, finished (ISO 8601) and elapsed (seconds).
      - Failure reason is taken from failure_reason, then job_explanation.
    type: list
    elements: dict
    required: true
  tickets:
    description: List of dicts with automation (template name) and assignment_group.
    type: list
    elements: dict
    default: []
  templates:
    description: All known template names, used to detect templates with no runs in the window.
    type: list
    elements: str
    default: []
  window_days:
    description: Only jobs finished within this many days before as_of are counted.
    type: int
    default: 30
  as_of:
    description: Reference time, ISO 8601 (UTC). Makes results reproducible.
    type: str
    required: true
  manual_groups:
    description: Assignment group names that mean "fell back to manual handling".
    type: list
    elements: str
    default: []
  manual_minutes:
    description: Per-template minutes a human would spend per successful run.
    type: dict
    default: {}
  default_manual_minutes:
    description: Used when a template is not in manual_minutes.
    type: int
    default: 30
  top_failures:
    description: How many failure reasons to return.
    type: int
    default: 5
"""
 
import math
import statistics
from datetime import datetime, timedelta, timezone
 
from ansible.module_utils.basic import AnsibleModule
 
FAIL_STATES = ("failed", "error")
DONE_STATES = ("successful", "failed", "error", "canceled")
 
 
def parse_ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
 
 
def p95(values):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]
 
 
def build_template_row(name, runs, tickets, manual_groups, minutes):
    done = [r for r in runs if r["status"] in DONE_STATES]
    ok = [r for r in done if r["status"] == "successful"]
    bad = [r for r in done if r["status"] in FAIL_STATES]
    elapsed = [float(r.get("elapsed") or 0) for r in ok]
    finished = max(done, key=lambda r: r["_finished"]) if done else None
    fallbacks = [t for t in tickets if t.get("assignment_group") in manual_groups]
    scored = len(ok) + len(bad)
    return {
        "name": name,
        "runs": len(done),
        "successful": len(ok),
        "failed": len(bad),
        "success_rate": round(100.0 * len(ok) / scored, 1) if scored else None,
        "median_runtime_s": round(statistics.median(elapsed), 1) if elapsed else None,
        "p95_runtime_s": round(p95(elapsed), 1) if elapsed else None,
        "last_run": finished["finished"] if finished else None,
        "last_status": finished["status"] if finished else None,
        "tickets": len(tickets),
        "fallback_to_manual": len(fallbacks),
        "fallback_rate": round(100.0 * len(fallbacks) / len(tickets), 1) if tickets else None,
        "hours_saved": round(len(ok) * minutes / 60.0, 1),
    }
 
 
def main():
    module = AnsibleModule(
        argument_spec=dict(
            jobs=dict(type="list", elements="dict", required=True),
            tickets=dict(type="list", elements="dict", default=[]),
            templates=dict(type="list", elements="str", default=[]),
            window_days=dict(type="int", default=30),
            as_of=dict(type="str", required=True),
            manual_groups=dict(type="list", elements="str", default=[]),
            manual_minutes=dict(type="dict", default={}),
            default_manual_minutes=dict(type="int", default=30),
            top_failures=dict(type="int", default=5),
        ),
        supports_check_mode=True,
    )
    p = module.params
 
    try:
        as_of = parse_ts(p["as_of"])
    except ValueError:
        module.fail_json(msg="as_of is not a valid ISO 8601 timestamp: %s" % p["as_of"])
    start = as_of - timedelta(days=p["window_days"])
 
    in_window = []
    for job in p["jobs"]:
        if not job.get("finished"):
            continue
        finished = parse_ts(job["finished"])
        if start <= finished <= as_of:
            row = dict(job)
            row["_finished"] = finished
            in_window.append(row)
 
    by_template = {}
    for job in in_window:
        by_template.setdefault(job["name"], []).append(job)
 
    tickets_by_template = {}
    for t in p["tickets"]:
        tickets_by_template.setdefault(t.get("automation"), []).append(t)
 
    rows = []
    for name in sorted(by_template):
        minutes = int(p["manual_minutes"].get(name, p["default_manual_minutes"]))
        rows.append(build_template_row(
            name, by_template[name], tickets_by_template.get(name, []), p["manual_groups"], minutes))
    # worst success rate first so problems surface at the top
    rows.sort(key=lambda r: (r["success_rate"] is None, r["success_rate"] if r["success_rate"] is not None else 0))
 
    reasons = {}
    for job in in_window:
        if job["status"] in FAIL_STATES:
            reason = (job.get("failure_reason") or job.get("job_explanation") or "").strip() or "unknown"
            reasons[reason] = reasons.get(reason, 0) + 1
    failure_reasons = [{"reason": k, "count": v}
                       for k, v in sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0]))][:p["top_failures"]]
 
    never_run = sorted(set(p["templates"]) - set(by_template))
 
    done = [j for j in in_window if j["status"] in DONE_STATES]
    ok = [j for j in done if j["status"] == "successful"]
    scored = [j for j in done if j["status"] in ("successful",) + FAIL_STATES]
    overall = {
        "window_days": p["window_days"],
        "as_of": p["as_of"],
        "runs": len(done),
        "successful": len(ok),
        "failed": len([j for j in done if j["status"] in FAIL_STATES]),
        "success_rate": round(100.0 * len(ok) / len(scored), 1) if scored else None,
        "templates_active": len(by_template),
        "templates_not_run": len(never_run),
        "hours_saved": round(sum(r["hours_saved"] for r in rows), 1),
    }
 
    module.exit_json(changed=False, overall=overall, templates=rows,
                     failure_reasons=failure_reasons, not_run=never_run)
 
 
if __name__ == "__main__":
    main()