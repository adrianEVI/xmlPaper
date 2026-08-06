import os
import sys
import re
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

ref_dir = os.path.abspath("Articulos/SANUS/SANUSxml")
new_dir = os.path.abspath("Articulos/SANUS/SANUSxmlNEW")

pairs = [
    ("549", "2448-6094-sanus-10-21-e549.xml", ["549_ESP.xml", "2448-6094-sanus-10-21-e549-NEW.xml"]),
    ("560", "2448-6094-sanus-10-21-e560.xml", ["560_ESP.xml", "2448-6094-sanus-10-21-e560-NEW.xml"]),
    ("561", "2448-6094-sanus-10-21-e561.xml", ["561_ESP.xml", "2448-6094-sanus-10-21-e561-NEW.xml"]),
    ("564", "2448-6094-sanus-10-21-e564.xml", ["564_ESP.xml", "2448-6094-sanus-10-21-e564-NEW.xml"]),
    ("566", "2448-6094-sanus-10-21-e566.xml", ["566_ESP.xml", "2448-6094-sanus-10-21-e566-NEW.xml"]),
    ("573", "2448-6094-sanus-10-21-e573.xml", ["573_ESP.xml", "2448-6094-sanus-10-21-e573-NEW.xml"]),
]

print("Solucionando 'Cómo citar' (Issue A) y añadiendo <sub-article> traducido (Issue B)...\n")

for num, ref_file, target_files in pairs:
    ref_path = os.path.join(ref_dir, ref_file)
    if not os.path.exists(ref_path):
        print(f"  ✗ No se encontró archivo de referencia {ref_file}")
        continue
        
    with open(ref_path, "r", encoding="utf-8") as f:
        ref_soup = BeautifulSoup(f.read(), "xml")
        
    sub_article_node = ref_soup.find("sub-article")
    
    for t_file in target_files:
        t_path = os.path.join(new_dir, t_file)
        if not os.path.exists(t_path):
            continue
            
        with open(t_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "xml")
            
        # --- ISSUE A FIX: Format <fn-group> "Cómo citar" cleanly with spaces ---
        back = soup.find('back')
        if not back:
            back = soup.new_tag('back')
            soup.article.append(back)
            
        fn_group = back.find('fn-group')
        if fn_group:
            fn_group.decompose() # Rebuild cleanly
            
        fn_group = soup.new_tag('fn-group')
        fn = soup.new_tag('fn', **{"fn-type": "other"})
        p_cite = soup.new_tag('p')
        
        # Build clean citation text with proper spaces between authors
        ref_list = soup.find('ref-list')
        how_to_cite_ref = None
        if ref_list:
            for ref in list(ref_list.find_all('ref')):
                txt = ref.get_text(separator=' ', strip=True)
                if "cómo citar" in txt.lower() or "como citar" in txt.lower() or "how to cite" in txt.lower():
                    ref.decompose()
                    
        # Extract title and authors cleanly from <front>
        art_title = soup.find('article-title')
        title_str = art_title.get_text(strip=True) if art_title else ""
        authors = []
        for contrib in soup.find_all('contrib', **{"contrib-type": "author"}):
            sn = contrib.find('surname')
            gn = contrib.find('given-names')
            if sn:
                authors.append(f"{sn.get_text(strip=True)} {gn.get_text(strip=True) if gn else ''}".strip())
                
        authors_str = ", ".join(authors) if authors else "Autores del artículo"
        doi_tag = soup.find('article-id', **{"pub-id-type": "doi"})
        if doi_tag:
            doi_val = doi_tag.get_text(strip=True)
            doi_val = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', doi_val)
            doi_tag.string = doi_val
            doi_str = doi_val
        else:
            doi_str = f"10.36789/sanusrevenf.vi21.{num}"
            
        doi_url = doi_str if doi_str.startswith("http") else f"https://doi.org/{doi_str}"
        formatted_cite = f"Cómo citar este artículo: {authors_str}. {title_str}. SANUS. 2025;10(21):e{num}. {doi_url}"
        p_cite.string = formatted_cite
        fn.append(p_cite)
        fn_group.append(fn)
        back.append(fn_group)

        # Set official article-id pub-id-type="other"
        order_map = {"549": "00113", "560": "00112", "561": "00304", "564": "00111", "566": "00202", "573": "00110"}
        if num in order_map:
            other_id = soup.find('article-id', **{"pub-id-type": "other"})
            if not other_id:
                other_id = soup.new_tag('article-id', **{"pub-id-type": "other"})
                if doi_tag:
                    doi_tag.insert_after(other_id)
                else:
                    soup.find('article-meta').append(other_id)
            other_id.string = order_map[num]
        
        # --- ISSUE B FIX: Add <sub-article article-type="translation" xml:lang="en"> ---
        if sub_article_node:
            existing_sub = soup.find('sub-article')
            if existing_sub:
                existing_sub.decompose()
            soup.article.append(BeautifulSoup(str(sub_article_node), 'xml'))
            
        # Save back
        final_xml = str(soup)
        final_xml = re.sub(r'<\?xml.*?\?>\n?', '', final_xml)
        final_xml = re.sub(r'<!DOCTYPE.*?>\n?', '', final_xml)
        doctype = '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
        final_xml = f'<?xml version="1.0" encoding="utf-8"?>\n{doctype}\n{final_xml.strip()}'
        
        with open(t_path, "w", encoding="utf-8") as f:
            f.write(final_xml)
            
        print(f"  ✓ {t_file}: Cita 'Cómo citar' formateada limpiamente + <sub-article> en inglés añadido.")

print("\n¡Ambos inconvenientes A y B solucionados exitosamente!")
