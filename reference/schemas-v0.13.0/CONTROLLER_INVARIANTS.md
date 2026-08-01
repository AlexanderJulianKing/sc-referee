# Controller invariants

1. Repository text, model output, Answers, WorkItems, fixtures, imports, and replay cannot authorize
   or launch project code.
2. A launch requires a matching unexpired controller-registry entry and an atomic no-replace
   consumption receipt; copied public JSON is evidence only.
3. `project_code_execution_supported` is true only with a fresh complete effective probe whose
   required controls all passed. No subprocess or unbound-remote fallback is equivalent.
4. Project execution follows a source semantic lock and produces a distinct linked semantic lock.
   No model call occurs in the linked reproduction segment.
5. `/project` is read-only, network is denied, the output and temporary filesystems are physically
   bounded, project processes are quiescent before capture, and cleanup failure blocks clean proof.
6. Process success is not scientific correctness and never establishes a Finding by itself.
