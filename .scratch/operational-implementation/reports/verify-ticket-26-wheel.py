"""Verify ticket 26 source/archive bytes and packaged guidance symlink targets."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


def digest(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def required_paths(root, base):
    changed = subprocess.check_output(['git', 'diff', '--name-only', '--diff-filter=ACM', base, '--', 'src'], cwd=root, text=True).splitlines()
    paths = {p for p in changed if (root / p).is_file()}
    paths.update(str(p.relative_to(root)) for p in (root / 'src').rglob('*.sql'))
    paths.update(str(p.relative_to(root)) for p in (root / 'src/smi_review/static').rglob('*') if p.is_file())
    paths.update(str(p.relative_to(root)) for p in (root / 'src').rglob('AGENTS.md'))
    paths.update(str(p.relative_to(root)) for p in (root / 'src').rglob('CLAUDE.md'))
    return sorted(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, default=Path(__file__).with_name('ticket-26-wheel-manifest.json'))
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    base = '7459d1a8a6ccfd7b02220549682507e0d5011e4c'
    paths = required_paths(root, base)
    files = []
    with zipfile.ZipFile(args.wheel) as archive:
        for name in paths:
            path = root / name
            target = path.readlink().as_posix() if path.is_symlink() else None
            if target is not None:
                assert target == 'AGENTS.md' and path.resolve() == path.with_name('AGENTS.md').resolve(), name
            source_bytes = path.read_bytes()
            archive_name = name.removeprefix('src/')
            archive_bytes = archive.read(archive_name)
            assert source_bytes == archive_bytes, name
            files.append({'source': name, 'archive': archive_name, 'source_identity': digest(source_bytes),
                          'archive_identity': digest(archive_bytes), 'symlink_target': target})
        entry_count = len(archive.infolist())
    document = {'base_commit': base, 'files': files, 'wheel': {'filename': args.wheel.name,
        **digest(args.wheel.read_bytes()), 'entry_count': entry_count}}
    assert len([p for p in paths if p.endswith('.sql')]) == 9
    assert len([p for p in paths if '/static/' in p]) == 2
    if args.record:
        document['runtime_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        args.manifest.write_text(json.dumps(document, indent=2) + '\n')
    else:
        recorded = json.loads(args.manifest.read_text())
        assert {k: v for k, v in recorded.items() if k != 'runtime_commit'} == document
    print(f'Verified {len(files)} source/archive entries, nine SQL schemas, two review assets and all packaged guidance targets/siblings; wheel {document["wheel"]["size"]} bytes, {entry_count} entries.')


if __name__ == '__main__':
    main()
