#!/usr/bin/env python3
"""Cross-reference and well-formedness checks for source/*.ptx.

    xrefs.py --check              well-formedness of every file, then list
                                  every <xref ref="..."/> whose target id
                                  exists nowhere in source/
    xrefs.py <file.ptx> [...]     for each xml:id defined in the file(s),
                                  how many times it is referenced from the
                                  same file and from which other files

Run from the project root.  Only files reachable from source/main.ptx by
xi:include are read (commented-out includes count too), so the retired
files in source/ are ignored.
"""
import collections, glob, os, re, sys
import xml.etree.ElementTree as ET

# Only files reachable from main.ptx by xi:include are checked; the retired
# files in source/ (section-arc-length-old.ptx and friends) are ignored.
def included(root):
    seen, todo = set(), [root]
    while todo:
        f = todo.pop()
        if f in seen or not os.path.exists(f):
            continue
        seen.add(f)
        for h in re.findall(r'<xi:include\s+href="([^"]+)"', open(f).read()):
            todo.append(os.path.join(os.path.dirname(f), h))
    return seen
files = sorted(included('source/main.ptx'))
ids, refs = set(), collections.defaultdict(list)
for f in files:
    s = open(f).read()
    ids |= set(re.findall(r'xml:id="([^"]+)"', s))
    for m in re.finditer(r'<xref[^>]*\sref="([^"]+)"', s):
        for r in m.group(1).split():
            refs[r].append(os.path.basename(f))

if sys.argv[1:] == ['--check'] or not sys.argv[1:]:
    bad = 0
    for f in files:
        try:
            ET.parse(f)
        except ET.ParseError as e:
            print(f"NOT WELL-FORMED {f}: {e}"); bad += 1
    for r, v in sorted(refs.items()):
        if r not in ids:
            print("UNRESOLVED", r, sorted(set(v))); bad += 1
    print("ok" if not bad else f"{bad} problem(s)")
    sys.exit(1 if bad else 0)

for t in sys.argv[1:]:
    s = open(t).read()
    base = os.path.basename(t)
    print(f"=== {base}")
    for i in re.findall(r'xml:id="([^"]+)"', s):
        ext = sorted(set(x for x in refs.get(i, []) if x != base))
        n_int = sum(1 for x in refs.get(i, []) if x == base)
        flag = "  <== EXTERNAL: " + ",".join(ext) if ext else ""
        print(f"  {i:45s} internal={n_int}{flag}")
