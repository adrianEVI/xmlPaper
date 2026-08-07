import os
import sys
import re
import docx
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.text.paragraph import Paragraph
from docx.table import Table
from bs4 import BeautifulSoup
from bs4.element import Tag

sys.stdout.reconfigure(encoding='utf-8')

def sanitize_named_content_and_local_paths(soup: BeautifulSoup) -> BeautifulSoup:
    """
    B. Desactiva y elimina de forma absoluta todas las marcas de resaltado/revisión de Word (<named-content content-type="mark">)
    y limpia cualquier ruta de archivo local (file:///).
    """
    for nc in list(soup.find_all('named-content')):
        nc.unwrap()
            
    for ext in soup.find_all(['ext-link', 'email', 'graphic', 'inline-graphic']):
        for attr in ['xlink:href', 'href']:
            if ext.has_attr(attr):
                val = ext[attr]
                if val.startswith('file:///'):
                    clean_val = re.sub(r'^file:///[^\s]+', '', val)
                    if clean_val:
                        ext[attr] = clean_val
                    else:
                        del ext[attr]
                        
    return soup

def split_long_paragraph(text, max_len=110):
    if len(text) <= max_len:
        return [text]
    words = text.split(' ')
    chunks = []
    curr = ''
    for w in words:
        if curr and (len(curr) + 1 + len(w) > max_len):
            chunks.append(curr.strip())
            curr = w
        else:
            curr = (curr + ' ' + w).strip() if curr else w
    if curr:
        chunks.append(curr.strip())
    return chunks

def split_text_into_n_chunks(text, n):
    if n <= 1 or len(text) < 40:
        return [text]
    parts = re.split(r'(r/c|m/p|,|;|\.)', text)
    tokens = []
    i = 0
    while i < len(parts):
        token = parts[i]
        if i + 1 < len(parts) and parts[i+1] in ['r/c', 'm/p', ',', ';', '.']:
            token += parts[i+1]
            i += 1
        if token.strip():
            tokens.append(token.strip())
        i += 1
        
    target_len = max(35, len(text) // n)
    chunks = []
    curr = ''
    for t in tokens:
        if curr and (len(curr) + len(t) > target_len) and len(chunks) < n - 1:
            chunks.append(curr.strip())
            curr = t
        else:
            curr = (curr + ' ' + t).strip() if curr else t
    if curr:
        chunks.append(curr.strip())
    return chunks

def build_jats_table_from_docx(docx_path: str, soup: BeautifulSoup) -> BeautifulSoup:
    """
    A. Recorre secuencialmente doc.element.body de python-docx para detectar elementos w:tbl.
    Genera el nodo estandarizado JATS <table-wrap id="t1"> con <label>, <caption>, <table>, <tbody>, <tr>, <td>
    y <table-wrap-foot><attrib>Fuente: ...</attrib></table-wrap-foot>.
    """
    if not os.path.exists(docx_path):
        return soup

    doc = docx.Document(docx_path)
    body_tag = soup.find('body')
    if not body_tag:
        return soup

    # Primero sanitizar <named-content>
    soup = sanitize_named_content_and_local_paths(soup)

    table_counter = 1
    docx_tables = []
    
    # Extraer las tablas nativas de Word con sus encabezados y fuentes circundantes
    elements = list(doc.element.body)
    for idx, elem in enumerate(elements):
        if isinstance(elem, CT_Tbl):
            tbl = Table(elem, doc)
            
            # Buscar título en el párrafo anterior si existe (ej. "Tabla 1. Contrastiva...")
            tbl_label = f"Tabla {table_counter}"
            tbl_title = f"Tabla {table_counter}"
            if idx > 0 and isinstance(elements[idx - 1], CT_P):
                prev_p = Paragraph(elements[idx - 1], doc)
                prev_text = prev_p.text.strip()
                match = re.search(r'^(Tabla|Table)\s*(\d*)[\.\s:\-]*(.*)', prev_text, re.IGNORECASE)
                if match:
                    num_str = match.group(2) if match.group(2) else str(table_counter)
                    tbl_label = f"{match.group(1).capitalize()} {num_str}"
                    if match.group(3).strip():
                        tbl_title = match.group(3).strip()
            
            # Buscar fuente/nota en el párrafo posterior si existe
            tbl_foot = ""
            if idx < len(elements) - 1 and isinstance(elements[idx + 1], CT_P):
                next_p = Paragraph(elements[idx + 1], doc)
                next_text = next_p.text.strip()
                if next_text.lower().startswith(('fuente:', 'nota:', 'source:', 'note:')):
                    tbl_foot = next_text

            # Extraer las filas del objeto Table y detectar si contiene sub-tablas unificadas (ej. Tabla 4 y Tabla 5 juntas en Word)
            current_table_rows = []
            
            for row in tbl.rows:
                col_paragraphs = []
                for cell in row.cells:
                    lines = []
                    for p in cell.paragraphs:
                        p_text = p.text.strip()
                        if not p_text: continue
                        for l in p_text.split('\n'):
                            if l.strip():
                                if len(l.strip()) > 110 and not any(kw in l.lower() for kw in ['00421', 'diagnóstico', 'volumen']):
                                    lines.extend(split_long_paragraph(l.strip(), max_len=110))
                                else:
                                    lines.append(l.strip())
                    if not lines:
                        lines = [cell.text.strip()] if cell.text.strip() else []
                    col_paragraphs.append(lines)
                
                max_p_count = max((len(cp) for cp in col_paragraphs), default=0)
                
                final_col_lines = []
                for cp in col_paragraphs:
                    if len(cp) == 1 and max_p_count > 1 and len(cp[0]) > 40:
                        k = min(max_p_count, max(2, (len(cp[0]) + 39) // 40))
                        chunks = split_text_into_n_chunks(cp[0], k)
                        final_col_lines.append(chunks)
                    else:
                        final_col_lines.append(cp)
                        
                max_len = max((len(cl) for cl in final_col_lines), default=0)
                if max_len <= 1:
                    sub_rows = [[cell.text.strip() for cell in row.cells]]
                else:
                    sub_rows = []
                    for i in range(max_len):
                        r_cells = [final_col_lines[c][i] if i < len(final_col_lines[c]) else '' for c in range(len(final_col_lines))]
                        sub_rows.append(r_cells)

                for row_cells_text in sub_rows:
                    joined_row_text = " ".join(row_cells_text)
                    
                    # Verificar si esta fila inicia una nueva sub-tabla (ej. "Tabla 5", "Tabla 5. Libertad...")
                    match_sub = re.search(r'^(Tabla|Table)\s*(\d+)[\.\s:\-]*(.*)', joined_row_text, re.IGNORECASE)
                    if current_table_rows and match_sub and not joined_row_text.lower().startswith(('fuente:', 'nota:')):
                        # Guardar la tabla actual (ej. Tabla 4)
                        docx_tables.append({
                            'counter': table_counter,
                            'label': tbl_label,
                            'title': tbl_title,
                            'foot': tbl_foot,
                            'rows': current_table_rows
                        })
                        table_counter += 1
                        
                        # Iniciar la nueva tabla independiente (ej. Tabla 5)
                        sub_num = match_sub.group(2) if match_sub.group(2) else str(table_counter)
                        tbl_label = f"{match_sub.group(1).capitalize()} {sub_num}"
                        tbl_title = match_sub.group(3).strip() if match_sub.group(3).strip() else tbl_label
                        tbl_foot = ""
                        current_table_rows = []
                        continue
                        
                    # Verificar si la fila es una nota de fuente/pie de tabla
                    if joined_row_text.lower().startswith(('fuente:', 'nota:', 'source:', 'note:')):
                        tbl_foot = joined_row_text
                        continue
                        
                    current_table_rows.append(row_cells_text)

            if current_table_rows:
                docx_tables.append({
                    'counter': table_counter,
                    'label': tbl_label,
                    'title': tbl_title,
                    'foot': tbl_foot,
                    'rows': current_table_rows
                })
                table_counter += 1

    if not docx_tables:
        return soup

    # Limpiar cualquier tabla mal parseada o concatenada en el XML (ej. Tabla1Contrastiva... o Tabla 1. Contrastiva...)
    for sec in list(body_tag.find_all('sec')):
        title = sec.find('title')
        if title:
            t_text = title.get_text(strip=True)
            if re.search(r'^(Tabla|Table)\s*\d*', t_text, re.IGNORECASE):
                sec.decompose()

    for p in list(body_tag.find_all('p')):
        p_text = p.get_text(strip=True)
        if re.search(r'^(Tabla|Table)\s*\d*', p_text, re.IGNORECASE) and not p.find_parent('table-wrap'):
            p.decompose()

    # Reemplazar o insertar los nodos <table-wrap> verdaderos e independientes en el XML JATS
    existing_tables = body_tag.find_all('table-wrap')
    for idx, dt in enumerate(docx_tables, start=1):
        tbl_wrap = soup.new_tag('table-wrap', id=f"t{dt['counter']}")
        
        lbl_tag = soup.new_tag('label')
        lbl_tag.string = dt['label']
        tbl_wrap.append(lbl_tag)
        
        cap_tag = soup.new_tag('caption')
        title_tag = soup.new_tag('title')
        title_tag.string = dt['title']
        cap_tag.append(title_tag)
        tbl_wrap.append(cap_tag)
        
        table_tag = soup.new_tag('table')
        tbody = soup.new_tag('tbody')
        
        for r_cells in dt['rows']:
            tr = soup.new_tag('tr')
            for cell_text in r_cells:
                td = soup.new_tag('td')
                td.string = cell_text
                tr.append(td)
            tbody.append(tr)
            
        table_tag.append(tbody)
        tbl_wrap.append(table_tag)
        
        if dt['foot']:
            foot_tag = soup.new_tag('table-wrap-foot')
            attrib_tag = soup.new_tag('attrib')
            attrib_tag.string = dt['foot']
            foot_tag.append(attrib_tag)
            tbl_wrap.append(foot_tag)
            
        matched_existing = None
        for et in existing_tables:
            et_txt = et.get_text(strip=True)
            if f"Tabla {dt['counter']}" in et_txt or f"Table {dt['counter']}" in et_txt or dt['title'] in et_txt:
                matched_existing = et
                break
                
        if matched_existing:
            matched_existing.replace_with(tbl_wrap)
        else:
            cite_xref = body_tag.find(lambda tag: tag.name == 'xref' and tag.get('rid') == f"t{dt['counter']}")
            if not cite_xref:
                cite_p = body_tag.find(lambda tag: tag.name == 'p' and f"tabla {dt['counter']}" in tag.get_text(strip=True).lower())
            else:
                cite_p = cite_xref.find_parent('p')
                
            if cite_p:
                cite_p.insert_after(tbl_wrap)
            elif idx - 1 < len(existing_tables):
                existing_tables[idx - 1].replace_with(tbl_wrap)
            else:
                intro_sec = body_tag.find('sec', **{"sec-type": "intro"}) or body_tag.find('sec')
                if intro_sec:
                    intro_sec.append(tbl_wrap)
                else:
                    body_tag.append(tbl_wrap)

    # Actualizar contador de tablas en <counts>
    tc_tag = soup.find('table-count')
    if tc_tag:
        tc_tag['count'] = str(len(docx_tables))

    return soup
