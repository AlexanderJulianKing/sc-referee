# Migration from v0.6.0 to v0.7.0

Add empty `work_items` and `answers` arrays when migrating a v0.6.0 AuditBundle. Do not invent
interaction history, model proposals, scientist answers, or pre-lock lifecycle states. Existing
records retain their meaning and are versioned into the new namespace only through an explicit
migration output.
