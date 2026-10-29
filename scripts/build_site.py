#!/usr/bin/env python3
"""Stage only public website assets, with a verifiable deployment manifest."""
import csv
import json
import shutil
import subprocess
from pathlib import Path
if __package__:
    from .validate_research_briefs import validate_from_files
    from .validate_adoption import validate_from_files as validate_adoption
    from .pilot_lab import run_from_files as run_pilot
else:
    from validate_research_briefs import validate_from_files
    from validate_adoption import validate_from_files as validate_adoption
    from pilot_lab import run_from_files as run_pilot

ROOT = Path(__file__).resolve().parents[1]
FILES = ('index.html', 'top30.html', 'project.html', 'blueprints.html', 'network.html', 'adoption.html', 'pilot-lab.html', 'README.md', 'LICENSE')
DIRECTORIES = ('data', 'docs')

def build(destination, source=ROOT, commit=None):
    destination, source = Path(destination).resolve(), Path(source).resolve()
    if destination == source or source.is_relative_to(destination):
        raise ValueError('Destination must not contain the source repository')
    for name in (*FILES, *DIRECTORIES):
        item = source / name
        if not item.exists():
            raise ValueError('Missing site asset: ' + name)
        if item.is_symlink() or (item.is_dir() and any(p.is_symlink() for p in item.rglob('*'))):
            raise ValueError('Symlinks are not published: ' + name)
    catalog = json.loads((source / 'data/catalog.json').read_text())
    curated = json.loads((source / 'data/curated.json').read_text())
    metadata = json.loads((source / 'data/repo_metadata.json').read_text())
    evidence = json.loads((source / 'data/top30_evidence.json').read_text())
    provenance = json.loads((source / 'data/provenance.json').read_text())
    with (source / 'data/top30_evaluation.csv').open(encoding='utf-8-sig') as file:
        projects = list(csv.DictReader(file))
    if not len(curated) <= len(catalog) <= 5000 or provenance['total'] != len(catalog):
        raise ValueError('Catalog count does not match provenance or capacity')
    if evidence['generated_from_snapshot_utc'] != metadata['generated_at_utc']:
        raise ValueError('Stale research evidence')
    if len(evidence['projects']) != len(projects):
        raise ValueError('Incomplete research evidence')
    # A published project-detail URL must resolve against all three source datasets.
    cases = json.loads((source / 'data/business_use_cases.json').read_text())
    if cases.get('status') != 'illustrative-blueprints-not-tested' or not isinstance(cases.get('domains'), dict):
        raise ValueError('Invalid or overstated blueprint evidence')
    domains = cases['domains']
    if len(domains) < 4 or any(
        not isinstance(c, dict) or not isinstance(c.get('flow'), list)
        or len(c['flow']) < 3 or not all(c.get(k) for k in ('goal', 'metric', 'risk'))
        for c in domains.values()
    ):
        raise ValueError('Incomplete blueprint data')
    slugs = [r['github_repository'].lower() for r in projects]
    if len(set(slugs)) != len(slugs) or any(r['domain'] not in domains for r in projects):
        raise ValueError('Project details refer to missing blueprints')
    if set(slugs) != {p['repo'].lower() for p in evidence['projects']}:
        raise ValueError('Project evidence repositories do not match the CSV')
    if not set(slugs).issubset(metadata['repositories']):
        raise ValueError('Project detail metadata is incomplete')
    # Editorial claims are first-class release data; stale or forged promotions block shipping.
    research_summary = validate_from_files(source)
    adoption_summary = validate_adoption(source)
    pilot_summary = run_pilot(source)
    if not pilot_summary['all_expected_met'] or pilot_summary['total_cases'] != 24:
        raise ValueError('Pilot contract baseline not reproducible; refuse deployment')
    if commit is None:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    manifest = {
        'schema_version': 1,
        'version': json.loads((source / 'package.json').read_text())['version'],
        'source_commit': commit,
        'catalog_count': len(catalog),
        'curated_count': len(curated),
        'research_project_count': len(projects),
        'blueprint_count': len(domains),
        'research_briefs_count': research_summary['count'],
        'research_reviewed_count': research_summary['reviewed'],
        **adoption_summary,
        'pilot_contract_cases': pilot_summary['total_cases'],
        'pilot_contract_passed': pilot_summary['passed_cases'],
        'pilot_upstream_packages_executed': pilot_summary['upstream_code_executed'],
        'metadata_snapshot_utc': metadata['generated_at_utc'],
        'catalog_snapshot_utc': provenance['generated_at_utc'],
    }
    # Rebuild only the selected destination after inputs have passed validation.
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for name in FILES:
        shutil.copyfile(source / name, destination / name)
    for name in DIRECTORIES:
        shutil.copytree(source / name, destination / name)
    (destination / 'data/pilot_lab_results.json').write_text(
        json.dumps(pilot_summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (destination / 'deployment.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest

if __name__ == '__main__':
    print(json.dumps(build(ROOT / '_site'), indent=2))
