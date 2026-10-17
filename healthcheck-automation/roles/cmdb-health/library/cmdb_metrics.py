#!/usr/bin/python
# -*- coding: utf-8 -*-
# Standard library only, so it runs unchanged inside any AAP execution environment.
# No network access: the playbook reads the CIs, this module only counts.
 
from __future__ import absolute_import, division, print_function
 
__metaclass__ = type
 
DOCUMENTATION = r"""
---
module: cmdb_metrics
short_description: Count data-quality problems in a list of CMDB configuration items
description:
  - Pure computation. Feed it CIs read from the ServiceNow Table API (reference fields as sys_id strings,
    use sysparm_exclude_reference_link=true) and it returns counts and lists of problem CIs.
options:
  cis:
    description: List of CI dicts.
    type: list
    elements: dict
    required: true
  as_of:
    description: Reference time, ISO 8601 (UTC).
    type: str
    required: true
  fields:
    description: Field names that were requested. Used to report how many CIs have each field filled.
    type: list
    elements: str
    default: []
  name_field:
    description: Field holding the CI name.
    type: str
    default: name
  class_field:
    description: Field holding the CI class.
    type: str
    default: sys_class_name
  status_field:
    description: Field holding the install status.
    type: str
    default: install_status
  in_scope_status_values:
    description: Install status values that count as live CIs. Empty means every CI is in scope.
    type: list
    elements: str
    default: []
  stale_field:
    description: Date field that tells when the CI was last seen (for example last_discovered).
    type: str
    default: last_discovered
  stale_fallback_field:
    description: Used when stale_field is empty.
    type: str
    default: sys_updated_on
  stale_days:
    description: A live CI not seen for more than this many days is stale.
    type: int
    default: 90
  owner_fields:
    description: A live CI with none of these fields filled has no owner.
    type: list
    elements: str
    default: []
  list_limit:
    description: Maximum number of CIs returned in each problem list.
    type: int
    default: 200
"""
 
from collections import Counter
from datetime import datetime, timezone
 
from ansible.module_utils.basic import AnsibleModule
 
 
def text(value):
    """Reference fields can come as {'value': ..} dicts. Return a plain string."""
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
            cis=dict(type="list", elements="dict", required=True),
            as_of=dict(type="str", required=True),
            fields=dict(type="list", elements="str", default=[]),
            name_field=dict(type="str", default="name"),
            class_field=dict(type="str", default="sys_class_name"),
            status_field=dict(type="str", default="install_status"),
            in_scope_status_values=dict(type="list", elements="str", default=[]),
            stale_field=dict(type="str", default="last_discovered"),
            stale_fallback_field=dict(type="str", default="sys_updated_on"),
            stale_days=dict(type="int", default=90),
            owner_fields=dict(type="list", elements="str", default=[]),
            list_limit=dict(type="int", default=200),
        ),
        supports_check_mode=True,
    )
    p = module.params
    as_of = parse_ts(p["as_of"])
    if as_of is None:
        module.fail_json(msg="as_of is not a valid timestamp: %s" % p["as_of"])
 
    cis = p["cis"]
    total = len(cis)
 
    field_fill = []
    for f in p["fields"]:
        filled = sum(1 for c in cis if text(c.get(f)))
        field_fill.append({"field": f, "filled": filled,
                           "percent": round(100.0 * filled / total, 1) if total else None})
 
    status_counts = Counter(text(c.get(p["status_field"])) or "(empty)" for c in cis)
    in_scope_values = set(p["in_scope_status_values"])
 
    name_counts = Counter()
    scoped = []
    for c in cis:
        status = text(c.get(p["status_field"]))
        if in_scope_values and status not in in_scope_values:
            continue
        scoped.append(c)
        name_counts[text(c.get(p["name_field"])).lower()] += 1
 
    stale, no_owner, duplicates, healthy = [], [], [], 0
    by_class = Counter()
    for c in scoped:
        name = text(c.get(p["name_field"]))
        cls = text(c.get(p["class_field"])) or "(no class)"
        seen = parse_ts(c.get(p["stale_field"])) or parse_ts(c.get(p["stale_fallback_field"]))
        age = (as_of - seen).days if seen else None
        is_stale = seen is None or age > p["stale_days"]
        has_owner = (not p["owner_fields"]) or any(text(c.get(f)) for f in p["owner_fields"])
        is_dup = bool(name) and name_counts[name.lower()] > 1
 
        if is_stale:
            stale.append({"name": name, "class": cls, "days": age})
        if not has_owner:
            no_owner.append({"name": name, "class": cls})
        if is_dup:
            duplicates.append({"name": name, "class": cls})
        if is_stale or (not has_owner) or is_dup:
            by_class[cls] += 1
        else:
            healthy += 1
 
    # oldest first; CIs with no date at all come first
    stale.sort(key=lambda r: (r["days"] is not None, -(r["days"] or 0)))
    dup_groups = Counter(r["name"].lower() for r in duplicates)
    dup_display = {}
    for r in duplicates:
        dup_display.setdefault(r["name"].lower(), r["name"])
    duplicate_names = [{"name": dup_display[k], "count": v} for k, v in
                       sorted(dup_groups.items(), key=lambda kv: (-kv[1], kv[0]))]
    limit = p["list_limit"]
    in_scope = len(scoped)
 
    module.exit_json(
        changed=False,
        overall={
            "as_of": p["as_of"],
            "total_read": total,
            "in_scope": in_scope,
            "out_of_scope": total - in_scope,
            "stale_days": p["stale_days"],
            "stale": len(stale),
            "no_owner": len(no_owner),
            "duplicate_name_cis": len(duplicates),
            "duplicate_names": len(duplicate_names),
            "healthy": healthy,
            "health_percent": round(100.0 * healthy / in_scope, 1) if in_scope else None,
        },
        stale=stale[:limit],
        stale_names=[r["name"] for r in stale],
        no_owner=no_owner[:limit],
        duplicates=duplicate_names[:limit],
        problems_by_class=[{"class": k, "count": v} for k, v in by_class.most_common(10)],
        field_fill=field_fill,
        status_counts=[{"status": k, "count": v} for k, v in status_counts.most_common(10)],
    )
 
 
if __name__ == "__main__":
    main()