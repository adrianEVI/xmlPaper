import os
from bs4 import BeautifulSoup
import re

sanus_dir = os.path.abspath("Articulos/SANUS/SANUSxml")
new_dir = os.path.abspath("Articulos/SANUS/SANUSxmlNEW")

pairs = [
    ("549", "2448-6094-sanus-10-21-e549.xml", "2448-6094-sanus-10-21-e549-NEW.xml", "549_ESP.xml"),
    ("560", "2448-6094-sanus-10-21-e560.xml", "2448-6094-sanus-10-21-e560-NEW.xml", "560_ESP.xml"),
    ("561", "2448-6094-sanus-10-21-e561.xml", "2448-6094-sanus-10-21-e561-NEW.xml", "561_ESP.xml"),
    ("564", "2448-6094-sanus-10-21-e564.xml", "2448-6094-sanus-10-21-e564-NEW.xml", "564_ESP.xml"),
    ("566", "2448-6094-sanus-10-21-e566.xml", "2448-6094-sanus-10-21-e566-NEW.xml", "566_ESP.xml"),
    ("573", "2448-6094-sanus-10-21-e573.xml", "2448-6094-sanus-10-21-e573-NEW.xml", "573_ESP.xml"),
]

def find_new_file(f1, f2):
    p1 = os.path.join(new_dir, f1)
    if os.path.exists(p1):
        return p1
    p2 = os.path.join(new_dir, f2)
    if os.path.exists(p2):
        return p2
    # Find any matching file in new_dir containing the number
    num = f1.split('e')[-1].split('.')[0] if 'e' in f1 else f2.split('_')[0]
    for fn in os.listdir(new_dir):
        if num in fn:
            return os.path.join(new_dir, fn)
    raise FileNotFoundError(f"No file found for {f1} or {f2}")

def analyze_pair(article_id, ref_file, new_f1, new_f2):
    ref_path = os.path.join(sanus_dir, ref_file)
    new_path = find_new_file(new_f1, new_f2)
    
    with open(ref_path, "r", encoding="utf-8") as f:
        ref_soup = BeautifulSoup(f.read(), "xml")
        
    with open(new_path, "r", encoding="utf-8") as f:
        new_soup = BeautifulSoup(f.read(), "xml")
        
    report = []
    report.append(f"### Artículo {article_id} (`{ref_file}` vs `{os.path.basename(new_path)}`)")
    
    # 1. Front Meta Comparison
    report.append("#### 1. Encabezado Metadatos (`<front>`)")
    
    # DOI & IDs
    ref_doi = ref_soup.find('article-id', **{'pub-id-type': 'doi'})
    new_doi = new_soup.find('article-id', **{'pub-id-type': 'doi'})
    ref_doi_str = ref_doi.text if ref_doi else 'N/A'
    new_doi_str = new_doi.text if new_doi else 'N/A'
    report.append(f"- **DOI**: Experto=`{ref_doi_str}` | Generado=`{new_doi_str}`")
    
    ref_other = ref_soup.find('article-id', **{'pub-id-type': 'other'})
    new_other = new_soup.find('article-id', **{'pub-id-type': 'other'})
    ref_other_str = ref_other.text if ref_other else 'N/A'
    new_other_str = new_other.text if new_other else 'N/A'
    report.append(f"- **ID Publisher/Other**: Experto=`{ref_other_str}` | Generado=`{new_other_str}`")

    # Titles
    ref_title = ref_soup.find('article-title')
    new_title = new_soup.find('article-title')
    report.append(f"- **Título (ES)**: Experto=`{ref_title.text[:60] if ref_title else 'N/A'}...` | Generado=`{new_title.text[:60] if new_title else 'N/A'}...`")

    ref_trans_title = ref_soup.find('trans-title')
    new_trans_title = new_soup.find('trans-title')
    report.append(f"- **Título (EN)**: Experto=`{ref_trans_title.text[:60] if ref_trans_title else 'N/A'}...` | Generado=`{new_trans_title.text[:60] if new_trans_title else 'N/A'}...`")

    # Portuguese title
    ref_pt_title = ref_soup.find('trans-title-group', **{'xml:lang': 'pt'})
    new_pt_title = new_soup.find('trans-title-group', **{'xml:lang': 'pt'})
    pt_status_ref = ref_pt_title.find('trans-title').text if ref_pt_title and ref_pt_title.find('trans-title') else 'No existe'
    pt_status_new = new_pt_title.find('trans-title').text if new_pt_title and new_pt_title.find('trans-title') else 'No existe'
    report.append(f"- **Título en Portugués (PT)**: Experto=`{pt_status_ref[:40]}...` | Generado=`{pt_status_new}`")

    # Authors & Affiliations
    ref_authors = ref_soup.find_all('contrib', **{'contrib-type': 'author'})
    new_authors = new_soup.find_all('contrib', **{'contrib-type': 'author'})
    report.append(f"- **Número de Autores**: Experto=`{len(ref_authors)}` | Generado=`{len(new_authors)}`")
    
    # Check author ORCIDs and roles
    ref_orcids = [c.find('contrib-id').text for c in ref_authors if c.find('contrib-id')]
    new_orcids = [c.find('contrib-id').text for c in new_authors if c.find('contrib-id')]
    report.append(f"- **ORCIDs de Autores**: Experto={len(ref_orcids)}/{len(ref_authors)} | Generado={len(new_orcids)}/{len(new_authors)}")

    ref_roles = [c.find('role').text for c in ref_authors if c.find('role')]
    new_roles = [c.find('role').text for c in new_authors if c.find('role')]
    report.append(f"- **Roles de Autores**: Experto={len(ref_roles)}/{len(ref_authors)} (`{ref_roles[:2]}`) | Generado={len(new_roles)}/{len(new_authors)} (`{new_roles[:2]}`)")

    ref_affs = ref_soup.find_all('aff')
    new_affs = new_soup.find_all('aff')
    report.append(f"- **Afiliaciones (`<aff>`)**: Experto=`{len(ref_affs)}` | Generado=`{len(new_affs)}`")
    
    # Dates
    ref_received = ref_soup.find('date', **{'date-type': 'received'})
    new_received = new_soup.find('date', **{'date-type': 'received'})
    ref_rec_str = f"{ref_received.find('year').text}-{ref_received.find('month').text}-{ref_received.find('day').text}" if ref_received and ref_received.find('year') and ref_received.find('month') and ref_received.find('day') else 'N/A'
    new_rec_str = f"{new_received.find('year').text}-{new_received.find('month').text}-{new_received.find('day').text}" if new_received and new_received.find('year') and new_received.find('month') and new_received.find('day') else 'N/A'
    report.append(f"- **Fecha Recepción**: Experto=`{ref_rec_str}` | Generado=`{new_rec_str}`")

    ref_accepted = ref_soup.find('date', **{'date-type': 'accepted'})
    new_accepted = new_soup.find('date', **{'date-type': 'accepted'})
    ref_acc_str = f"{ref_accepted.find('year').text}-{ref_accepted.find('month').text}-{ref_accepted.find('day').text}" if ref_accepted and ref_accepted.find('year') and ref_accepted.find('month') and ref_accepted.find('day') else 'N/A'
    new_acc_str = f"{new_accepted.find('year').text}-{new_accepted.find('month').text}-{new_accepted.find('day').text}" if new_accepted and new_accepted.find('year') and new_accepted.find('month') and new_accepted.find('day') else 'N/A'
    report.append(f"- **Fecha Aceptación**: Experto=`{ref_acc_str}` | Generado=`{new_acc_str}`")

    # 2. Body Structure Comparison
    report.append("\n#### 2. Estructura del Cuerpo (`<body>`)")
    ref_body = ref_soup.find('body')
    new_body = new_soup.find('body')
    
    ref_secs = ref_body.find_all('sec') if ref_body else []
    new_secs = new_body.find_all('sec') if new_body else []
    report.append(f"- **Secciones (`<sec>`)**: Experto=`{len(ref_secs)}` | Generado=`{len(new_secs)}`")

    ref_sec_types = [s.get('sec-type') for s in ref_secs if s.get('sec-type')]
    new_sec_types = [s.get('sec-type') for s in new_secs if s.get('sec-type')]
    report.append(f"- **Tipos de Sección (`sec-type`)**: Experto=`{ref_sec_types}` | Generado=`{new_sec_types}`")

    ref_figs = ref_body.find_all('fig') if ref_body else []
    new_figs = new_body.find_all('fig') if new_body else []
    report.append(f"- **Figuras (`<fig>`)**: Experto=`{len(ref_figs)}` | Generado=`{len(new_figs)}`")

    ref_tables = ref_body.find_all('table-wrap') if ref_body else []
    new_tables = new_body.find_all('table-wrap') if new_body else []
    report.append(f"- **Tablas (`<table-wrap>`)**: Experto=`{len(ref_tables)}` | Generado=`{len(new_tables)}`")

    # 3. References Comparison
    report.append("\n#### 3. Referencias Bibliográficas (`<ref-list>`)")
    ref_refs = ref_soup.find_all('ref')
    new_refs = new_soup.find_all('ref')
    report.append(f"- **Total de Referencias**: Experto=`{len(ref_refs)}` | Generado=`{len(new_refs)}`")
    
    ref_elem_pubtypes = [e.get('publication-type') for e in ref_soup.find_all('element-citation') if e.get('publication-type')]
    new_elem_pubtypes = [e.get('publication-type') for e in new_soup.find_all('element-citation') if e.get('publication-type')]
    from collections import Counter
    report.append(f"- **Tipos de Publicación Citas (Experto)**: {dict(Counter(ref_elem_pubtypes))}")
    report.append(f"- **Tipos de Publicación Citas (Generado)**: {dict(Counter(new_elem_pubtypes))}")

    # Specific missing/extra tags in element-citation
    ref_dois = len([e for e in ref_soup.find_all('pub-id', **{'pub-id-type': 'doi'})])
    new_dois = len([e for e in new_soup.find_all('pub-id', **{'pub-id-type': 'doi'})])
    report.append(f"- **DOIs en Referencias**: Experto=`{ref_dois}` | Generado=`{new_dois}`")

    return "\n".join(report)

print("Analizando diferencias 1 a 1 entre SANUSxml y SANUSxmlNEW...\n")
full_analysis = []
for art_id, ref_f, new_f1, new_f2 in pairs:
    res = analyze_pair(art_id, ref_f, new_f1, new_f2)
    print(res)
    print("\n" + "="*60 + "\n")
    full_analysis.append(res)

with open("analysis_summary.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(full_analysis))
