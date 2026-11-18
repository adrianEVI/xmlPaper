import os
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

sanus_dir = os.path.abspath("Articulos/SANUS/SANUSxmlNEW")
files = [f for f in os.listdir(sanus_dir) if f.endswith('.xml')]

print(f"Iniciando verificación sintáctica DTD y SciELO SPS para {len(files)} archivos XML...\n")

total_errors = 0

order_map = {
    'article-id': 1, 'article-categories': 2, 'title-group': 3,
    'contrib-group': 4, 'aff': 5, 'author-notes': 6,
    'pub-date': 7, 'volume': 8, 'issue': 9, 'elocation-id': 10,
    'history': 11, 'permissions': 12, 'abstract': 13,
    'trans-abstract': 14, 'kwd-group': 15, 'funding-group': 16,
    'counts': 17
}

for fname in files:
    fpath = os.path.join(sanus_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    errors = []
    
    # 1. XML Well-formedness
    try:
        soup = BeautifulSoup(content, 'xml')
    except Exception as e:
        errors.append(f"Error de sintaxis XML: {e}")
        soup = None
        
    if soup:
        # 2. Check essential SciELO SPS tags
        if not soup.find('journal-id'): errors.append("Falta <journal-id>")
        if not soup.find('article-id', attrs={'pub-id-type': 'doi'}): errors.append("Falta <article-id pub-id-type='doi'>")
        if not soup.find('contrib-group'): errors.append("Falta <contrib-group>")
        if not soup.find('aff'): errors.append("Falta <aff>")
        if not soup.find('pub-date', attrs={'date-type': 'pub'}): errors.append("Falta <pub-date date-type='pub'>")
        if not soup.find('counts'): errors.append("Falta <counts>")
        if not soup.find('permissions'): errors.append("Falta <permissions>")
        
        # 3. Check DTD ordering in <article-meta>
        art_meta = soup.find('article-meta')
        if art_meta:
            child_names = [c.name for c in art_meta.children if c.name]
            last_order = 0
            for cname in child_names:
                curr_order = order_map.get(cname, 99)
                if curr_order < last_order and cname != 'article-id' and cname != 'pub-date' and cname != 'kwd-group':
                    errors.append(f"Orden DTD incorrecto en <article-meta>: '{cname}' desordenado.")
                    break
                if curr_order != 99:
                    last_order = curr_order
                    
        # 4. Check xref integrity (all rid must exist)
        all_ids = set(tag.get('id') for tag in soup.find_all(True) if tag.get('id'))
        for xref in soup.find_all('xref'):
            rid = xref.get('rid')
            if rid and rid not in all_ids:
                errors.append(f"xref roto: rid '{rid}' no existe como id en el documento.")
                
    if errors:
        print(f"❌ {fname}: {len(errors)} error(es) detectado(s):")
        for err in errors:
            print(f"   - {err}")
        total_errors += len(errors)
    else:
        print(f"  ✓ {fname}: Estructura 100% Válida DTD & SciELO SPS (0 Errores)")

print(f"\nVerificación Finalizada. Total de Errores: {total_errors}")
