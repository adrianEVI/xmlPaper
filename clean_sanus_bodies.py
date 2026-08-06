import os
import sys
import re
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

sanus_xml_dir = os.path.abspath("Articulos/SANUS/SANUSxmlNEW")

keywords_to_remove = [
    "investigación", "revisión", "caso clínico", "artículo de investigación",
    "experiencias de jóvenes universitarios ante realización de prueba rápida de vih",
    "experiences of young university students with rapid hiv testing",
    "experiências de jovens universitários com o teste rápido de hiv",
    "efectividad de la auriculoterapia para reducción del estrés",
    "eficácia da auriculoterapia na redução do estresse",
    "effectiveness of auriculotherapy in reducing stress",
    "asociación de estilos parentales y violencia de pareja",
    "proceso de enfermería a persona con choque séptico",
    "relación de la percepción materna y conductas alimentarias"
]

print("Depurando residuo de metadatos al inicio del <body> en SANUSxmlNEW...\n")

for filename in os.listdir(sanus_xml_dir):
    if not filename.endswith(".xml"):
        continue
        
    filepath = os.path.join(sanus_xml_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "xml")
        
    body = soup.find('body')
    if not body:
        continue
        
    # Purge any top-level nodes in body preceding the true Introducción section
    for child in list(body.children):
        if not hasattr(child, 'get_text'):
            continue
            
        # If it's a section with sec-type="intro" or title "Introducción", we stop purging
        if child.name == 'sec':
            stype = child.get('sec-type')
            sid = child.get('id', '')
            title_text = child.find('title').get_text(strip=True).lower() if child.find('title') else ''
            if stype == 'intro' or sid == 'introducción' or title_text in ['introducción', 'introduccion']:
                break
                
        # Decompose all duplicate header/abstract nodes preceding main text
        if hasattr(child, 'decompose'):
            child.decompose()
        elif hasattr(child, 'extract'):
            child.extract()
            

        
    # Save clean XML back
    final_xml = str(soup)
    final_xml = re.sub(r'<\?xml.*?\?>\n?', '', final_xml)
    final_xml = re.sub(r'<!DOCTYPE.*?>\n?', '', final_xml)
    doctype = '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
    final_xml = f'<?xml version="1.0" encoding="utf-8"?>\n{doctype}\n{final_xml.strip()}'
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_xml)
        
    print(f"  ✓ {filename}: <body> depurado sin residuos de encabezado ni listas duplicadas.")

print("\n¡Depuración del <body> completada exitosamente!")
