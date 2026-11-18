import docx
import re
import xml.etree.ElementTree as ET

def extract_docx_headers_text(docx_path):
    doc = docx.Document(docx_path)
    header_texts = []
    for s in doc.sections:
        for h in (s.first_page_header, s.header):
            if h and h._element is not None:
                # Parse all text elements inside header XML
                root = ET.fromstring(h._element.xml)
                texts = [elem.text for elem in root.iter() if elem.text and elem.text.strip()]
                if texts:
                    header_texts.append(" ".join(texts))
    return "\n".join(header_texts)

for f in ["549_ESP.docx", "560_ESP.docx", "561_ESP.docx", "564_ESP.docx", "566_ESP.docx", "573_ESP.docx"]:
    path = f"Articulos/SANUS/SANUSdocx/{f}"
    print(f"=== Header for {f} ===")
    print(extract_docx_headers_text(path))
    print()
