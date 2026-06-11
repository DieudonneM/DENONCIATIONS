import urllib.request
import re

with urllib.request.urlopen('http://127.0.0.1:8000/') as r:
    html = r.read().decode()
    # Find the logo img tag
    img_tags = re.findall(r'<img[^>]*>', html)
    for tag in img_tags:
        print(tag)
    # Try to fetch the logo
    if 'logo_ministere.png' in html:
        print('\nLogo tag found in HTML')
        # Extract the src
        match = re.search(r'src=["\']([^"\']+logo_ministere[^"\']*)["\']', html)
        if match:
            logo_url = match.group(1)
            print(f'Logo URL: {logo_url}')
            # Make the URL absolute
            if not logo_url.startswith('http'):
                logo_url = 'http://127.0.0.1:8000' + logo_url
            print(f'Absolute URL: {logo_url}')
            try:
                with urllib.request.urlopen(logo_url) as r2:
                    print(f'Logo status: {r2.status}')
            except Exception as e:
                print(f'Error accessing logo: {e}')
