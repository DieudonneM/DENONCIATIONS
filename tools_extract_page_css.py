from pathlib import Path
import re

workspace = Path(r'c:/Users/dmuhe/Documents/DJANGO/denunciations_app')


def slugify(parts):
    return '_'.join(re.sub(r'[^a-zA-Z0-9]+', '_', p).strip('_').lower() for p in parts)

html_files = []
html_files.extend((workspace / 'core/templates').rglob('*.html'))
html_files.extend((workspace / 'users/templates').rglob('*.html'))
html_files.append(workspace / 'core/dashboard.html')

for path in sorted(set(html_files)):
    if not path.exists():
        continue
    text = path.read_text(encoding='utf-8')
    if '<style' not in text:
        continue

    style_blocks = list(re.finditer(r'<style\b[^>]*>(.*?)</style>', text, re.S | re.I))
    if not style_blocks:
        continue

    css_content = '\n\n'.join(m.group(1).strip() for m in style_blocks if m.group(1).strip())

    rel = path.relative_to(workspace)
    if path.name == 'dashboard.html' and path.parent == workspace / 'core':
        css_rel = Path('core/static/css/dashboard.css')
        css_link = "{% static 'css/dashboard.css' %}"
    elif rel.parts[0] == 'core' and rel.parts[1] == 'templates':
        parts = rel.parts[2:-1]  # directory path without file name
        filename = rel.stem
        css_name = slugify(parts + (filename,))
        css_rel = Path('core/static/css') / f'{css_name}.css'
        css_link = "{% static 'css/" + css_rel.name + "' %}"
    elif rel.parts[0] == 'users' and rel.parts[1] == 'templates':
        parts = rel.parts[2:-1]
        filename = rel.stem
        css_name = slugify(parts + (filename,))
        css_rel = Path('users/static/users/css') / f'{css_name}.css'
        css_link = "{% static 'users/css/" + css_rel.name + "' %}"
    else:
        continue

    css_rel.parent.mkdir(parents=True, exist_ok=True)
    css_rel.write_text(css_content.rstrip() + '\n', encoding='utf-8')

    new_text = text
    for block in reversed(style_blocks):
        new_text = new_text[:block.start()] + new_text[block.end():]

    if '{% block extra_css %}' in new_text:
        if css_link not in new_text:
            new_text = new_text.replace('{% block extra_css %}{% endblock %}', '{% block extra_css %}\n    <link rel="stylesheet" href="' + css_link + '">\n{% endblock %}', 1)
    else:
        title_match = re.search(r'\{%\s*block title[^%]*%\}(.*?)\{%\s*endblock\s*%\}', new_text, re.S)
        if title_match:
            insert_after = title_match.end()
            block_html = "\n\n{% block extra_css %}\n    <link rel=\"stylesheet\" href=\"" + css_link + "\">\n{% endblock %}\n"
            new_text = new_text[:insert_after] + block_html + new_text[insert_after:]
        else:
            new_text = new_text.replace('{% load static %}\n', '{% load static %}\n\n{% block extra_css %}\n    <link rel=\"stylesheet\" href=\"' + css_link + '\">\n{% endblock %}\n', 1)

    new_text = re.sub(r'\n{3,}', '\n\n', new_text)
    path.write_text(new_text, encoding='utf-8')
    print(f'processed {path} -> {css_rel}')
