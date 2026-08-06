import os
import sys
import re
import asyncio
import pypandoc
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

from main import (
    extract_metadata_from_text,
    extract_docx_headers_text,
    build_scielo_front,
    clean_body_duplicate_metadata,
    restructure_body_to_sections,
    clean_phantom_sections,
    format_figures,
    format_tables,
    format_sections,
    auto_link_cross_references,
    fix_footnotes,
    extract_bibliography_paragraphs,
    parse_references_with_gemini,
    build_ref_list_xml
)

async def convert_biolex_docx_to_xml(input_path: str) -> tuple[str, str, str]:
    filename = os.path.basename(input_path)
    print(f"  [1/6] Convirtiendo DOCX a JATS HTML/XML con Pandoc: {filename}...", flush=True)
    
    # Extraer el número de artículo del nombre de archivo (ej. 413-XML.docx -> 413, 425-xml-.docx -> 425)
    num_match = re.search(r'(\d+)', filename)
    art_num = num_match.group(1) if num_match else "000"
    default_eloc = f"e{art_num}"
    
    xml_output = pypandoc.convert_file(
        input_path, 
        to='jats', 
        format='docx', 
        extra_args=['--standalone']
    )
    
    soup = BeautifulSoup(xml_output, 'xml')
    header_text = extract_docx_headers_text(input_path)
    raw_text = header_text + "\n" + soup.get_text(separator='\n', strip=True)
    
    print(f"  [2/6] Extrayendo metadatos con Gemini...", flush=True)
    metadata = await extract_metadata_from_text(raw_text)
    
    # Enforzar metadatos estándar de la revista BIOLEX
    metadata.journal_id = "biolex"
    metadata.journal_title = "Biolex"
    metadata.issn = "2007-5545"
    metadata.publisher_name = "Universidad de Sonora, División de Ciencias Sociales"
    if not metadata.volume:
        metadata.volume = "17"
    if not metadata.issue:
        metadata.issue = "28"
    if not metadata.elocation_id or metadata.elocation_id == "e000":
        metadata.elocation_id = default_eloc
        
    print(f"  [3/6] Construyendo sección <front> según SciELO SPS...", flush=True)
    old_front = soup.find('front')
    scielo_front = build_scielo_front(soup, metadata)
    
    if old_front:
        old_front.replace_with(scielo_front)
    elif soup.article:
        soup.article.insert(0, scielo_front)
        
    print(f"  [4/6] Limpiando metadatos duplicados, estructurando <sec>, <fig>, <table> y notas al pie...", flush=True)
    from docx_table_parser import build_jats_table_from_docx, sanitize_named_content_and_local_paths
    sanitize_named_content_and_local_paths(soup)
    clean_body_duplicate_metadata(soup, metadata)
    restructure_body_to_sections(soup)
    clean_phantom_sections(soup)
    format_figures(soup)
    build_jats_table_from_docx(input_path, soup)
    format_tables(soup)
    format_sections(soup)
    auto_link_cross_references(soup)
    fix_footnotes(soup)
    
    for fn in soup.find_all('fn'):
        if not fn.has_attr('fn-type'):
            fn['fn-type'] = "other"
            
    print(f"  [5/6] Extrayendo y parseando bibliografía con Gemini...", flush=True)
    raw_ref_nodes = extract_bibliography_paragraphs(soup)
    parsed_references = await parse_references_with_gemini(raw_ref_nodes)
    
    back = soup.find('back')
    if not back:
        back = soup.new_tag('back')
        if soup.article:
            soup.article.append(back)
            
    if back:
        old_ref_list = back.find('ref-list')
        if old_ref_list:
            old_ref_list.decompose()
        ref_list_tag = build_ref_list_xml(soup, parsed_references, raw_ref_nodes)
        back.append(ref_list_tag)
        
    if soup.article:
        soup.article['xmlns:mml'] = "http://www.w3.org/1998/Math/MathML"
        soup.article['xmlns:xlink'] = "http://www.w3.org/1999/xlink"
        soup.article['article-type'] = "research-article"
        soup.article['dtd-version'] = "1.1"
        soup.article['specific-use'] = "sps-1.9"
        soup.article['xml:lang'] = "es"
    
    rc = soup.find('ref-count')
    if rc:
        rc['count'] = str(len(soup.find_all('ref')))
        
    tc = soup.find('table-count')
    if tc:
        tc['count'] = str(len(soup.find_all('table-wrap')))
        
    fc = soup.find('fig-count')
    if fc:
        fc['count'] = str(len(soup.find_all('fig')))
        
    ec = soup.find('equation-count')
    if ec:
        ec['count'] = str(len(soup.find_all('disp-formula')))
    
    # Limpiar DOIs en bibliografía
    for pub_id in soup.find_all("pub-id", **{"pub-id-type": "doi"}):
        if pub_id.string:
            clean_ref_doi = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', pub_id.string.strip(), flags=re.IGNORECASE)
            clean_ref_doi = re.sub(r'^doi:\s*', '', clean_ref_doi, flags=re.IGNORECASE)
            pub_id.string = clean_ref_doi
    
    final_xml = str(soup)
    final_xml = re.sub(r'<\?xml.*?\?>\n?', '', final_xml)
    final_xml = re.sub(r'<!DOCTYPE.*?>\n?', '', final_xml)
    
    # Recomendación 3: Inactivar la extracción de rutas locales (file:///)
    final_xml = re.sub(r'(?:xlink:href|href)="file:///[^"]+"', '', final_xml)
    final_xml = re.sub(r'file:///[^\s<"\']+', '', final_xml)
    
    doctype = '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
    final_xml = f'<?xml version="1.0" encoding="utf-8"?>\n{doctype}\n{final_xml.strip()}'
    
    scielo_filename = f"2007-5545-biolex-{metadata.volume}-{metadata.issue}-{metadata.elocation_id}.xml"
    
    print(f"  [6/6] XML final generado correctamente para {filename} (SciELO name: {scielo_filename})", flush=True)
    return final_xml, art_num, scielo_filename

async def main():
    base_dir = os.path.abspath("Articulos/BIOLEX")
    input_dir = os.path.join(base_dir, "BIOLEXdocx")
    output_dir = os.path.join(base_dir, "BIOLEXxmlNEW")
    
    os.makedirs(output_dir, exist_ok=True)
    
    all_files = [f for f in os.listdir(input_dir) if f.endswith(".docx") and not f.startswith("~$")]
    all_files.sort()
    
    print(f"==================================================", flush=True)
    print(f"Iniciando procesamiento de {len(all_files)} artículos DOCX de BIOLEX", flush=True)
    print(f"Carpeta origen: {input_dir}", flush=True)
    print(f"Carpeta destino: {output_dir}", flush=True)
    print(f"==================================================", flush=True)
    
    for idx, filename in enumerate(all_files, 1):
        in_path = os.path.join(input_dir, filename)
        out_filename_std = filename.replace(".docx", ".xml")
        out_path_std = os.path.join(output_dir, out_filename_std)
        
        if os.path.exists(out_path_std) and "--force" not in sys.argv:
            print(f"\n[{idx}/{len(all_files)}] Omitiendo (Ya procesado): {filename}", flush=True)
            continue
            
        print(f"\n[{idx}/{len(all_files)}] Procesando: {filename}", flush=True)
        
        try:
            xml_content, art_num, scielo_name = await convert_biolex_docx_to_xml(in_path)
            
            # Guardar con el nombre base reemplazando .docx por .xml
            out_filename_std = filename.replace(".docx", ".xml")
            out_path_std = os.path.join(output_dir, out_filename_std)
            with open(out_path_std, "w", encoding="utf-8") as out_f:
                out_f.write(xml_content)
            print(f"  [OK] Guardado como: {out_filename_std}", flush=True)
            
            # Guardar también con el formato oficial SciELO (ej. 2007-5545-biolex-17-28-e413.xml)
            out_path_scielo = os.path.join(output_dir, scielo_name)
            with open(out_path_scielo, "w", encoding="utf-8") as out_f:
                out_f.write(xml_content)
            print(f"  [OK] Guardado como (SciELO format): {scielo_name}", flush=True)
            
            # Pausa breve entre llamados a API
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"  [ERROR] Procesando '{filename}': {e}", flush=True)
            import traceback
            traceback.print_exc()

    print("\n==================================================", flush=True)
    print("¡Procesamiento de BIOLEX finalizado con éxito!", flush=True)
    print("==================================================", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
