"""Print a .ptx file with heavy figure internals collapsed, line-numbered."""
import re, sys
path = sys.argv[1]
lines = open(path).read().split('\n')
out = []
i = 0
COLLAPSE = ('prefigure', 'description', 'annotations', 'latex-image', 'shortdescription')
while i < len(lines):
    l = lines[i]
    m = re.match(r'\s*<(' + '|'.join(COLLAPSE) + r')[ >]', l)
    if m and not re.search(r'</' + m.group(1) + r'>', l):
        tag = m.group(1)
        j = i
        while j < len(lines) and not re.search(r'</' + tag + r'>', lines[j]):
            j += 1
        out.append(f"{i+1:5d}| {l.rstrip()}")
        if j > i + 1:
            out.append(f"     |   ... [{j-i-1} lines of <{tag}> elided] ...")
        out.append(f"{j+1:5d}| {lines[j].rstrip()}" if j < len(lines) else "")
        i = j + 1
        continue
    out.append(f"{i+1:5d}| {l.rstrip()}")
    i += 1
print('\n'.join(out))
