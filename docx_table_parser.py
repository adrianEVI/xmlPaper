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

NS_W = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def parse_docx_table_grid(tbl):
    """
    Lee la estructura XML de una tabla Word (CT_Tbl) utilizando OpenXML (w:tcPr, w:gridSpan, w:vMerge)
    para preservar celdas combinadas (colspan, rowspan) y alineación.
    """
    rows_xml = tbl._element.xpath('./w:tr')
    grid = []
    for tr in rows_xml:
        row_cells = []
        c_idx = 0
        tcs = tr.xpath('./w:tc')
        for tc in tcs:
            tcPr = tc.find('w:tcPr', NS_W)
            gridSpan = tcPr.find('w:gridSpan', NS_W) if tcPr is not None else None
            vMerge = tcPr.find('w:vMerge', NS_W) if tcPr is not None else None
            
            span = int(gridSpan.attrib.get(f'{{{NS_W["w"]}}}val', '1')) if gridSpan is not None else 1
            vmerge_val = 'none'
            if vMerge is not None:
                vmerge_val = vMerge.attrib.get(f'{{{NS_W["w"]}}}val', 'continue')
            
            texts = [t.text for t in tc.findall('.//w:t', NS_W) if t.text]
            text = ' '.join(''.join(texts).split())
            
            align = 'left'
            jc = tc.find('.//w:jc', NS_W)
            if jc is not None:
                val = jc.attrib.get(f'{{{NS_W["w"]}}}val')
                if val in ['center', 'right', 'left']:
                    align = val
            
            row_cells.append({
                'text': text,
                'colspan': span,
                'vmerge': vmerge_val,
                'grid_col': c_idx,
                'align': align
            })
            c_idx += span
        grid.append(row_cells)
    
    # Calcular rowspan y marcar celdas secundarias
    for r_idx in range(len(grid)):
        for cell in grid[r_idx]:
            if cell['vmerge'] == 'restart':
                g_col = cell['grid_col']
                rowspan = 1
                for r_next in range(r_idx + 1, len(grid)):
                    next_cell = next((c for c in grid[r_next] if c['grid_col'] == g_col), None)
                    if next_cell and next_cell['vmerge'] == 'continue':
                        rowspan += 1
                    else:
                        break
                cell['rowspan'] = rowspan
            elif cell['vmerge'] == 'continue':
                cell['rowspan'] = 0
            else:
                cell['rowspan'] = 1
                
    return grid

def build_jats_table_from_docx(docx_path: str, soup: BeautifulSoup) -> BeautifulSoup:
    """
    A. Recorre secuencialmente doc.element.body de python-docx para detectar elementos w:tbl.
    Genera el nodo estandarizado JATS <table-wrap id="t1"> con <label>, <caption>, <table>, <tbody>, <tr>, <td>
    preservando celdas combinadas (colspan, rowspan) y alineaciones de celda.
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
            
            # Buscar título en los párrafos anteriores si existe (ej. "Tabla 1. Criterios...")
            tbl_label = f"Tabla {table_counter}"
            tbl_title = f"Tabla {table_counter}"
            for back in range(1, 6):
                if idx - back >= 0 and isinstance(elements[idx - back], CT_P):
                    prev_p = Paragraph(elements[idx - back], doc)
                    prev_text = prev_p.text.strip()
                    if not prev_text:
                        continue
                    match = re.search(r'^(Tabla|Table)\s*(\d*)[\.\s:\-]*(.*)', prev_text, re.IGNORECASE)
                    if match:
                        num_str = match.group(2) if match.group(2) else str(table_counter)
                        tbl_label = f"{match.group(1).capitalize()} {num_str}"
                        if match.group(3).strip():
                            tbl_title = match.group(3).strip()
                        break
            
            # Buscar fuente/nota en los párrafos posteriores si existe
            tbl_foot = ""
            for fwd in range(1, 6):
                if idx + fwd < len(elements) and isinstance(elements[idx + fwd], CT_P):
                    next_p = Paragraph(elements[idx + fwd], doc)
                    next_text = next_p.text.strip()
                    if not next_text:
                        continue
                    if next_text.lower().startswith(('fuente:', 'nota:', 'source:', 'note:')):
                        tbl_foot = next_text
                    break

            grid_rows = parse_docx_table_grid(tbl)
            current_table_rows = []
            
            for row_cells in grid_rows:
                row_texts = [c['text'] for c in row_cells if c.get('rowspan', 1) > 0]
                joined_row_text = " ".join(row_texts)
                
                # Verificar si esta fila inicia una nueva sub-tabla (ej. "Tabla 5")
                match_sub = re.search(r'^(Tabla|Table)\s*(\d+)[\.\s:\-]*(.*)', joined_row_text, re.IGNORECASE)
                if current_table_rows and match_sub and not joined_row_text.lower().startswith(('fuente:', 'nota:')):
                    docx_tables.append({
                        'counter': table_counter,
                        'label': tbl_label,
                        'title': tbl_title,
                        'foot': tbl_foot,
                        'rows': current_table_rows
                    })
                    table_counter += 1
                    
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
                    
                current_table_rows.append(row_cells)

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

    # Limpiar cualquier tabla mal parseada o concatenada en el XML
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

    # Eliminar tablas preliminares/imperfectas de Pandoc antes de insertar las reconstruidas de python-docx
    for old_tw in list(body_tag.find_all('table-wrap')):
        old_tw.decompose()

    # Reemplazar o insertar los nodos <table-wrap> verdaderos e independientes en el XML JATS
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
        
        table_tag = soup.new_tag('table', border="0", cellspacing="0", cellpadding="0")
        tbody = soup.new_tag('tbody')
        
        total_rows = len(dt['rows'])
        for r_idx, row_cells in enumerate(dt['rows']):
            tr = soup.new_tag('tr')
            for cell in row_cells:
                if cell.get('rowspan', 1) == 0:
                    continue  # Celda omitida por vMerge
                
                td_attrs = {}
                if cell.get('colspan', 1) > 1:
                    td_attrs['colspan'] = str(cell['colspan'])
                if cell.get('rowspan', 1) > 1:
                    td_attrs['rowspan'] = str(cell['rowspan'])
                    
                align_val = cell.get('align', 'left')
                style_parts = ["border: 0"]
                if r_idx == 0:
                    style_parts.append("border-top: 1px solid #000000")
                if r_idx == total_rows - 1:
                    style_parts.append("border-bottom: 1px solid #000000")
                style_parts.append(f"text-align: {align_val}")
                if align_val == 'left':
                    style_parts.append("padding-left: 10px")
                    
                td_attrs['style'] = "; ".join(style_parts) + ";"
                
                td = soup.new_tag('td', **td_attrs)
                td.string = cell['text']
                tr.append(td)
            tbody.append(tr)
            
        table_tag.append(tbody)
        tbl_wrap.append(table_tag)
        
        if dt['foot']:
            foot_tag = soup.new_tag('table-wrap-foot')
            fn_tag = soup.new_tag('fn', id=f"TFN{dt['counter']}", **{"fn-type": "other"})
            p_tag = soup.new_tag('p')
            p_tag.string = dt['foot']
            fn_tag.append(p_tag)
            foot_tag.append(fn_tag)
            tbl_wrap.append(foot_tag)
            
        cite_xref = body_tag.find(lambda tag: tag.name == 'xref' and tag.get('rid') == f"t{dt['counter']}")
        if not cite_xref:
            cite_p = body_tag.find(lambda tag: tag.name == 'p' and f"tabla {dt['counter']}" in tag.get_text(strip=True).lower())
        else:
            cite_p = cite_xref.find_parent('p')
            
        if cite_p:
            cite_p.insert_after(tbl_wrap)
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

