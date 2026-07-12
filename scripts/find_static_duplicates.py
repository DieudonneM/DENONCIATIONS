"""
Script pour trouver les fichiers statiques dupliqués dans le workspace.
Usage: python scripts/find_static_duplicates.py
"""
import os
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ignore_dirs = {'staticfiles', 'venv', '.git'}

files_map = defaultdict(list)

for dirpath, dirnames, filenames in os.walk(ROOT):
    # Skip ignored directories
    parts = set(dirpath.split(os.sep))
    if parts & ignore_dirs:
        continue
    # We only care about directories named 'static' or any subdirs within them
    if os.path.sep + 'static' + os.path.sep in os.path.join(os.sep, os.path.relpath(dirpath, ROOT) + os.sep):
        for f in filenames:
            rel_dir = os.path.relpath(dirpath, os.path.join(ROOT))
            # compute path relative to the nearest 'static' directory
            # find the index of '/static/' in the rel path
            rel = os.path.relpath(os.path.join(dirpath, f), ROOT)
            # path under static root: take piece after '/static/'
            try:
                idx = rel.index(os.path.join('static', ''))
                key = rel[idx + len(os.path.join('static', '')):]
            except ValueError:
                # file directly inside a 'static' dir without trailing slash
                parts = rel.split(os.path.join('static', ''))
                key = parts[-1]
            files_map[key].append(rel)

# Find duplicates
duplicates = {k: v for k, v in files_map.items() if len(v) > 1}

if not duplicates:
    print('Aucun fichier statique dupliqué trouvé.')
else:
    print(f'Trouvé {len(duplicates)} fichiers statiques dupliqués:\n')
    for key, paths in sorted(duplicates.items()):
        print(f'- {key}')
        for p in paths:
            print(f'    - {p}')
    print('\nConseil: consolidez ou renommez les fichiers pour éviter conflits lors de collectstatic.')
