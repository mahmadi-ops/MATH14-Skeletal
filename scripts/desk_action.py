#!/usr/bin/env python3
"""Posting Desk mechanical action: post or unpost one topic.

Usage: desk_action.py post-notes|unpost-notes <topic-xml-id> [<topic-xml-id> ...]

A topic is a lecture section, an assignment, or a review set; the key is
its xml:id (also the page name on the site).  Several keys make one change,
checked as a whole, which is how a set of topics that cite each other comes
down together.  Posting unwraps the topic's
<xi:include>; unposting wraps it in the UNPOSTED comment described in
CLAUDE.md.  Every root file that includes the topic is treated alike
(main.ptx and, where it exists, main-print.ptx).

The chapters of this book are written inline in the root files, so a
chapter whose every section is unposted cannot simply lose an include: the
whole <chapter> block is wrapped in the HIDDEN-CHAPTER markers that the
written-assignments chapter already uses, with its includes left bare
inside (a comment may not nest a comment).  Posting a section into a
hidden chapter reverses that: the chapter comes back with every other
section wrapped.  While no real chapter is visible at all, the placeholder
chapter ch-coming-soon.ptx keeps the book valid.

Unposting also wraps any dependent include whose cross-references would
otherwise dangle (marked UNPOSTED-WITH so the matching post restores it).
If a dangling reference cannot be fixed that way, every touched file is
restored and the script exits nonzero, so nothing half-done gets committed.

Exit 0: repo now in the requested state (possibly with no change).
Exit 1: bad invocation.  Exit 2: cannot be done mechanically.
"""
import os
import re
import sys

SRC = "source"
ROOTS = [p for p in ("source/main.ptx", "source/main-print.ptx") if os.path.exists(p)]

# The chapters the desk manages.  The written-assignments chapter is hidden
# by hand with the same markers and is deliberately not listed here.
CHAPTERS = ("ch-curves-and-fields", "ch-multiple-integrals", "ch-integral-theorems", "ch-problems")

# A book needs a chapter, so this placeholder stands in while every real
# chapter is hidden, and goes away again as soon as one is visible.
PLACEHOLDER = "ch-coming-soon.ptx"

# topic key (xml:id) -> include href.  The same file is included by every
# root that carries the topic; assignments and review sets are web-only.
TOPICS = {
    # Chapter 1: Line Integrals
    "sec-parametrization": "section-parametrization.ptx",
    "sec-arc-length": "section-arc-length.ptx",
    "sec-line-integrals": "section-line-integrals.ptx",
    "sec-vector-fields": "section-vector-fields.ptx",
    "section-conservative-fields": "conservative-fields.ptx",
    # Chapter 2: Multiple Integrals
    "section-double-integrals-rectangles": "double-integrals-rectangles.ptx",
    "section-double-integrals-general-regions": "double-integrals-general-regions.ptx",
    "section-polar-coordinates": "polar-coordinates.ptx",
    "section-double-integrals-polar-form": "double-integrals-polar-form.ptx",
    "section-triple-integrals-rectangular": "triple-integrals-rectangular.ptx",
    "section-triple-integrals-cylindrical": "triple-integrals-cylindrical.ptx",
    "section-triple-integrals-spherical": "triple-integrals-spherical.ptx",
    "section-mass-center-of-mass": "mass-center-of-mass.ptx",
    "section-jacobian-substitution": "jacobian-substitution.ptx",
    "section-surface-integrals": "surface-integrals.ptx",
    # Chapter 3: The Big Theorems
    "section-greens-theorem": "greens-theorem.ptx",
    "section-stokes-theorem": "stokes-theorem.ptx",
    "section-divergence-theorem": "divergence-theorem.ptx",
    # Assignments and Review Problems (web root only)
    "sec-exercises-hw1-online": "hw1-online.ptx",
    "sec-exercises-hw2-online": "hw2-online.ptx",
    "sec-exercises-hw3-online": "hw3-online.ptx",
    "sec-exercises-hw4-online": "hw4-online.ptx",
    "sec-exercises-hw5-online": "hw5-online.ptx",
    "sec-exercises-hw6-online": "hw6-online.ptx",
    "sec-exercises-hw7-online": "hw7-online.ptx",
    "sec-exercises-hw8-online": "hw8-online.ptx",
    "sec-exercises-hw9-online": "hw9-online.ptx",
    "sec-exercises-hw10-online": "hw10-online.ptx",
    "sec-exercises-review1-practice": "review1-practice.ptx",
    "sec-exercises-review2-practice": "review2-practice.ptx",
    "sec-exercises-review3-practice": "review3-practice.ptx",
    "sec-exercises-review4-practice": "review4-practice.ptx",
}


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def inc_re(href):
    return re.compile(r'<xi:include\s+href="\.?/?%s"\s*/>' % re.escape(href))


def wrapped_re(href):
    return re.compile(
        r'<!--\s*UNPOSTED(?:-WITH topic="([^"]*)")?\s+'
        r'(<xi:include\s+href="\.?/?%s"\s*/>)\s+UNPOSTED\s*-->' % re.escape(href)
    )


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


# ---------------------------------------------------------------- includes

def unpost_include(path, href, topic=None):
    """Wrap one include.  Returns 'done', 'already', or 'absent'."""
    text = read(path)
    if wrapped_re(href).search(text):
        return "already"
    m = inc_re(href).search(text)
    if m is None:
        return "absent"
    tag = "UNPOSTED" if topic is None else 'UNPOSTED-WITH topic="%s"' % topic
    write(path, text[: m.start()] + "<!-- %s %s UNPOSTED -->" % (tag, m.group(0)) + text[m.end():])
    return "done"


def post_include(path, href):
    """Unwrap one include.  Returns 'done', 'already', or 'absent'."""
    text = read(path)
    m = wrapped_re(href).search(text)
    if m is None:
        return "already" if inc_re(href).search(text) else "absent"
    write(path, text[: m.start()] + m.group(2) + text[m.end():])
    return "done"


# ---------------------------------------------------------------- chapters

def hidden_re(cid):
    # Tempered so the match can never run across a neighbouring block: the
    # stretch between the BEGIN marker and this chapter's opening tag may not
    # contain another chapter's close or an END marker.
    return re.compile(
        r'^([ \t]*)<!-- HIDDEN-CHAPTER-BEGIN[ \t]*\n'
        r'((?:(?!</chapter>|HIDDEN-CHAPTER-END).)*?<chapter xml:id="%s">.*?</chapter>)'
        r'[ \t]*\n[ \t]*HIDDEN-CHAPTER-END -->' % re.escape(cid), re.S | re.M)


def visible_re(cid):
    return re.compile(r'^([ \t]*)<chapter xml:id="%s">.*?</chapter>' % re.escape(cid), re.S | re.M)


def chapter_state(text, cid):
    """('hidden', match) / ('visible', match) / (None, None)."""
    m = hidden_re(cid).search(text)
    if m:
        return "hidden", m
    m = visible_re(cid).search(text)
    if m:
        return "visible", m
    return None, None


def hide_chapter(path, cid):
    """Wrap a visible chapter whose includes are all wrapped: the includes
    are unwrapped first, since the chapter comment may not contain them as
    comments, and the block is checked for anything else a comment forbids."""
    text = read(path)
    state, m = chapter_state(text, cid)
    if state != "visible":
        return "already" if state == "hidden" else "absent"
    indent, block = m.group(1), m.group(0)[len(m.group(1)):]
    block = re.sub(r'<!--\s*UNPOSTED(?:-WITH topic="[^"]*")?\s+(<xi:include\s+href="[^"]+"\s*/>)\s+UNPOSTED\s*-->',
                   lambda w: w.group(1), block)
    if "--" in block or "<!--" in block:
        sys.exit("chapter %s in %s contains '--' or a comment and cannot be hidden" % (cid, path))
    new = "%s<!-- HIDDEN-CHAPTER-BEGIN\n%s%s\n%sHIDDEN-CHAPTER-END -->" % (indent, indent, block, indent)
    write(path, text[: m.start()] + new + text[m.end():])
    return "done"


def unhide_chapter(path, cid):
    """Bring a hidden chapter back with every include wrapped, so that only
    the section then posted becomes visible."""
    text = read(path)
    state, m = chapter_state(text, cid)
    if state != "hidden":
        return "already" if state == "visible" else "absent"
    block = m.group(2)  # starts with the <chapter line's own indentation
    block = re.sub(r'<xi:include\s+href="[^"]+"\s*/>',
                   lambda w: "<!-- UNPOSTED %s UNPOSTED -->" % w.group(0), block)
    write(path, text[: m.start()] + block + text[m.end():])
    return "done"


def chapter_of(path, href):
    """The desk chapter (visible or hidden) whose block holds this include."""
    text = read(path)
    for cid in CHAPTERS:
        state, m = chapter_state(text, cid)
        if m and re.search(r'href="\.?/?%s"' % re.escape(href), m.group(0)):
            return cid, state
    return None, None


def live_in_chapter(path, cid):
    state, m = chapter_state(read(path), cid)
    if state != "visible":
        return []
    return re.findall(r'<xi:include\s+href="\.?/?([^"]+)"\s*/>', strip_comments(m.group(0)))


def sync_roots():
    """After a toggle: a visible chapter with nothing live is hidden, and the
    placeholder chapter is present exactly when no real chapter is visible."""
    for path in ROOTS:
        for cid in CHAPTERS:
            state, _ = chapter_state(read(path), cid)
            if state == "visible" and not live_in_chapter(path, cid):
                hide_chapter(path, cid)
        real = re.findall(r"<chapter\b", strip_comments(read(path)))
        if real:
            unpost_include(path, PLACEHOLDER)
        else:
            if post_include(path, PLACEHOLDER) == "absent":
                sys.exit("%s has no placeholder include for %s; add one (wrapped) before </book>" % (path, PLACEHOLDER))


# ------------------------------------------------------- cross-references

def expand(path, depth=0):
    """Inline xi:includes recursively, dropping XML comments (so wrapped
    includes and hidden chapters vanish), for cross-reference checking."""
    if depth > 20 or not os.path.exists(path):
        return ""
    text = strip_comments(read(path))
    return re.sub(r'<xi:include\s+href="\.?/?([^"]+)"\s*/>',
                  lambda m: expand(os.path.join(SRC, m.group(1)), depth + 1), text)


def dangling_refs():
    out = set()
    for root in ROOTS:
        full = expand(root)
        ids = set(re.findall(r'xml:id="([^"]+)"', full))
        for group in re.findall(r'<xref\b[^>]*\bref="([^"]+)"', full):
            for r in re.split(r"[,\s]+", group):
                if r and r not in ids:
                    out.add(r)
    return out


def files_referencing(ref_id):
    hits = []
    for name in os.listdir(SRC):
        if name.endswith(".ptx") and re.search(
                r'<xref\b[^>]*\bref="[^"]*\b%s\b[^"]*"' % re.escape(ref_id), read(os.path.join(SRC, name))):
            hits.append(name)
    return hits


# ------------------------------------------------------------------- main

def post(key, href):
    results = []
    for path in ROOTS:
        cid, state = chapter_of(path, href)
        if cid is None:
            continue
        if state == "hidden":
            unhide_chapter(path, cid)
        results.append(post_include(path, href))
    # restore dependents that were unposted together with this topic
    pat = re.compile(
        r'<!--\s*UNPOSTED-WITH topic="%s"\s+(<xi:include\s+href="[^"]+"\s*/>)\s+UNPOSTED\s*-->' % re.escape(key))
    for path in ROOTS:
        text = read(path)
        new = pat.sub(lambda m: m.group(1), text)
        if new != text:
            write(path, new)
    return "done" if "done" in results else ("already" if results else "absent")


def wrap_topic(href):
    """Wrap the topic's include in every root.  Inside a hidden chapter the
    include is already off the site (and wrapping it there would nest a
    comment), so that counts as done already."""
    results = []
    for path in ROOTS:
        cid, state = chapter_of(path, href)
        results.append("already" if state == "hidden" else unpost_include(path, href))
    return "done" if "done" in results else ("already" if "already" in results else "absent")


def fix_dependents(keys, baseline, bail):
    """After wrapping the batch, wrap any non-topic include whose references
    now dangle, tagging it with the batch topic that defines the target so
    reposting that topic brings it back.  A topic is never taken down as a
    side effect: that is an editorial call, so it bails to the Claude path."""
    topic_files = set(TOPICS.values())

    def owner(ref):
        for k in keys:
            if re.search(r'xml:id="%s"' % re.escape(ref), read(os.path.join(SRC, TOPICS[k]))):
                return k
        return keys[0]

    for _ in range(10):
        new_dangling = dangling_refs() - baseline
        if not new_dangling:
            return
        fixed_any = False
        for ref in sorted(new_dangling):
            for fname in files_referencing(ref):
                if fname in topic_files:
                    continue
                for path in ROOTS:
                    if unpost_include(path, fname, topic=owner(ref)) == "done":
                        fixed_any = True
        if not fixed_any:
            bail("unpost %s leaves dangling cross-references (%s) that cannot be fixed by wrapping an include"
                 % (" ".join(keys), ", ".join(sorted(new_dangling))))
    bail("unpost %s: dependency fixing did not converge" % " ".join(keys))


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("post-notes", "unpost-notes"):
        sys.exit(__doc__)
    action, keys = sys.argv[1], sys.argv[2:]
    for key in keys:
        if key not in TOPICS:
            sys.exit("unknown topic key: %s" % key)

    originals = {os.path.join(SRC, n): read(os.path.join(SRC, n))
                 for n in os.listdir(SRC) if n.endswith(".ptx")}

    def bail(msg):
        for p, s in originals.items():
            write(p, s)
        print(msg, file=sys.stderr)
        sys.exit(2)

    baseline = dangling_refs()
    states = {}
    if action == "post-notes":
        for key in keys:
            states[key] = post(key, TOPICS[key])
    else:
        for key in keys:
            states[key] = wrap_topic(TOPICS[key])
        if "done" in states.values():
            fix_dependents(keys, baseline, bail)
    for key, state in states.items():
        if state == "absent":
            bail("%s: include %s is in no root file" % (key, TOPICS[key]))
        print("%s %s: %s" % (action, key, state))

    sync_roots()

    leftover = dangling_refs() - baseline
    if leftover:
        bail("change would leave dangling cross-references: %s" % ", ".join(sorted(leftover)))

    from xml.etree import ElementTree as ET
    for p, s in originals.items():
        if read(p) != s:
            try:
                ET.fromstring(read(p))
            except ET.ParseError as e:
                bail("%s no longer parses: %s" % (p, e))
            print("modified: %s" % p)


if __name__ == "__main__":
    main()
