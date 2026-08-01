# Storage durability policy

Milestone 0 uses the following local-filesystem durability rules:

- normalized JSON is written to a unique same-directory temporary file, file-fsynced, atomically
  replaced, and followed by a parent-directory fsync;
- write-once normalized JSON is file-fsynced in a unique same-directory temporary file and then
  installed by an atomic hard link that fails for every pre-existing destination entry, including
  symlinks; a concurrent winner is preserved rather than replaced;
- JSONL records are serialized canonically, appended under an exclusive file lock, file-fsynced
  before return, and followed by a directory fsync when the record file is first created;
- a torn JSONL tail blocks future append and iteration instead of being silently ignored;
- iteration rejects invalid UTF-8, malformed JSON, noncanonical serialization, non-object records,
  and record types filed under the wrong JSONL path;
- the final StorageManifest and SQLite projection verification remain the run-level integrity
  commit checks.

These guarantees assume a local filesystem that honors `fsync`, atomic same-directory replacement,
and same-filesystem hard-link creation. Network filesystems and filesystems without ordinary hard
links remain outside Milestone 0 coverage.
