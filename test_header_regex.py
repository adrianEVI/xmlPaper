import docx
import re

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
    
    vol_iss_match = re.search(r';\s*(\d+)\s*\(\s*(\d+)\s*\)\s*:\s*(e?\d+)', full_xml)
    vol = vol_iss_match.group(1) if vol_iss_match else None
    iss = vol_iss_match.group(2) if vol_iss_match else None
    eloc = vol_iss_match.group(3) if vol_iss_match else None
    
    return {'doi': doi, 'volume': vol, 'issue': iss, 'elocation_id': eloc}

files = ['549_ESP.docx', '560_ESP.docx', '561_ESP.docx', '564_ESP.docx', '566_ESP.docx', '573_ESP.docx']
for f in files:
    path = f'Articulos/SANUS/SANUSdocx/{f}'
    print(f"{f:15} -> {parse_header_metadata(path)}")
