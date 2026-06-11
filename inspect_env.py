from pathlib import Path

p = Path(r'C:/Users/dmuhe/Documents/DJANGO/denunciations_app/.env')
raw = p.read_bytes()
print('len', len(raw))
print('head', raw[:160])
print('high bytes', [(i, hex(b), b) for i, b in enumerate(raw) if b >= 0x80])
print('decoded UTF-8 replace:')
print(raw.decode('utf-8', errors='replace'))
