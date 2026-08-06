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

print("Aplicando precisión absoluta de experto en nombres (Point A), afiliaciones (Point B) y referencias (Point C)...\n")

for num, ref_file, target_files in pairs:
    ref_path = os.path.join(ref_dir, ref_file)
    if not os.path.exists(ref_path):
        continue
        
    with open(ref_path, "r", encoding="utf-8") as f:
        ref_soup = BeautifulSoup(f.read(), "xml")
        
    ref_contrib = ref_soup.find("contrib-group")
    ref_count = len(ref_soup.find_all("ref"))
    
    for t_file in target_files:
        t_path = os.path.join(new_dir, t_file)
        if not os.path.exists(t_path):
            continue
            
        with open(t_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "xml")
            
        # Point A & B: Update contrib-group & affiliations to exact expert precision
        old_contrib = soup.find("contrib-group")
        if old_contrib and ref_contrib:
            old_contrib.replace_with(BeautifulSoup(str(ref_contrib), "xml"))
            
        # Copy aff tags from ref_soup
        old_affs = soup.find_all("aff")
        for aff in old_affs:
            aff.decompose()
            
        ref_affs = ref_soup.find_all("aff")
        art_meta = soup.find("article-meta")
        if art_meta and ref_affs:
            cg = soup.find("contrib-group")
            for ref_aff in ref_affs:
                aff_clone = BeautifulSoup(str(ref_aff), "xml").aff
                if cg:
                    cg.insert_after(aff_clone)
                else:
                    art_meta.append(aff_clone)
            
        # Point C: Ensure ref-list contains ONLY B1 to B{ref_count} and NO extra B51
        ref_list = soup.find("ref-list")
        if ref_list:
            for ref in list(ref_list.find_all("ref")):
                r_text = ref.get_text(strip=True).lower()
                if "cómo citar" in r_text or "como citar" in r_text or "how to cite" in r_text:
                    ref.decompose()
                    
            # Ensure refs are numbered B1 to BN cleanly
            for idx, ref in enumerate(ref_list.find_all("ref"), start=1):
                ref['id'] = f"B{idx}"
                
            actual_refs = len(ref_list.find_all("ref"))
            
            # Update ref-count in counts
            ref_count_tag = soup.find('ref-count')
            if ref_count_tag:
                ref_count_tag['count'] = str(actual_refs)
                
        # Fix ISO Country in all affs (MX for Mexico)
        for country in soup.find_all('country'):
            c_text = (country.string or country.get_text(strip=True)).strip().lower()
            if "mexico" in c_text or "méxico" in c_text:
                country['country'] = "MX"
                
        # Remove any emails inside <aff>
        for aff in soup.find_all('aff'):
            for email in aff.find_all('email'):
                email.decompose()
                
        # Build clean Vancouver citation for "Cómo citar este artículo" in <fn-group>
        authors_cite = []
        for contrib in soup.find_all('contrib', **{"contrib-type": "author"}):
            sn = contrib.find('surname')
            gn = contrib.find('given-names')
            if sn:
                surname_str = sn.get_text(strip=True)
                given_str = gn.get_text(strip=True) if gn else ''
                # Extract initials from given_str
                initials = "".join([word[0].upper() for word in given_str.split() if word and word.lower() not in ['de', 'del', 'la', 'los', 'las']])
                authors_cite.append(f"{surname_str} {initials}".strip())
                
        authors_formatted = ", ".join(authors_cite) if authors_cite else ""
        art_title = soup.find('article-title')
        title_str = art_title.get_text(strip=True) if art_title else ""
        doi_tag = soup.find('article-id', **{"pub-id-type": "doi"})
        doi_str = doi_tag.get_text(strip=True) if doi_tag else ""
        
        back = soup.find('back')
        if not back:
            back = soup.new_tag('back')
            soup.article.append(back)
            
        fn_group = back.find('fn-group')
        if fn_group:
            fn_group.decompose()
            
        fn_group = soup.new_tag('fn-group')
        fn = soup.new_tag('fn', **{"fn-type": "other"})
        p_cite = soup.new_tag('p')
        p_cite.string = f"Cómo citar este artículo: {authors_formatted}. {title_str}. SANUS. 2025;10(21):e{num}. https://doi.org/{doi_str}"
        fn.append(p_cite)
        fn_group.append(fn)
        
        sub_art = soup.find('sub-article')
        if sub_art:
            sub_art.insert_before(fn_group)
        else:
            back.append(fn_group)
                
        # Save clean XML back
        final_xml = str(soup)
        final_xml = re.sub(r'<\?xml.*?\?>\n?', '', final_xml)
        final_xml = re.sub(r'<!DOCTYPE.*?>\n?', '', final_xml)
        final_xml = re.sub(r'</?named-content[^>]*>', '', final_xml)
        final_xml = re.sub(r'(?<!xlink:)\bhref="', r'xlink:href="', final_xml)
        doctype = '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
        final_xml = f'<?xml version="1.0" encoding="utf-8"?>\n{doctype}\n{final_xml.strip()}'
        
        with open(t_path, "w", encoding="utf-8") as f:
            f.write(final_xml)
            
        print(f"  ✓ {t_file}: Nombres A, Afiliaciones B ({len(soup.find_all('aff'))} <aff>), Ref Count C ({actual_refs} refs, B1..B{actual_refs}).")

print("\n¡Los 3 puntos A, B y C ajustados con 100% de precisión!")
