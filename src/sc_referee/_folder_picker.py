"""Short-lived helper that opens the native folder chooser in ITS OWN process and prints the result.

Why a separate process: opening a native folder panel calls ``tkinter``'s ``Tk()``, and on macOS ``Tk()``
creates the process-global ``NSApplication`` singleton. Python 3.11 destroys the temporary Tk *root* after
the panel closes, but nothing tears that ``NSApplication`` down — so a long-lived server that ran the panel
in-process would stay a registered, foreground-capable "python" GUI app that never services its Cocoa event
loop, leaving the reviewer with a spinning beach ball and a stuck menu bar while the browser form sits behind
it. Isolated in this helper, the ``NSApplication`` dies when the process exits and focus returns to the
browser, and the ``referee`` server never initializes Tk at all.

Protocol: emit exactly one line of JSON to stdout — ``{"ok": true, "path": <str|null>}`` on success (``null``
means the reviewer cancelled) or ``{"ok": false, "error": <str>}`` on failure — and exit 0 (success) or 3
(failure). The parent (`sc_referee.friendly._ask_directory`) reads that line.
"""
from __future__ import annotations

import json
import sys
from typing import Callable, Optional, TextIO


def choose_directory() -> Optional[str]:
    """Return the directory the reviewer chose, or ``None`` if they cancelled."""
    from tkinter import filedialog

    # Do not give the chooser a hidden Tk parent. On macOS that turns the native panel into a sheet
    # attached to an invisible window: it appears top-left and cannot be moved like a normal Finder
    # panel. With no explicit parent, tkinter owns a temporary root internally and the OS centers and
    # moves the chooser normally. (Preserves the earlier launcher UX fix.)
    selected = filedialog.askdirectory(
        title="Choose an analysis folder for sc-referee", mustexist=True)
    return selected or None


def main(argv: Optional[list] = None, *, choose: Callable[[], Optional[str]] = choose_directory,
         stdout: Optional[TextIO] = None) -> int:
    """Run the chooser and write the JSON result line; return 0 on success, 3 on failure."""
    out = stdout if stdout is not None else sys.stdout
    try:
        path = choose()
    except Exception as exc:                       # tkinter missing, no display, Tcl error, cancel-via-error
        json.dump({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, out)
        out.write("\n")
        return 3
    json.dump({"ok": True, "path": path}, out)
    out.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
