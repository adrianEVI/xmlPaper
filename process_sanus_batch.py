import os
import sys
import asyncio
import pypandoc
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

from main import (
    extract_metadata_from_text,
    extract_docx_headers_text,
    extract_structured_abstracts_from_body,
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
    build_ref_list_xml,
    process_eng_docx_to_subarticle,
    extract_authors_and_affiliations_from_docx,
    format_xml_with_tabs
)

async def convert_docx_file_to_xml(input_path: str, eng_input_path: str = None) -> str:
    print(f"  [1/6] Convirtiendo DOCX a JATS HTML/XML con Pandoc...", flush=True)
    xml_output = pypandoc.convert_file(
        input_path, 
        to='jats', 
        format='docx', 
        extra_args=['--standalone']
    )
    
    soup = BeautifulSoup(xml_output, 'xml')
    header_text = extract_docx_headers_text(input_path)
    raw_text = header_text + "\n" + soup.get_text(separator='\n', strip=True)
    
    if eng_input_path and os.path.exists(eng_input_path):
        try:
            import docx
            eng_doc = docx.Document(eng_input_path)
            eng_front_paras = [p.text.strip() for p in eng_doc.paragraphs[:40] if p.text.strip()]
            raw_text = "\n".join(eng_front_paras) + "\n\n" + raw_text
        except Exception as e:
            print(f"  [AVISO] No se pudo leer portada de {eng_input_path}: {e}")

    print(f"  [2/6] Extrayendo metadatos con Gemini (incluyendo encabezados DOCX: DOI, volumen, número)...", flush=True)
    metadata, used_fallback = await extract_metadata_from_text(raw_text)
    
    det_authors, det_affs = extract_authors_and_affiliations_from_docx(eng_input_path or input_path)
    if det_authors:
        print(f"  [2.5/6] Aplicando metadatos deterministas de autores ({len(det_authors)} autores con roles/ORCID/xrefs)...", flush=True)
        metadata.authors = det_authors
        if det_affs:
            metadata.affiliations = det_affs

    extract_structured_abstracts_from_body(soup, metadata)
    
    print(f"  [3/6] Construyendo sección <front> según SciELO SPS...", flush=True)
    old_front = soup.find('front')
    scielo_front = build_scielo_front(soup, metadata)
    
    if old_front:
        old_front.replace_with(scielo_front)
    elif soup.article:
        soup.article.insert(0, scielo_front)
        
    print(f"  [4/6] Limpiando metadatos duplicados, estructurando <sec>, <fig> y notas al pie...", flush=True)
    clean_body_duplicate_metadata(soup, metadata)
    restructure_body_to_sections(soup)
    extract_structured_abstracts_from_body(soup, metadata)
    clean_phantom_sections(soup)
    format_figures(soup)
    from docx_table_parser import build_jats_table_from_docx, sanitize_named_content_and_local_paths
    sanitize_named_content_and_local_paths(soup)
    build_jats_table_from_docx(input_path, soup)
    format_tables(soup)
    format_sections(soup)
    auto_link_cross_references(soup)
    fix_footnotes(soup)
    
    for fn in soup.find_all('fn'):
        if not fn.has_attr('fn-type'):
            fn['fn-type'] = "other"
            
    print(f"  [5/6] Extrayendo y parseando bibliografía con Gemini...", flush=True)
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
        
    if eng_input_path and os.path.exists(eng_input_path):
        print(f"  [5.5/6] Procesando versión en Inglés ({os.path.basename(eng_input_path)}) y construyendo <sub-article>...", flush=True)
        sub_art_tag = process_eng_docx_to_subarticle(soup, eng_input_path, metadata)
        if soup.article:
            old_sub = soup.article.find('sub-article')
            if old_sub:
                old_sub.decompose()
            soup.article.append(sub_art_tag)
            
        # Re-construir front principal para reflejar título, abstract y keywords en inglés recién extraídos
        scielo_front_updated = build_scielo_front(soup, metadata)
        old_front = soup.find('front')
        if old_front:
            old_front.replace_with(scielo_front_updated)
        elif soup.article:
            soup.article.insert(0, scielo_front_updated)

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
    
    import re
    final_xml = str(soup)
    try:
        final_xml = format_xml_with_tabs(final_xml)
    except Exception as e:
        print(f"  [AVISO] No se pudo formatear XML con tabuladores: {e}")
        final_xml = re.sub(r'<\?xml.*?\?>\n?', '', final_xml)
        final_xml = re.sub(r'<!DOCTYPE.*?>\n?', '', final_xml)
        doctype = '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
        final_xml = f'<?xml version="1.0" encoding="utf-8"?>\n{doctype}\n{final_xml.strip()}'
    
    print(f"  [6/6] XML final generado correctamente.", flush=True)
    return final_xml

async def main():
    base_dir = os.path.abspath("Articulos/SANUS")
    input_dir = os.path.join(base_dir, "SANUSdocx")
    output_dir = os.path.join(base_dir, "SANUSxmlNEW")
    
    os.makedirs(output_dir, exist_ok=True)
    
    all_files = os.listdir(input_dir)
    esp_files = [f for f in all_files if f.endswith(".docx") and "ESP" in f and not f.startswith("~$")]
    esp_files.sort()
    
    print(f"==================================================", flush=True)
    print(f"Iniciando procesamiento de {len(esp_files)} artículos combinados (_ESP.docx + _ENG.docx)", flush=True)
    print(f"Carpeta origen: {input_dir}", flush=True)
    print(f"Carpeta destino: {output_dir}", flush=True)
    print(f"==================================================", flush=True)
    
    # Mapping table for full SciELO name format if applicable
    scielo_map = {
        "549_ESP.docx": "2448-6094-sanus-10-21-e549.xml",
        "560_ESP.docx": "2448-6094-sanus-10-21-e560.xml",
        "561_ESP.docx": "2448-6094-sanus-10-21-e561.xml",
        "564_ESP.docx": "2448-6094-sanus-10-21-e564.xml",
        "566_ESP.docx": "2448-6094-sanus-10-21-e566.xml",
        "573_ESP.docx": "2448-6094-sanus-10-21-e573.xml"
    }

    for idx, filename in enumerate(esp_files, 1):
        print(f"\n[{idx}/{len(esp_files)}] Procesando: {filename}", flush=True)
        in_path = os.path.join(input_dir, filename)
        eng_filename = filename.replace("_ESP.docx", "_ENG.docx")
        eng_path = os.path.join(input_dir, eng_filename)
        if not os.path.exists(eng_path):
            eng_path = None
            
        try:
            xml_content = await convert_docx_file_to_xml(in_path, eng_input_path=eng_path)
            
            # Save standard name
            out_filename_std = filename.replace(".docx", ".xml")
            out_path_std = os.path.join(output_dir, out_filename_std)
            with open(out_path_std, "w", encoding="utf-8") as out_f:
                out_f.write(xml_content)
            print(f"  [OK] Guardado como: {out_filename_std}", flush=True)
            
            # Save full SciELO format name if mapped
            if filename in scielo_map:
                scielo_name = scielo_map[filename]
                out_path_scielo = os.path.join(output_dir, scielo_name)
                with open(out_path_scielo, "w", encoding="utf-8") as out_f:
                    out_f.write(xml_content)
                print(f"  [OK] Guardado como (SciELO format): {scielo_name}", flush=True)
                
            await asyncio.sleep(1) # Breve pausa entre llamadas para evitar saturación de API
            
        except Exception as e:
            print(f"  [ERROR] Procesando '{filename}': {e}", flush=True)
            import traceback
            traceback.print_exc()

    print("\n==================================================", flush=True)
    print("¡Procesamiento finalizado con éxito!", flush=True)
    print("==================================================", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
