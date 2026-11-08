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
    from .validate_recipes import validate_from_files as validate_recipes
    from .verify_recipe_demos import verify_from_files as verify_recipe_demos
else:
    from validate_research_briefs import validate_from_files
    from validate_adoption import validate_from_files as validate_adoption
    from pilot_lab import run_from_files as run_pilot
    from validate_recipes import validate_from_files as validate_recipes
    from verify_recipe_demos import verify_from_files as verify_recipe_demos

ROOT = Path(__file__).resolve().parents[1]
FILES = ('index.html', 'top30.html', 'project.html', 'blueprints.html', 'network.html', 'adoption.html', 'pilot-lab.html', 'recipes.html', 'demos.html', 'mission-studio.html', 'mission-engine.js', 'semantic-studio.html', 'semantic-core.js', 'semantic-worker.js', 'runtime-evidence.html', 'README.md', 'LICENSE')
DIRECTORIES = ('data', 'docs')
EXAMPLE_SUBDIRS = ('consent_lead_triage', 'recipe_demos')

def build(destination, source=ROOT, commit=None):
    destination, source = Path(destination).resolve(), Path(source).resolve()
    if destination == source or source.is_relative_to(destination):
        raise ValueError('Destination must not contain the source repository')
    for name in (*FILES, *DIRECTORIES, *(str(Path('examples') / x) for x in EXAMPLE_SUBDIRS)):
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
    recipe_summary = validate_recipes(source)
    demo_results = verify_recipe_demos(source)
    # Public runtime exhibit is excerpted from an actual independent SDK/Graph CI.
    # It is not a live task API, nor a claim of production agent execution.
    case = json.loads((source / 'data/agent_runtime_public_case_v20.json').read_text())
    deny = json.loads((source / 'data/agent_runtime_public_denial_v20.json').read_text())
    if (case.get('schema_version') != 1 or case.get('scenario') != 'education'
        or case.get('status') != 'LOCAL_APPROVED_RESEARCH_REPORT_NOT_DEPLOYED'
        or case.get('real_neural_executed') is not True
        or case.get('real_langgraph_sqlite_interrupt') is not True
        or len(case.get('selected', [])) != 4
        or case.get('scope', {}).get('outbound_business_actions') != 0
        or case.get('scope', {}).get('orders') != 0
        or deny.get('status') != 'BLOCK: declined'
        or deny.get('generated_reports') != 0
        or deny.get('real_orders') != 0
        or case.get('evidence_origin', {}).get('run_id') != deny.get('evidence_origin', {}).get('run_id')):
        raise ValueError('Actual agent runtime exhibit contract broken')
    if case.get('source_sha256') != {
        n.removeprefix('data/').removesuffix('.json'): __import__('hashlib').sha256((source / n).read_bytes()).hexdigest()
        for n in ('data/curated.json', 'data/repo_metadata.json', 'data/research_briefs.json')
    }:
        raise ValueError('Actual neural runtime exhibit has stale or forged input hashes')
    curated_by_repo = {x['repo']: x for x in curated}
    if any(x.get('source_url') != 'https://github.com/' + x.get('repo', '')
           or x.get('repo') not in curated_by_repo
           or x['source_url'] != curated_by_repo[x['repo']]['url']
           or not isinstance(x.get('similarity_cosine'), (float, int))
           or not x.get('blockers')
           for x in case['selected']):
        raise ValueError('Runtime sample contains fabricated sources or unknown audit blockers')
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
        'recipe_count': recipe_summary['recipes_count'],
        'recipe_curated_tool_count': recipe_summary['unique_curated_tool_refs'],
        'recipe_verified_integrations': recipe_summary['verified_integrations'],
        'recipe_demo_count': len(demo_results['scenarios']),
        'recipe_demo_contract_passed': demo_results['all_passed'],
        'recipe_demo_upstream_integrations': demo_results['verified_3rd_party_integrations'],
        'interactive_demo_count': 3,
        'interactive_demo_runtime': 'client-side first-party synthetic JavaScript',
        'interactive_demo_third_party_integrations': 0,
        'mission_studio_enabled': True,
        'mission_studio_curated_candidates': len(curated),
        'mission_studio_source_briefs': research_summary['count'],
        'mission_studio_runtime': 'browser-local deterministic source matching',
        'mission_studio_verified_integrations': 0,
        'semantic_studio_enabled': True,
        'semantic_studio_scope': 'opt-in local pretrained embeddings only',
        'semantic_studio_candidate_cap': 32,
        'semantic_studio_user_model_consent_required': True,
        'semantic_studio_remote_inference_calls': 0,
        'semantic_studio_verified_agent_integrations': 0,
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
    for name in EXAMPLE_SUBDIRS:
        shutil.copytree(source / 'examples' / name, destination / 'examples' / name)
    (destination / 'data/recipe_demo_results.json').write_text(
        json.dumps(demo_results, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    (destination / 'data/pilot_lab_results.json').write_text(
        json.dumps(pilot_summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (destination / 'deployment.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest

if __name__ == '__main__':
    print(json.dumps(build(ROOT / '_site'), indent=2))
