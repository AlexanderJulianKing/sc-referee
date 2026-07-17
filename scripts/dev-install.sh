#!/usr/bin/env bash
# Dev install into the local .venv.
#
# uv's editable redirect (_editable_impl_<name>.pth) is unreliably processed by CPython's
# site.py on this setup, so `import sc_referee` / the `sc-referee` console script can fail.
# We drop our OWN newline-terminated src .pth (a filename uv never rewrites) to guarantee
# the package is importable. CI installs non-editable (`uv pip install .`), which copies the
# package into site-packages and needs none of this.
set -euo pipefail
cd "$(dirname "$0")/.."

uv pip install -e ".[engine,dev,llm]"

SP="$(.venv/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
printf '%s\n' "$(cd src && pwd)" > "$SP/zz_scref_src.pth"

# Files created or downloaded by GUI applications on macOS can inherit UF_HIDDEN. Python 3.11's
# site.py intentionally skips *every* .pth file with that flag, which makes an otherwise-correct
# editable install fail with `ModuleNotFoundError`. Clear only that metadata bit; other platforms
# do not provide chflags and need no equivalent step.
if command -v chflags >/dev/null 2>&1; then
  chflags nohidden "$SP/zz_scref_src.pth"
fi

.venv/bin/python -c "import sc_referee; print('dev install OK:', sc_referee.__version__)"
