#!/usr/bin/env bash
# Build the deployable site: the web book with the print PDF alongside it.
#
# The navbar carries a "PDF" button (see assets/custom.js) pointing at
# math14-skeletal-notes.pdf next to the HTML pages, so the PDF has to end up
# inside output/web before `pretext deploy` copies that directory to the
# staging area.
#
# It is copied rather than deployed as its own target on purpose.  Giving the
# print target a `deploy-dir` would make it a deploy target, which flips
# `pretext deploy` from the "default_target" strategy to Pelican and rebuilds
# the site around a generated landing page; it would also publish the whole of
# output/print (.tex, .log and duplicated assets) instead of the one PDF.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PDF="math14-skeletal-notes.pdf"

pretext build web
pretext build print

cp "output/print/$PDF" "output/web/$PDF"

# A LaTeX abort leaves a truncated PDF behind, and `pretext build print` still
# exits 0 and prints "Success!  Built requested target(s) without errors."
# So check the page count ourselves.
#
# A fixed floor cannot work any more: the Posting Desk toggles sections in
# and out of the book, so an almost-empty PDF is a legitimate state.  The
# floor is therefore scaled to what is posted: every <xi:include> reachable
# from main-print.ptx (the print root) is one source file in the PDF, and
# the fixtures that are always present and carry no course content do not
# count.  PAGES_PER_FILE sits well below the true average so an uneven
# section does not trip the guard, and still catches a build that died
# partway through a full book.  Override for a one-off build with
# `PAGES_PER_FILE=... scripts/build-site.sh`, or set MIN_PAGES outright.
PAGES_PER_FILE="${PAGES_PER_FILE:-6}"

CONTENT_FILES="$(python3 - <<'PY'
import os, re

SRC = "source"
ROOT = "main-print.ptx" if os.path.exists("source/main-print.ptx") else "main.ptx"
FIXTURES = {ROOT, "docinfo.ptx", "frontmatter.ptx", "frontmatter-print.ptx",
            "preface-skeletal.ptx", "introduction.ptx", "subsec-brain-map.ptx",
            "ch-coming-soon.ptx"}

def includes(path):
    text = re.sub(r"<!--.*?-->", "", open(path, encoding="utf8").read(), flags=re.S)
    return re.findall(r'<xi:include\s+href="\.?/?([^"]+)"\s*/>', text)

seen = set()

def walk(name):
    path = os.path.join(SRC, name)
    if name in seen or not os.path.exists(path):
        return
    seen.add(name)
    for href in includes(path):
        walk(href)

walk(ROOT)
print(len(seen - FIXTURES))
PY
)"

MIN_PAGES="${MIN_PAGES:-$(( CONTENT_FILES * PAGES_PER_FILE ))}"

# pretext depends on pyMuPDF, so it is present wherever this script can run.
# The module was renamed from `fitz` to `pymupdf` in 1.24.3; accept either.
PAGES="$(python3 - "output/web/$PDF" <<'PY'
import sys
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf
print(pymupdf.open(sys.argv[1]).page_count)
PY
)"

if [ "$PAGES" -lt "$MIN_PAGES" ]; then
    echo "ERROR: $PDF has $PAGES pages, expected at least $MIN_PAGES" >&2
    echo "       ($CONTENT_FILES content files posted, $PAGES_PER_FILE pages each)." >&2
    echo "       LaTeX almost certainly aborted partway and the PDF is truncated," >&2
    echo "       even though pretext reported success.  To see the error it" >&2
    echo "       swallowed, build the latex target and compile it by hand:" >&2
    echo "         pretext build latex" >&2
    echo "         cd output/latex && xelatex -interaction=nonstopmode main.tex" >&2
    echo "         grep -n '^!' main.log" >&2
    exit 1
fi

echo "Site ready in output/web (PDF: $PAGES pages, floor $MIN_PAGES, $(du -h "output/web/$PDF" | cut -f1))"
