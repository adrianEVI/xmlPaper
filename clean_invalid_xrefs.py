import os
import re
from bs4 import BeautifulSoup

def fix_xrefs_in_file(xml_path):
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'xml')
    valid_ref_ids = set(r['id'] for r in soup.find_all('ref') if r.has_attr('id'))

    modified = False

    # 1. Unwrap any xref inside ref-list, ref, mixed-citation, element-citation, label
    for ref_parent in soup.find_all(['ref-list', 'ref', 'mixed-citation', 'element-citation', 'label']):
        for xr in list(ref_parent.find_all('xref')):
            xr.unwrap()
            modified = True

    # 2. Unwrap any bibr xref whose rid is not in valid_ref_ids
    for xr in list(soup.find_all('xref', {'ref-type': 'bibr'})):
        rid = xr.get('rid')
        if not rid or rid not in valid_ref_ids:
            xr.unwrap()
            modified = True

    if modified:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"[CLEANED] {xml_path}")
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
                    fix_xrefs_in_file(os.path.join(full_d, fname))

if __name__ == "__main__":
    main()
