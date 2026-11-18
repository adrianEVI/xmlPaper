import os
import sys
import re
import docx
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

def parse_header_metadata(docx_path):
    doc = docx.Document(docx_path)
    header_xmls = []
    for s in doc.sections:
        for h in (s.first_page_header, s.header):
            if h and h._element is not None:
                header_xmls.append(h._element.xml)
    full_xml = ' '.join(header_xmls)
    
    doi_match = re.search(r'10\.\d{4,9}/[^\s<"\']+', full_xml)
    doi = doi_match.group(0).rstrip('.') if doi_match else None
    
    # E-location ID matching
    eloc_match = re.search(r':\s*(e\d+)', full_xml, re.IGNORECASE)
    eloc = eloc_match.group(1) if eloc_match else None
    if not eloc:
        # Fallback from filename
        fn = os.path.basename(docx_path)
        num = re.search(r'\d+', fn)
        if num:
            eloc = f"e{num.group(0)}"
            
    return {'doi': doi, 'volume': "10", 'issue': "21", 'elocation_id': eloc}

sanus_docx_dir = os.path.abspath("Articulos/SANUS/SANUSdocx")
sanus_xml_dir = os.path.abspath("Articulos/SANUS/SANUSxmlNEW")

# Map of expert publisher IDs
other_ids = {
    "549": "00113",
    "560": "00304",
    "561": "00112",
    "564": "00111",
    "566": "00202",
    "573": "00110"
}

files = [
    ("549", "549_ESP.docx", "549_ESP.xml", "2448-6094-sanus-10-21-e549-NEW.xml"),
    ("560", "560_ESP.docx", "560_ESP.xml", "2448-6094-sanus-10-21-e560-NEW.xml"),
    ("561", "561_ESP.docx", "561_ESP.xml", "2448-6094-sanus-10-21-e561-NEW.xml"),
    ("564", "564_ESP.docx", "564_ESP.xml", "2448-6094-sanus-10-21-e564-NEW.xml"),
    ("566", "566_ESP.docx", "566_ESP.xml", "2448-6094-sanus-10-21-e566-NEW.xml"),
    ("573", "573_ESP.docx", "573_ESP.xml", "2448-6094-sanus-10-21-e573-NEW.xml"),
]

print("Actualizando metadatos de encabezado (DOI, volumen, número, elocation-id) en los XMLs de SANUSxmlNEW...\n")

for art_num, docx_f, xml_f1, xml_f2 in files:
    docx_path = os.path.join(sanus_docx_dir, docx_f)
    meta = parse_header_metadata(docx_path)
    pub_other = other_ids.get(art_num, "00000")
    
    for xml_name in [xml_f1, xml_f2]:
        xml_path = os.path.join(sanus_xml_dir, xml_name)
        if not os.path.exists(xml_path):
            continue
            
        with open(xml_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "xml")
            
        # Update DOI
        doi_tag = soup.find("article-id", **{"pub-id-type": "doi"})
        if doi_tag and meta["doi"]:
            doi_tag.string = meta["doi"]
            
        # Update Other ID
        other_tag = soup.find("article-id", **{"pub-id-type": "other"})
        if other_tag:
            other_tag.string = pub_other
            
        # Update Volume & Issue
        vol_tag = soup.find("volume")
        if not vol_tag:
            vol_tag = soup.new_tag("volume")
            article_meta = soup.find("article-meta")
            if article_meta: article_meta.append(vol_tag)
        vol_tag.string = "10"
        
        iss_tag = soup.find("issue")
        if not iss_tag:
            iss_tag = soup.new_tag("issue")
            article_meta = soup.find("article-meta")
            if article_meta: article_meta.append(iss_tag)
        iss_tag.string = "21"
        
        # Update Elocation-id
        eloc_tag = soup.find("elocation-id")
        if eloc_tag and meta["elocation_id"]:
            eloc_tag.string = meta["elocation_id"]
            
        # Clean ref-list DOIs
        for pub_id in soup.find_all("pub-id", **{"pub-id-type": "doi"}):
            if pub_id.string:
                clean_ref_doi = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', pub_id.string.strip(), flags=re.IGNORECASE)
                clean_ref_doi = re.sub(r'^doi:\s*', '', clean_ref_doi, flags=re.IGNORECASE)
                pub_id.string = clean_ref_doi
            
        # Save back
        final_xml = str(soup)
        final_xml = re.sub(r'<\?xml.*?\?>\n?', '', final_xml)
        final_xml = re.sub(r'<!DOCTYPE.*?>\n?', '', final_xml)
        
        doctype = '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
        final_xml = f'<?xml version="1.0" encoding="utf-8"?>\n{doctype}\n{final_xml.strip()}'
        
        with open(xml_path, "w", encoding="utf-8") as out_f:
            out_f.write(final_xml)
            
        print(f"  ✓ {xml_name}: DOI={meta['doi']}, elocation={meta['elocation_id']}, pub-id={pub_other}")

print("\n¡Metadatos de encabezado actualizados exitosamente en todos los XMLs!")
