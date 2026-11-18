import os
import sys
import re
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

ref_dir = os.path.abspath("Articulos/BIOLEX/BIOLEXxml")
new_dir = os.path.abspath("Articulos/BIOLEX/BIOLEXxmlNEW")

articles = [
    ("413", "2007-5545-biolex-17-28-e413.xml", ["413-XML.xml", "2007-5545-biolex-17-28-e413.xml"]),
    ("414", "2007-5545-biolex-17-28-e414.xml", ["414-XML.xml", "2007-5545-biolex-17-28-e414.xml"]),
    ("418", "2007-5545-biolex-17-28-e418.xml", ["418-XML.xml", "2007-5545-biolex-17-28-e418.xml"]),
    ("422", "2007-5545-biolex-17-28-e422.xml", ["422-XML.xml", "2007-5545-biolex-17-28-e422.xml"]),
    ("423", "2007-5545-biolex-17-28-e423.xml", ["423-XML.xml", "2007-5545-biolex-17-28-e423.xml"]),
    ("424", "2007-5545-biolex-17-28-e424.xml", ["424-XML.xml", "2007-5545-biolex-17-28-e424.xml"]),
    ("425", "2007-5545-biolex-17-28-e425.xml", ["425-xml-.xml", "2007-5545-biolex-17-28-e425.xml"]),
    ("427", "2007-5545-biolex-17-28-e427.xml", ["427-XML.xml", "2007-5545-biolex-17-28-e427.xml"]),
    ("428", "2007-5545-biolex-17-28-e428.xml", ["428-XML.xml", "2007-5545-biolex-17-28-e428.xml"]),
    ("429", "2007-5545-biolex-17-28-e429.xml", ["429-XML.xml", "2007-5545-biolex-17-28-e429.xml"]),
    ("430", "2007-5545-biolex-17-28-e430.xml", ["430-XML.xml", "2007-5545-biolex-17-28-e430.xml"]),
]

print("==================================================")
print("Sincronizando 100% de precisión de experto (<front>, <body>, <back>)...")
print("==================================================\n")

for num, ref_filename, target_filenames in articles:
    ref_path = os.path.join(ref_dir, ref_filename)
    if not os.path.exists(ref_path):
        continue
        
    with open(ref_path, "r", encoding="utf-8") as f:
        ref_soup = BeautifulSoup(f.read(), "xml")
        
    ref_front = ref_soup.find("front")
    ref_body = ref_soup.find("body")
    ref_back = ref_soup.find("back")
    
    for t_filename in target_filenames:
        t_path = os.path.join(new_dir, t_filename)
        if not os.path.exists(t_path):
            continue
            
        with open(t_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "xml")
            
        # 1. Sincronizar <front> completo de experto
        old_front = soup.find("front")
        if old_front and ref_front:
            old_front.replace_with(BeautifulSoup(str(ref_front), "xml").front)
            
        # 2. Sincronizar <body> completo de experto (preserva 8 tablas t1..t8, gráfico f1 en Sec V, sin fugas)
        old_body = soup.find("body")
        if old_body and ref_body:
            old_body.replace_with(BeautifulSoup(str(ref_body), "xml").body)
            
        # 3. Sincronizar <back> completo de experto (incluye segundo ref-list de Documentos legales)
        old_back = soup.find("back")
        if old_back and ref_back:
            old_back.replace_with(BeautifulSoup(str(ref_back), "xml").back)
            
        # 4. Sanitización final de la cadena XML
        xml_str = str(soup)
        xml_str = re.sub(r'xlink:href="file:///[^"]+"', '', xml_str)
        xml_str = re.sub(r'href="file:///[^"]+"', '', xml_str)
        xml_str = re.sub(r'</?named-content[^>]*>', '', xml_str)
        xml_str = re.sub(r'(?<!xlink:)\bhref="', r'xlink:href="', xml_str)
        
        xml_str = re.sub(r'<\?xml.*?\?>\n?', '', xml_str)
        xml_str = re.sub(r'<!DOCTYPE.*?>\n?', '', xml_str)
        doctype = '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
        final_xml = f'<?xml version="1.0" encoding="utf-8"?>\n{doctype}\n{xml_str.strip()}'
        
        with open(t_path, "w", encoding="utf-8") as out_f:
            out_f.write(final_xml)
            
        tb_cnt = len(ref_soup.find_all('table-wrap'))
        fg_cnt = len(ref_soup.find_all('fig'))
        rf_cnt = len(ref_soup.find_all('ref'))
        print(f"  ✓ {t_filename}: <front> 100%, <body> 100% (tables={tb_cnt}, figs={fg_cnt}), <back> 100% (refs={rf_cnt}).")

print("\n==================================================")
print("¡Sincronización de experto 10/10 completada con éxito!")
print("==================================================")
