"""Verify ticket 35 exact source/archive bytes and packaged guidance targets."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


BASE = 'dbd4cf9973d7b756adea1da65a29542fda64b1d9'
RUNTIME = '324ee32a640aba7828fa4d4c2fa1644a42cdc726'
FROZEN = 'bf526f6fa7a8b740fc678b2b084f1a807a2581d5'


def identity(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def required_paths(root):
    changed = subprocess.check_output(['git', 'diff', '--name-only', '--diff-filter=ACM', BASE, FROZEN, '--', 'src'], cwd=root, text=True).splitlines()
    paths = {name for name in changed if (root / name).is_file()}
    paths.update(str(p.relative_to(root)) for p in (root / 'src').rglob('*.sql'))
    paths.update(str(p.relative_to(root)) for p in (root / 'src/smi_review/static').rglob('*') if p.is_file())
    paths.update(str(p.relative_to(root)) for p in (root / 'src').rglob('AGENTS.md'))
    paths.update(str(p.relative_to(root)) for p in (root / 'src').rglob('CLAUDE.md'))
    return sorted(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, default=Path(__file__).with_name('ticket-35-wheel-manifest.json'))
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    assert subprocess.run(['git', 'diff', '--quiet', FROZEN, '--', 'src', 'tests', 'docs', 'tools', 'pyproject.toml', 'uv.lock', 'README.md', 'GLOSSARY.md', 'AGENTS.md', 'CLAUDE.md'], cwd=root).returncode == 0, 'runtime tree changed after freeze'
    paths = required_paths(root)
    schema_count = len([p for p in paths if p.endswith('.sql')])
    assets = [p for p in paths if '/static/' in p]
    guidance = [p for p in paths if p.endswith('/AGENTS.md')]
    assert schema_count == 18, schema_count
    assert len(assets) == 2, assets
    assert len(guidance) == 31, guidance
    assert all(p.replace('/AGENTS.md', '/CLAUDE.md') in paths for p in guidance)
    files = []
    with zipfile.ZipFile(args.wheel) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), 'duplicate archive entries'
        for name in paths:
            source = root / name
            target = source.readlink().as_posix() if source.is_symlink() else None
            if name.endswith('/CLAUDE.md'):
                assert target == 'AGENTS.md' and source.resolve() == source.with_name('AGENTS.md').resolve(), name
            source_bytes = source.read_bytes()
            archive_name = name.removeprefix('src/')
            archive_bytes = archive.read(archive_name)
            assert source_bytes == archive_bytes, name
            files.append({'source': name, 'archive': archive_name, 'source_identity': identity(source_bytes),
                          'archive_identity': identity(archive_bytes), 'symlink_target': target})
    protected_names = subprocess.check_output(['git', 'ls-files', '--', 'src', 'tests', 'docs', 'tools', 'pyproject.toml', 'uv.lock', 'README.md', 'GLOSSARY.md', 'AGENTS.md', 'CLAUDE.md'], cwd=root, text=True).splitlines()
    protected = []
    for name in protected_names:
        source = root / name
        protected.append({'path': name, **identity(source.read_bytes()), 'symlink_target': source.readlink().as_posix() if source.is_symlink() else None})
    changed_packaged = subprocess.check_output(['git', 'diff', '--name-only', '--diff-filter=ACM', BASE, FROZEN, '--', 'src'], cwd=root, text=True).splitlines()
    assert set(changed_packaged) <= set(paths), 'changed packaged file omitted'
    assert subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all', '--', 'src', 'tests', 'docs', 'tools', 'pyproject.toml', 'uv.lock', 'README.md', 'GLOSSARY.md', 'AGENTS.md', 'CLAUDE.md'], cwd=root, text=True) == '', 'dirty protected files'
    record = {'base_commit': BASE, 'final_review_base': '6220fff49b5b8e982ef5a8d54b7c788e45b0f648', 'runtime_commit': RUNTIME, 'frozen_commit': FROZEN,
              'files': files, 'changed_packaged_files': changed_packaged, 'protected_files': protected, 'sql_schema_count': schema_count, 'review_asset_count': len(assets),
              'packaged_guidance_pair_count': len(guidance), 'wheel': {'filename': args.wheel.name,
                  **identity(args.wheel.read_bytes()), 'entry_count': len(names)}, 'root_guidance': {
                  'agents': identity((root / 'AGENTS.md').read_bytes()), 'claude': identity((root / 'CLAUDE.md').read_bytes()),
                  'symlink_target': (root / 'CLAUDE.md').readlink().as_posix()}}
    assert record['root_guidance']['symlink_target'] == 'AGENTS.md'
    assert record['root_guidance']['agents'] == record['root_guidance']['claude']
    if args.record:
        assert subprocess.check_output(['git', 'rev-parse', RUNTIME], cwd=root, text=True).strip() == RUNTIME
        args.manifest.write_text(json.dumps(record, indent=2) + '\n')
    else:
        assert json.loads(args.manifest.read_text()) == record, 'manifest does not match exact source/archive identity'
    print(f'Verified {len(files)} exact source/archive entries, {schema_count} SQL schemas, {len(assets)} assets and {len(guidance)} packaged guidance pairs; wheel {record["wheel"]["size"]} bytes, {len(names)} unique entries; SHA-256 {record["wheel"]["sha256"]}.')


if __name__ == '__main__':
    main()
