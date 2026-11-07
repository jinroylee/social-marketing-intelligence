"""Check scratch artifact links, upstream IDs, generated markup, r1 identity, and hashes."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Markup(HTMLParser):
    """Check explicit tag balance without DOM repair, rendering, or browser execution."""
    void = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__()
        self.stack = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        self.ids.extend(value for key, value in attrs if key == 'id')
        if tag not in self.void:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.ids.extend(value for key, value in attrs if key == 'id')

    def handle_endtag(self, tag):
        assert self.stack and self.stack[-1] == tag, (tag, self.stack[-5:])
        self.stack.pop()


def anchors(path):
    text = path.read_text()
    if path.suffix == '.html':
        return set(re.findall(r'\bid="([^"]+)"', text))
    found = set()
    for heading in re.findall(r'^#{1,6}\s+(.+)$', text, re.M):
        heading = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        found.add(heading)
    return found


links = 0
for path in HERE.glob('*.md'):
    text = path.read_text()
    assert text.count('```') % 2 == 0, f'Unbalanced fence: {path.name}'
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
        target = target.strip('<>')
        parts = urlsplit(target)
        if parts.scheme or parts.netloc:
            continue
        destination = (path.parent / unquote(parts.path)).resolve() if parts.path else path
        assert destination.exists(), f'{path.name}: {target}'
        if parts.fragment:
            assert parts.fragment in anchors(destination), f'Unknown anchor in {path.name}: {target}'
        links += 1
print(f'PASS {links} local Markdown links including heading targets; fences balanced')

baseline = HERE.parent.parent / 'task1-recovery' / 'requirements-matrix.md'
upstream = re.findall(r'^\| ((?:FR|OFR|PROP|UD)-[A-Z0-9]+) \|', baseline.read_text(), re.M)
mapped = re.findall(r'^\| ((?:FR|OFR|PROP|UD)-[A-Z0-9]+):', (HERE / 'fr-ui-traceability.md').read_text(), re.M)
assert len(upstream) == len(set(upstream)) == len(mapped) == len(set(mapped)) == 99
assert set(upstream) == set(mapped)
for review in ['R2-CHAT', 'R2-STREAM', 'R2-GRAPH']:
    for name in ['changes.md', 'review-guide.md', 'fr-ui-traceability.md']:
        assert review in (HERE / name).read_text(), (review, name)
print('PASS all 99 upstream IDs retained exactly once; all 3 review requests mapped')

snapshots = json.loads(subprocess.check_output(['node', str(HERE / 'verify-prototype.cjs'), '--markup'], text=True))
for name, markup in snapshots.items():
    parser = Markup()
    parser.feed(markup)
    assert not parser.stack, (name, parser.stack)
    assert len(parser.ids) == len(set(parser.ids)), f'Duplicate ID: {name}'
print(f'PASS {len(snapshots)} EN/KO generated chat/chart/graph markup snapshots have balanced explicit tags and unique IDs')

original = json.loads((HERE / 'r1-integrity.json').read_text())
for name, expected in original.items():
    assert digest(HERE.parent / name) == expected, f'r1 changed: {name}'
print(f'PASS {len(original)} r1 files unchanged from start-of-dispatch snapshot')

manifest_path = HERE / 'artifact-manifest.json'
files = {p.name: digest(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name != manifest_path.name}
if '--write-manifest' in sys.argv:
    manifest = {
        'revision': 'r2',
        'status': 'pending_actual_human_review',
        'entrypoint': 'prototype.html?variant=A#campaigns',
        'browser_verification': 'not_performed_permission_declined_no_workaround',
        'production_graph_interactions': 'specified_not_implemented',
        'task4': 'not_approved_gate_unchanged',
        'hash_algorithm': 'SHA-256',
        'manifest_scope': 'All r2 files except this self-referential manifest',
        'files': files,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'WROTE manifest with {len(files)} actual SHA-256 digests')
elif '--check-manifest' in sys.argv:
    assert json.loads(manifest_path.read_text())['files'] == files, 'Manifest content differs'
    print(f'PASS {len(files)} manifest digests match exact r2 file bytes')
print('Source and fixture checks only. No browser, rendering, visual approval, or production interaction verification.')
