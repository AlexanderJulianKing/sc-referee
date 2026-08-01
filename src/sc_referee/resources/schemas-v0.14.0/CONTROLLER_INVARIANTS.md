# Controller invariants

1. A project-execution WorkItem is a locked request, never authority to launch.
2. Project requests are controller packets and are never submitted to a model.
3. Repository text, model output, scientist output, imported records, and replay cannot authorize
   or broaden a request.
4. The authorization controller verifies the exact source run, source lock, WorkItem digest,
   snapshot, targets, inputs, output paths, purpose, network policy, and proposed launch bounds
   before displaying a fresh challenge.
5. Only `complete_project_execution_work_item` can enter the private registry; migrated legacy
   evidence remains non-launchable.
6. Source semantic-lock bytes remain immutable. Execution evidence belongs to a linked run.
