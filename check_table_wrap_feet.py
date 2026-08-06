import os
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

sanus_dir = os.path.abspath("Articulos/SANUS/SANUSxmlNEW")
files = [f for f in os.listdir(sanus_dir) if f.endswith('.xml')]

print("=== INSPECCION DETALLADA DE <table-wrap-foot> EN TODOS LOS ARCHIVOS XML ===\n")

for fname in files:
    fpath = os.path.join(sanus_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'xml')
        
    feet = soup.find_all('table-wrap-foot')
    print(f"*** {fname}: {len(feet)} <table-wrap-foot> encontrados ***")
    for idx, foot in enumerate(feet, 1):
        parent_tbl = foot.find_parent('table-wrap')
        tbl_id = parent_tbl.get('id') if parent_tbl else 'SIN_PARENT'
        foot_id = foot.get('id')
        children_tags = [c.name for c in foot.children if c.name]
        
        # Details of fn or attrib inside foot
        fns = foot.find_all('fn')
        fn_details = [f"fn(id={f.get('id')}, fn-type={f.get('fn-type')})" for f in fns]
        attribs = foot.find_all('attrib')
        attrib_details = [a.get_text(strip=True)[:40] for a in attribs]
        ps = foot.find_all('p', recursive=False)
        p_details = [p.get_text(strip=True)[:40] for p in ps]
        
        text_snippet = foot.get_text(strip=True)[:80]
        print(f"   [{idx}] Parent table id: {tbl_id} | foot id: {foot_id}")
        print(f"       Children: {children_tags}")
        if fn_details: print(f"       Footnotes: {fn_details}")
        if attrib_details: print(f"       Attribs: {attrib_details}")
        if p_details: print(f"       Direct Ps: {p_details}")
        print(f"       Texto: \"{text_snippet}...\"\n")
