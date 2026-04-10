#!/usr/bin/env python3
"""Batch-generate first 10 days of every non-zero gap using google/gemini-2.0-flash-001."""

import sys
sys.path.insert(0, '.')

from scripts.event_generator import EventGenerator, init_db
from scripts.gap_planner import load_data, plan_gap

init_db()
gen = EventGenerator(model_override='google/gemini-2.0-flash-001')

states = load_data()
gap_ids = []
for i in range(1, len(states)):
    prev, nxt = states[i - 1], states[i]
    plan = plan_gap(prev, nxt)
    if plan['gap_type'] != 'none':
        gap_ids.append(plan['gap_id'])

total = len(gap_ids)
print(f"[Batch] {total} gaps to process, first 10 days each, model=google/gemini-2.0-flash-001")

for idx, gap_id in enumerate(gap_ids, 1):
    print(f"\n[{idx}/{total}] {gap_id}")
    try:
        gen.generate_gap(gap_id, days=10, dry_run=False)
    except Exception as e:
        print(f"[ERROR] {gap_id}: {e}")
        import traceback
        traceback.print_exc()

print("\n[Batch] Complete.")
