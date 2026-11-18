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
    fix_section_title_case,
    auto_link_cross_references,
    fix_footnotes,
    extract_bibliography_paragraphs,
    parse_references_with_gemini,
    build_ref_list_xml
)

async def convert_biolex_docx_to_xml(input_path: str) -> tuple[str, str, str, dict]:
    filename = os.path.basename(input_path)
    print(f"  [1/6] Convirtiendo DOCX a JATS HTML/XML con Pandoc: {filename}...", flush=True)
    
    xml_output = pypandoc.convert_file(
        input_path, 
        to='jats', 
        format='docx', 
        extra_args=['--standalone']
    )
    
    soup = BeautifulSoup(xml_output, 'xml')
    header_text = extract_docx_headers_text(input_path)
    raw_text = header_text + "\n" + soup.get_text(separator='\n', strip=True)
    
    print(f"  [2/6] Extrayendo metadatos del documento...", flush=True)
    metadata, used_fallback = await extract_metadata_from_text(raw_text)
    
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
    fix_section_title_case(soup)
    auto_link_cross_references(soup)
    fix_footnotes(soup)
    
    for fn in soup.find_all('fn'):
        if not fn.has_attr('fn-type'):
            fn['fn-type'] = "other"
            
    print(f"  [5/6] Extrayendo y estructurando bibliografía...", flush=True)
    raw_ref_nodes, ref_section_title = extract_bibliography_paragraphs(soup)
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
        ref_list_tag = build_ref_list_xml(soup, parsed_references, raw_ref_nodes, ref_section_title)
        back.append(ref_list_tag)
        
    if soup.article:
        soup.article['xmlns:mml'] = "http://www.w3.org/1998/Math/MathML"
        soup.article['xmlns:xlink'] = "http://www.w3.org/1999/xlink"
        soup.article['article-type'] = "research-article"
        soup.article['dtd-version'] = "1.1"
        soup.article['specific-use'] = "sps-1.9"
        soup.article['xml:lang'] = metadata.language if metadata.language else "es"
    
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
    
    for tag in soup.find_all(True):
        if tag.has_attr('xlink:href'):
            if tag['xlink:href'].startswith('file:'):
                if tag.name == 'ext-link':
                    tag.unwrap()
                else:
                    del tag['xlink:href']
        if tag.has_attr('href'):
            tag['xlink:href'] = tag['href']
            del tag['href']
            
    final_xml = str(soup)
    final_xml = re.sub(r'<\?xml.*?\?>\n?', '', final_xml)
    final_xml = re.sub(r'<!DOCTYPE.*?>\n?', '', final_xml)
    
    doctype = '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
    final_xml = f'<?xml version="1.0" encoding="utf-8"?>\n{doctype}\n{final_xml.strip()}'
    
    from main import validate_sps
    validation_report = validate_sps(final_xml)
    
    issn_slug = metadata.issn_epub or metadata.issn or metadata.issn_ppub or "issn"
    j_slug = metadata.journal_id or "journal"
    vol_slug = metadata.volume or "vol"
    iss_slug = metadata.issue or "num"
    eloc_slug = metadata.elocation_id or "art"
    scielo_filename = f"{issn_slug}-{j_slug}-{vol_slug}-{iss_slug}-{eloc_slug}.xml"
    
    num_match = re.search(r'(\d+)', filename)
    art_num = num_match.group(1) if num_match else "000"
    
    print(f"  [6/6] XML final generado para {filename} (SPS Válido: {validation_report['is_valid']}, Errores: {len(validation_report['errors'])})", flush=True)
    return final_xml, art_num, scielo_filename, validation_report

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
            xml_content, art_num, scielo_name, validation_report = await convert_biolex_docx_to_xml(in_path)
            
            # Guardar con el nombre base reemplazando .docx por .xml (1 archivo por DOCX)
            out_filename_std = filename.replace(".docx", ".xml")
            out_path_std = os.path.join(output_dir, out_filename_std)
            with open(out_path_std, "w", encoding="utf-8") as out_f:
                out_f.write(xml_content)
            print(f"  [OK] Guardado: {out_filename_std} (SPS Válido: {validation_report['is_valid']})", flush=True)
            
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
