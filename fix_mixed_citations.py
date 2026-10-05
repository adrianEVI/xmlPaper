import os
import re
from bs4 import BeautifulSoup

def clean_mixed_citations(xml_path):
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'xml')
    modified = False

    for mc in soup.find_all('mixed-citation'):
        # 1. Unwrap <comment> tags inside <mixed-citation>
        comments = list(mc.find_all('comment'))
        if comments:
            modified = True
            for comm in comments:
                comm.unwrap()

        # 2. Unwrap <ext-link> if text inside is not a URL / DOI
        ext_links = list(mc.find_all('ext-link'))
        for ext in ext_links:
            txt = ext.get_text(strip=True)
            href = ext.get('xlink:href', '')
            if not (txt.startswith(('http://', 'https://', 'ftp://', 'www.', 'doi.org', '10.')) or (href and href == txt)):
                modified = True
                ext.unwrap()

    # Clean raw duplicate strings
    content = content.replace("Disponible en: Disponible en:", "Disponible en:")
    soup = BeautifulSoup(content, 'xml')

    if modified:
        new_xml = str(soup)
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(new_xml)
        print(f"[FIXED] {xml_path}")
    else:
        print(f"[OK] {xml_path}")

def main():
    dirs = [
        "Articulos/SANUS/SANUSxml",
        "Articulos/SANUS/SANUSxmlNEW"
    ]
    for d in dirs:
        full_d = os.path.abspath(d)
        if os.path.exists(full_d):
            for fname in os.listdir(full_d):
                if fname.endswith(".xml"):
                    clean_mixed_citations(os.path.join(full_d, fname))

if __name__ == "__main__":
    main()
