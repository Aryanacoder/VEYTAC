# Reviewed demo-session dataset checklist

Each session that counts toward training/evaluation data must meet ALL items.
One session ≈ one task demonstration (3–10 min) + review. Aim for ≥3 sessions
before the first SFT launch (train/val split needs ≥2 sessions; §7).

## Per session

- [ ] Task brief written: objective, visible references, outcome check.
- [ ] Four separate permissions recorded: capture, external inference,
      training, publication (a "yes" to recording is not a "yes" to training).
- [ ] Full stream saved (chunks + gaps marked), not only snapshots.
- [ ] ≥1 AI question genuinely grounded in an observed gap, answered live by
      the expert (mock questions do not count; label execution mode).
- [ ] Transcript keeps the expert's original language + corrections.
- [ ] ≥1 contrasting case defined (condition where the decision differs).
- [ ] Reviewer approved the decision record with scope (`approved_scope` set).
- [ ] Episode assembled, quality report `valid`, export bundle checksums verify.
- [ ] Source/rights entry: who may train on this, who may redistribute it.

## Can we use open-source datasets? Yes — for the right jobs

| Source | Good for | Not valid for |
|---|---|---|
| Ego-Exo4D commentary | Question/commentary structure, gap-format design | Our expert's decisions (reviewer ≠ demonstrator) |
| IndustReal | Assembly perception checks | Action/policy claims without alignment gate |
| robomimic / robosuite | Robot BC baseline, action-aligned trajectories | Industrial generalization claims |
| REASSEMBLE (optional) | Richer assembly annotations | Same limits as above |

Rules (non-negotiable): register every source with license + split group
before use; never put hidden ground truth into evaluation prompts; a public
video reviewed by our expert is a **reviewer's interpretation**, not the
original demonstrator's reasoning — attribution must say so.
