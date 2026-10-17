#!/usr/bin/python
# -*- coding: utf-8 -*-
# Standard library only, so it runs unchanged inside any AAP execution environment.
# No network access: the playbook reads the tasks, this module only counts.
 
from __future__ import absolute_import, division, print_function
 
__metaclass__ = type
 
DOCUMENTATION = r"""
---
module: opportunity_metrics
short_description: Find the request types that people still handle by hand
description:
  - Pure computation. Feed it ServiceNow tasks (for example sc_task) and it counts, per request type, how many
    were closed by the automation user and how many by people, and ranks the types people still handle.
options:
  tasks:
    description: List of task dicts.
    type: list
    elements: dict
    required: true
  type_field:
    description: Field that holds the request type (for example short_description).
    type: str
    default: short_description
  opened_field:
    description: Field with the opened time.
    type: str
    default: opened_at
  closed_field:
    description: Field with the closed time. Empty means the task is still open.
    type: str
    default: closed_at
  handler_fields:
    description: Fields that tell who handled the task, tried in order (the first one filled is used).
    type: list
    elements: str
    default: [closed_by.user_name, assigned_to.user_name]
  automation_user:
    description: User name of the automation account.
    type: str
    default: ""
  automation_users:
    description: More automation accounts (same meaning as automation_user).
    type: list
    elements: str
    default: []
  type_regex:
    description: Regular expression with one group. When it matches the request text, the group is the request type (for example an alert code at the start of an incident).
    type: str
    default: ""
  mask_patterns:
    description: Regular expressions whose matches are replaced by * in the request text, so hostnames and numbers do not make every request a new type.
    type: list
    elements: str
    default: []
  unknown_as_system:
    description: When true, a closed task with no handler at all (empty closed_by and assigned_to) counts as system, not as people.
    type: bool
    default: true
  type_labels:
    description: Readable text for a request type key (for example a change model number). The report shows "KEY - label".
    type: dict
    default: {}
  automated_if_handled:
    description: When true, a request type counts as already automated as soon as the automation account closed at least one task of it.
    type: bool
    default: false
  already_automated:
    description: Request types that already have an automation. They are listed separately.
    type: list
    elements: str
    default: []
  minutes_per_task:
    description: Minutes a person needs for one task, per request type.
    type: dict
    default: {}
  default_minutes:
    description: Minutes used for types not in minutes_per_task. 0 means hours are not estimated.
    type: int
    default: 0
  window_days:
    description: Length of the period the tasks cover. Used to turn counts into a monthly figure.
    type: int
    default: 90
  normalize_patterns:
    description: Regular expressions removed from the request type text before grouping (for example a leading date).
    type: list
    elements: str
    default: []
  system_users:
    description: Handler names that are the platform itself (workflows, business rules). Counted as system, not people.
    type: list
    elements: str
    default: []
  quick_close_minutes:
    description: A task closed within this many minutes of opening, by someone other than the automation user, counts as system. 0 turns it off.
    type: int
    default: 0
  min_volume:
    description: Request types with fewer tasks than this are ignored as noise.
    type: int
    default: 3
  top_n:
    description: How many candidates to return.
    type: int
    default: 15
"""
 
import re
import statistics
from collections import Counter
from datetime import datetime, timezone
 
from ansible.module_utils.basic import AnsibleModule
 
 
def text(value):
    if isinstance(value, dict):
        value = value.get("value") or value.get("display_value") or ""
    return ("" if value is None else str(value)).strip()
 
 
def parse_ts(value):
    value = text(value)
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
 
 
def main():
    module = AnsibleModule(
        argument_spec=dict(
            tasks=dict(type="list", elements="dict", required=True),
            type_field=dict(type="str", default="short_description"),
            opened_field=dict(type="str", default="opened_at"),
            closed_field=dict(type="str", default="closed_at"),
            handler_fields=dict(type="list", elements="str", default=["closed_by.user_name", "assigned_to.user_name"]),
            automation_user=dict(type="str", default=""),
            automation_users=dict(type="list", elements="str", default=[]),
            type_regex=dict(type="str", default=""),
            mask_patterns=dict(type="list", elements="str", default=[]),
            automated_if_handled=dict(type="bool", default=False),
            unknown_as_system=dict(type="bool", default=True),
            type_labels=dict(type="dict", default={}),
            already_automated=dict(type="list", elements="str", default=[]),
            minutes_per_task=dict(type="dict", default={}),
            default_minutes=dict(type="int", default=0),
            window_days=dict(type="int", default=90),
            normalize_patterns=dict(type="list", elements="str", default=[]),
            system_users=dict(type="list", elements="str", default=[]),
            quick_close_minutes=dict(type="int", default=0),
            min_volume=dict(type="int", default=3),
            top_n=dict(type="int", default=15),
        ),
        supports_check_mode=True,
    )
    p = module.params
    automated_types = set(t.strip() for t in p["already_automated"])
    monthly = 30.0 / p["window_days"] if p["window_days"] else 1.0
 
    patterns = [re.compile(x) for x in p["normalize_patterns"]]
    masks = [re.compile(x) for x in p["mask_patterns"]]
    type_re = re.compile(p["type_regex"]) if p["type_regex"] else None
    automation_set = set(u.strip() for u in ([p["automation_user"]] + list(p["automation_users"])) if u and u.strip())
    system_users = set(u.strip() for u in p["system_users"])
 
    def normalize(value):
        if type_re:
            m = type_re.match(value)
            if m and m.groups():
                return m.group(1).strip()
        for pat in patterns:
            value = pat.sub("", value, count=1).strip()
        for pat in masks:
            value = pat.sub("*", value)
        return value
 
    groups = {}
    for t in p["tasks"]:
        key = normalize(text(t.get(p["type_field"]))) or "(no description)"
        groups.setdefault(key, []).append(t)
 
    rows = []
    handler_counts = Counter()
    closed_total = closed_by_automation = closed_by_system = 0
    for key, items in groups.items():
        closed = [t for t in items if text(t.get(p["closed_field"]))]
        by_auto = by_people = by_system = 0
        hours = []
        for t in closed:
            handler = ""
            for f in p["handler_fields"]:
                handler = text(t.get(f))
                if handler:
                    break
            opened, closed_at = parse_ts(t.get(p["opened_field"])), parse_ts(t.get(p["closed_field"]))
            took = (closed_at - opened).total_seconds() if (opened and closed_at and closed_at >= opened) else None
            handler_counts[handler or "(empty)"] += 1
            if handler in automation_set:
                by_auto += 1
            elif (not handler and p["unknown_as_system"]) or handler in system_users or (p["quick_close_minutes"] and took is not None
                                             and took <= p["quick_close_minutes"] * 60):
                by_system += 1
            else:
                by_people += 1
            if took is not None:
                hours.append(took / 3600.0)
        closed_total += len(closed)
        closed_by_automation += by_auto
        closed_by_system += by_system
        handled = by_auto + by_people
        minutes = int(p["minutes_per_task"].get(key, p["default_minutes"]))
        label = p["type_labels"].get(key)
        rows.append({
            "type": ("%s - %s" % (key, label)) if label else key,
            "requests": len(items),
            "closed": len(closed),
            "open_now": len(items) - len(closed),
            "by_automation": by_auto,
            "by_people": by_people,
            "by_system": by_system,
            "automation_percent": round(100.0 * by_auto / handled, 1) if handled else None,
            "median_hours_to_close": round(statistics.median(hours), 1) if hours else None,
            "minutes_per_task": minutes,
            "people_hours_per_month": round(by_people * minutes / 60.0 * monthly, 1) if minutes else None,
            "already_automated": key in automated_types or (p["automated_if_handled"] and by_auto > 0),
        })
 
    candidates = [r for r in rows if not r["already_automated"] and r["requests"] >= p["min_volume"]
                  and r["by_people"] > 0]
    # biggest first: hours when minutes are known, otherwise the number of tasks people handled
    candidates.sort(key=lambda r: (-(r["people_hours_per_month"] or 0), -r["by_people"], r["type"]))
    automated = sorted((r for r in rows if r["already_automated"]), key=lambda r: -r["requests"])
    all_people = sum(r["by_people"] for r in rows)
    candidate_people = sum(r["by_people"] for r in candidates)
 
    module.exit_json(
        changed=False,
        overall={
            "window_days": p["window_days"],
            "tasks": len(p["tasks"]),
            "types": len(rows),
            "closed": closed_total,
            "closed_by_automation": closed_by_automation,
            "closed_by_system": closed_by_system,
            "closed_by_people": closed_total - closed_by_automation - closed_by_system,
            "automation_percent": (round(100.0 * closed_by_automation / (closed_total - closed_by_system), 1)
                                   if (closed_total - closed_by_system) else None),
            "candidate_types": len(candidates),
            "candidate_people_tasks": candidate_people,
            "people_tasks_all_types": all_people,
            "hours_estimated": any(r["minutes_per_task"] for r in candidates),
            "hours_per_month": round(sum(r["people_hours_per_month"] or 0 for r in candidates), 1),
        },
        handlers=[{"handler": k, "count": v} for k, v in handler_counts.most_common(10)],
        candidates=candidates[:p["top_n"]],
        automated=automated,
    )
 
 
if __name__ == "__main__":
    main()