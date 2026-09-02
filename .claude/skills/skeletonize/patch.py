"""Apply line-range replacements to a file, bottom-up, then check well-formedness.
usage: patch.py <file> <spec.py>   where spec.py defines EDITS = [(start, end, text), ...]
(1-based inclusive line numbers of the ORIGINAL file; text replaces those lines; '' deletes)."""
import sys, runpy, xml.etree.ElementTree as ET
path, spec = sys.argv[1], sys.argv[2]
edits = runpy.run_path(spec)['EDITS']
lines = open(path).read().split('\n')
# sanity: ranges must not overlap
rs = sorted((s, e) for s, e, _ in edits)
for (s1, e1), (s2, e2) in zip(rs, rs[1:]):
    assert e1 < s2, f"overlap {s1}-{e1} / {s2}-{e2}"
for s, e, text in sorted(edits, key=lambda x: -x[0]):
    assert 1 <= s <= e <= len(lines), (s, e, len(lines))
    new = text.strip('\n').split('\n') if text.strip() else []
    lines[s-1:e] = new
out = '\n'.join(lines)
try:
    ET.fromstring(out.encode())
except ET.ParseError as ex:
    print(f"XML ERROR (file NOT written) in {path}: {ex}")
    open(path + '.failed', 'w').write(out)
    sys.exit(1)
open(path, 'w').write(out)
print(f"OK: {path} now {len(lines)} lines, well-formed")
