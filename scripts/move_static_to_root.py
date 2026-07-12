"""
Déplace les fichiers statiques depuis les dossiers d'app (*/static/*) vers static/{css,img,js} à la racine du projet.
Usage: python scripts/move_static_to_root.py
"""
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / 'static'
CSS = DEST / 'css'
IMG = DEST / 'img'
JS = DEST / 'js'

for d in (CSS, IMG, JS):
    d.mkdir(parents=True, exist_ok=True)

moved = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip virtualenv, git, and the destination static folder
    if any(part in ('venv', '.git', 'staticfiles') for part in Path(dirpath).parts):
        continue
    # look for a 'static' folder in the path
    parts = Path(dirpath).parts
    if 'static' not in parts:
        continue
    # skip files already under project-level static
    if Path(dirpath).resolve().is_relative_to(DEST.resolve()):
        continue

    for fname in filenames:
        src = Path(dirpath) / fname
        # decide destination based on folder name in path or file extension
        lower = src.name.lower()
        if any(p == 'css' for p in parts):
            dst = CSS / src.name
        elif any(p == 'js' for p in parts):
            dst = JS / src.name
        else:
            # treat as image/other
            dst = IMG / src.name

        # avoid overwriting existing file at destination: if exists, keep existing and skip
        if dst.exists():
            moved.append((str(src), str(dst), 'skipped (exists)'))
            try:
                src.unlink()
            except Exception:
                pass
            continue

        try:
            shutil.move(str(src), str(dst))
            moved.append((str(src), str(dst), 'moved'))
        except Exception as e:
            moved.append((str(src), str(dst), f'error: {e}'))

# remove empty static directories under apps
for dirpath, dirnames, filenames in os.walk(ROOT, topdown=False):
    p = Path(dirpath)
    if p == DEST or p == ROOT:
        continue
    if 'static' in p.parts:
        try:
            # if directory empty after moves, remove
            if not any(p.iterdir()):
                p.rmdir()
        except Exception:
            pass

print('Moved files:')
for m in moved:
    print(m[0], '->', m[1], m[2])

print('\nDone.')
