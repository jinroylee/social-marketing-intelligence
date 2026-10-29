"""Verify the existing final-review wheel and every frozen protected source byte."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


BASE = '92967326912f025220374610e88f28a4f10350f2'
REVIEW_BASE = '6220fff49b5b8e982ef5a8d54b7c788e45b0f648'
RUNTIME = '7418e5bc0af72d70017b5eb612dcd2c37f265c57'
FROZEN = '7418e5bc0af72d70017b5eb612dcd2c37f265c57'


def identity(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, default=Path(__file__).with_name('final-review-fixes-wheel-manifest.json'))
    parser.add_argument('--record', action='store_true')
    parser.add_argument('--freeze', type=Path, help='Required pre-gate freeze when recording the manifest')
    args = parser.parse_args()
    root = args.root.resolve()
    assert git(root, 'rev-parse', FROZEN) == FROZEN
    assert git(root, 'rev-parse', RUNTIME) == RUNTIME
    frozen_names = [p for p in git(root, 'ls-tree', '-r', '--name-only', FROZEN).splitlines() if not p.startswith('.scratch/')]
    protected_names = [p for p in git(root, 'ls-files').splitlines() if not p.startswith('.scratch/')]
    assert protected_names == frozen_names, 'protected path set changed after freeze'
    assert len(protected_names) == 344, len(protected_names)
    assert subprocess.run(['git', 'diff', '--quiet', FROZEN, '--', *protected_names], cwd=root).returncode == 0, 'protected tree differs from freeze'
    assert not git(root, 'status', '--porcelain', '--untracked-files=all', '--', *protected_names), 'dirty protected files'
    assert not [p for p in git(root, 'ls-files', '--others', '--exclude-standard').splitlines() if not p.startswith('.scratch/')], 'untracked protected file'

    protected = []
    for name in protected_names:
        path = root / name
        protected.append({'path': name, **identity(path.read_bytes()),
                          'symlink_target': path.readlink().as_posix() if path.is_symlink() else None})
    paths = [p for p in protected_names if p.startswith('src/')]
    assert len(paths) == 211, len(paths)
    changed = git(root, 'diff', '--name-only', '--diff-filter=ACMR', BASE, FROZEN, '--', 'src').splitlines()
    review_changed = git(root, 'diff', '--name-only', '--diff-filter=ACMR', REVIEW_BASE, FROZEN, '--', 'src').splitlines()
    assert set(changed) <= set(paths), 'changed packaged file omitted'
    assert set(review_changed) <= set(paths), 'review-range packaged file omitted'
    schemas = [p for p in paths if p.endswith('.sql')]
    assets = [p for p in paths if '/static/' in p]
    assert len(schemas) == 19, schemas
    assert len(assets) == 2, assets
    guidance = []
    for name in protected_names:
        if Path(name).name != 'AGENTS.md':
            continue
        agents = root / name
        claude = agents.with_name('CLAUDE.md')
        assert claude.is_symlink() and claude.readlink().as_posix() == 'AGENTS.md', name
        assert claude.resolve() == agents.resolve(), name
        guidance.append({'agents': name, 'claude': claude.relative_to(root).as_posix(),
                         'agents_identity': identity(agents.read_bytes()),
                         'claude_identity': identity(claude.read_bytes()), 'symlink_target': 'AGENTS.md'})
    assert len(guidance) == 35
    assert len([g for g in guidance if g['agents'].startswith('src/')]) == 33
    assert any(g['agents'] == 'AGENTS.md' for g in guidance)

    files = []
    with zipfile.ZipFile(args.wheel) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), 'duplicate archive entries'
        for name in paths:
            path = root / name
            archive_name = name.removeprefix('src/')
            source_bytes, archive_bytes = path.read_bytes(), archive.read(archive_name)
            assert source_bytes == archive_bytes, name
            files.append({'source': name, 'archive': archive_name,
                          'source_identity': identity(source_bytes), 'archive_identity': identity(archive_bytes),
                          'symlink_target': path.readlink().as_posix() if path.is_symlink() else None})
    record = {'base_commit': BASE, 'final_review_base': REVIEW_BASE, 'runtime_commit': RUNTIME,
              'frozen_commit': FROZEN, 'files': files, 'changed_packaged_files': changed,
              'review_range_changed_packaged_files': review_changed, 'protected_files': protected,
              'guidance_pairs': guidance, 'sql_schemas': schemas, 'review_assets': assets,
              'wheel': {'filename': args.wheel.name, **identity(args.wheel.read_bytes()), 'entry_count': len(names)}}
    if args.record:
        assert args.freeze is not None, 'recording requires the original pre-gate freeze'
        freeze = json.loads(args.freeze.read_text())
        assert freeze['frozen_commit'] == FROZEN and freeze['runtime_commit'] == RUNTIME
        assert freeze['protected_files'] == protected, 'pre-gate protected bytes changed'
        args.manifest.write_text(json.dumps(record, indent=2) + '\n')
    else:
        assert json.loads(args.manifest.read_text()) == record, 'manifest differs from exact source/archive identity'
    print(json.dumps({'verified': True, 'protected_files': len(protected), 'source_archive_pairs': len(files),
                      'changed_packaged_files': len(changed), 'review_range_changed_packaged_files': len(review_changed),
                      'sql_schemas': len(schemas), 'review_assets': len(assets), 'guidance_pairs': len(guidance),
                      'packaged_guidance_pairs': 33, 'wheel': record['wheel']}, indent=2))


if __name__ == '__main__':
    main()
