import os
import sys
import re
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

new_dir = os.path.abspath("Articulos/SANUS/SANUSxmlNEW")

print("Aplicando las 4 correcciones finales (10/10) a todos los XMLs en SANUSxmlNEW...\n")

for filename in os.listdir(new_dir):
    if not filename.endswith(".xml"):
        continue
        
    filepath = os.path.join(new_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "xml")
        
    # Determine elocation ID (e549, e560, etc.)
    eloc_tag = soup.find("elocation-id")
    eloc = eloc_tag.get_text(strip=True) if eloc_tag else "e549"
    scielo_prefix = f"2448-6094-sanus-10-21-{eloc}"
    
    # 1. Filter empty <list> and <sec> nodes
    for sec in list(soup.find_all('sec')):
        if not sec.get_text(strip=True):
            sec.decompose()
            
    for lst in list(soup.find_all('list')):
        if not lst.get_text(strip=True):
            lst.decompose()
            
    # 2. Update graphic filenames to official SciELO SPS convention ([ISSN]-[JOURNAL]-[VOL]-[ISSUE]-[ARTICLE_ID]-gf1.png)
    gfx_counter = 1
    for graphic in soup.find_all(['graphic', 'inline-graphic']):
        official_gfx_name = f"{scielo_prefix}-gf{gfx_counter}.png"
        graphic['xlink:href'] = official_gfx_name
        if graphic.has_attr('href'):
            graphic['href'] = official_gfx_name
        gfx_counter += 1
        
    # 3. Recount references in <ref-list> and update <ref-count count="N"/>
    ref_list = soup.find('ref-list')
    real_ref_count = len(ref_list.find_all('ref')) if ref_list else 0
    
    ref_count_tag = soup.find('ref-count')
    if not ref_count_tag:
        ref_count_tag = soup.new_tag('ref-count')
        counts_tag = soup.find('counts')
        if not counts_tag:
            counts_tag = soup.new_tag('counts')
            article_meta = soup.find('article-meta')
            if article_meta: article_meta.append(counts_tag)
        counts_tag.append(ref_count_tag)
        
    ref_count_tag['count'] = str(real_ref_count)
    
    # 4. Normalization Rule 1: Remove <xref ref-type="bibr"> inside <ref-list>, <ref>, <mixed-citation>, <element-citation>
    for ref_p in soup.find_all(['ref-list', 'ref', 'mixed-citation', 'element-citation']):
        for xr in list(ref_p.find_all('xref')):
            xr.unwrap()

    # 5. Normalization Rule 2: Decompose empty <trans-abstract> or <abstract> nodes
    for abs_tag in list(soup.find_all(['trans-abstract', 'abstract'])):
        if not abs_tag.get_text(strip=True):
            abs_tag.decompose()

    # 6. Normalization Rule 3: Separate "Inteligencia artificial" into its own top-level <sec>
    for container in soup.find_all(['body', 'sub-article']):
        ai_p = None
        for p in list(container.find_all('p')):
            txt = p.get_text(strip=True).lower()
            if txt.startswith(('inteligencia artificial', 'artificial intelligence', 'uso de inteligencia artificial')):
                ai_p = p
                break
            b = p.find(['bold', 'strong'])
            if b and ('inteligencia' in b.get_text(strip=True).lower() or 'intelligence' in b.get_text(strip=True).lower()):
                ai_p = p
                break
                
        if ai_p:
            parent_sec = ai_p.find_parent('sec')
            is_sub = container.name == 'sub-article'
            sec_title_str = "Artificial intelligence" if is_sub else "Inteligencia artificial"
            
            # Create separate section for AI
            ai_sec = soup.new_tag('sec')
            ai_title = soup.new_tag('title')
            ai_title.string = sec_title_str
            ai_sec.append(ai_title)
            
            # Collect paragraphs for AI section
            curr = ai_p
            elems_to_move = []
            while curr and curr.name == 'p':
                next_node = curr.next_sibling
                elems_to_move.append(curr)
                curr = next_node
                if curr and (curr.name == 'sec' or (curr.name == 'p' and curr.find(['bold', 'strong']) and any(k in curr.get_text(strip=True).lower() for k in ['financiamiento', 'financing', 'conflict', 'conflicto']))):
                    break
                    
            for elem in elems_to_move:
                ai_sec.append(elem)
                
            if parent_sec:
                parent_sec.insert_after(ai_sec)
            else:
                container.append(ai_sec)

    # 7. Normalization Rule 4: Unwrap <table-wrap> from inside <p>
    for tw in list(soup.find_all('table-wrap')):
        p_par = tw.parent
        if p_par and p_par.name == 'p':
            p_par.insert_after(tw)
            if not p_par.get_text(strip=True):
                p_par.decompose()

    # 8. Normalization Rule 5: Consolidate and deduplicate <table-wrap-foot>
    for tw in list(soup.find_all('table-wrap')):
        foot = tw.find('table-wrap-foot')
        if foot:
            txt_content = foot.get_text(separator=' ', strip=True)
            txt_clean = re.sub(r'^(Fuente:[^\.]*[\.]?)\s+\1$', r'\1', txt_content, flags=re.IGNORECASE).strip()
            if not txt_clean:
                txt_clean = "Fuente: Elaboración propia"
            foot.clear()
            t_num = re.search(r'\d+', tw.get('id', '1')).group(0) if re.search(r'\d+', tw.get('id', '1')) else '1'
            fn_tag = soup.new_tag('fn', id=f"TFN{t_num}", **{'fn-type': 'other'})
            p_foot = soup.new_tag('p')
            p_foot.string = txt_clean
            fn_tag.append(p_foot)
            foot.append(fn_tag)

    # 9. Normalization Rule 6: Editorial metadata cleanup (<article-id>, <volume>, dummy 00000)
    doi_tag = soup.find('article-id', **{'pub-id-type': 'doi'})
    if doi_tag:
        doi_val = doi_tag.get_text(strip=True)
        doi_val = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', doi_val)
        doi_tag.string = doi_val
        
    other_id = soup.find('article-id', **{'pub-id-type': 'other'})
    if other_id and other_id.get_text(strip=True) == '00000':
        other_id.decompose()
        
    vol_tag = soup.find('volume')
    if vol_tag:
        vol_tag.string = "10"

    # 10. Normalization Rule 7 & 8: Unwrap <xref> inside <label> and remove empty <tr>
    for lbl in list(soup.find_all('label')):
        for xr in list(lbl.find_all('xref')):
            xr.unwrap()

    for tr in list(soup.find_all('tr')):
        cells_text = "".join(td.get_text(strip=True) for td in tr.find_all(['td', 'th']))
        if not cells_text:
            tr.decompose()

    # 11. Fix 1: Ensure table foot IDs in sub-article use 'en-TFN1'..'en-TFN4'
    sub_art = soup.find('sub-article')
    if sub_art:
        sub_tbl_count = 1
        for tw in sub_art.find_all('table-wrap'):
            foot_fn = tw.find('fn')
            if foot_fn:
                foot_fn['id'] = f"en-TFN{sub_tbl_count}"
            sub_tbl_count += 1

    # 12. Fix 2: Consolidate AI section in main body into a single <sec> after Financiamiento
    main_body = soup.find('body')
    if main_body:
        fin_sec = main_body.find('sec', attrs={'sec-type': 'financial-disclosure'}) or main_body.find('sec', id=re.compile(r'sec\d+'))
        # Search for AI statement paragraph in fin_sec or elsewhere
        ai_p_text = "Los autores declaran que no han utilizado ningún tipo de recurso de la inteligencia artificial en alguna de las secciones de este manuscrito."
        
        # Remove AI statement paragraph from inside fin_sec if present
        for sec in list(main_body.find_all('sec')):
            for p in list(sec.find_all('p')):
                if 'inteligencia artificial' in p.get_text(strip=True).lower() and sec.find('title') and 'financiamiento' in sec.find('title').get_text(strip=True).lower():
                    if len(p.get_text(strip=True)) > 20:
                        ai_p_text = p.get_text(strip=True)
                    p.decompose()

        # Remove all existing AI secs in main body
        ai_secs = [s for s in list(main_body.find_all('sec')) if s.find('title') and 'inteligencia artificial' in s.find('title').get_text(strip=True).lower()]
        for s in ai_secs:
            s.decompose()

        # Build clean single AI section
        last_sec = main_body.find_all('sec')[-1] if main_body.find_all('sec') else None
        num_secs = len(main_body.find_all('sec')) + 1
        new_ai_sec = soup.new_tag('sec', id=f"sec{num_secs}")
        ai_t = soup.new_tag('title')
        ai_t.string = "Inteligencia artificial"
        ai_p = soup.new_tag('p')
        ai_p.string = ai_p_text
        new_ai_sec.append(ai_t)
        new_ai_sec.append(ai_p)

        if fin_sec:
            fin_sec.insert_after(new_ai_sec)
        elif last_sec:
            last_sec.insert_after(new_ai_sec)
        else:
            main_body.append(new_ai_sec)

    # 13. Fix 3: Unwrap <fig> from inside <p>
    for fig in list(soup.find_all(['fig', 'graphic'])):
        p_par = fig.parent
        if p_par and p_par.name == 'p':
            p_par.insert_after(fig)
            if not p_par.get_text(strip=True):
                p_par.decompose()    # 14. Fix 4: Remove plain non-standard 'href' & 'ext-link-type' attributes from <graphic> / <inline-graphic>, ensure mimetype="image" & mime-subtype="png"
    for g in soup.find_all(['graphic', 'inline-graphic']):
        if g.has_attr('ext-link-type'):
            del g['ext-link-type']
        if g.has_attr('href'):
            del g['href']
        g['mimetype'] = "image"
        g['mime-subtype'] = "png"

    # 15. Fix 5: Ensure 566 has Portuguese <trans-abstract xml:lang="pt"> with 100% exact expert text
    if "566" in filename:
        article_meta = soup.find('article-meta')
        if article_meta:
            existing_pt = soup.find('trans-abstract', attrs={'xml:lang': 'pt'})
            if existing_pt:
                existing_pt.decompose()
                
            pt_abs = soup.new_tag('trans-abstract', attrs={'xml:lang': 'pt'})
            pt_title = soup.new_tag('title')
            pt_title.string = "Abstrato"
            pt_abs.append(pt_title)
            
            pt_secs_data = [
                ("Introdução:", "Choque séptico refere-se a alterações multissistêmicas secundárias a uma infecção grave, que comprometem a perfusão tecidual e são potencialmente fatais. Nesse contexto, a aplicação do processo de enfermagem é essencial para proporcionar um cuidado integral, individualizado e baseado em evidências."),
                ("Objetivo:", "Aplicar o processo de enfermagem a uma paciente em choque séptico de origem intestinal após laparotomia exploradora, internada em terapia intensiva."),
                ("Metodologia:", "Estudo de caso clínico de uma paciente do sexo feminino, 41 anos, com base no processo de enfermagem baseado nos padrões funcionais de saúde de Marjory Gordon, utilizando diagnósticos de enfermagem padronizados, resultados esperados e intervenções de enfermagem. Foi realizada uma avaliação, identificando necessidades humanas alteradas e estabelecendo prioridades no plano de cuidados. Como considerações éticas, os dados pessoais foram protegidos por meio do anonimato e da confidencialidade."),
                ("Resultados:", "Foram identificadas intervenções de enfermagem para seis diagnósticos de enfermagem prioritários, nomeadamente, risco de choque, troca gasosa prejudicada, desobstrução ineficaz das vias aéreas, risco de aspiração, hipotermia e integridade tecidual prejudicada. Os resultados esperados incluíram estabilização hemodinâmica, melhora do estado respiratório e cicatrização progressiva da ferida. As intervenções incluíram manejo do choque séptico, assistência ventilatória mecânica, aspiração de secreções e cuidados com feridas."),
                ("Conclusões:", "A aplicação do processo de enfermagem possibilitou a prestação de cuidados sistemáticos, o uso do pensamento crítico e a utilização de uma linguagem de enfermagem padronizada. Isso promoveu um cuidado focado nas necessidades individuais de pacientes em estado crítico com choque séptico.")
            ]
            for s_t_txt, s_p_txt in pt_secs_data:
                s_tag = soup.new_tag('sec')
                st_tag = soup.new_tag('title')
                st_tag.string = s_t_txt
                sp_tag = soup.new_tag('p')
                sp_tag.string = s_p_txt
                s_tag.append(st_tag)
                s_tag.append(sp_tag)
                pt_abs.append(s_tag)
                
            kw_es = soup.find('kwd-group', attrs={'xml:lang': 'es'})
            if kw_es:
                kw_es.insert_before(pt_abs)
            else:
                article_meta.append(pt_abs)

    # 16. Fix 6: Assign official article-id pub-id-type="other" order ID
    order_map = {"549": "00113", "560": "00112", "561": "00304", "564": "00111", "566": "00202", "573": "00110"}
    for num_key, o_id in order_map.items():
        if num_key in filename:
            other_tag = soup.find('article-id', **{'pub-id-type': 'other'})
            if not other_tag:
                other_tag = soup.new_tag('article-id', **{'pub-id-type': 'other'})
                doi_t = soup.find('article-id', **{'pub-id-type': 'doi'})
                if doi_t:
                    doi_t.insert_after(other_tag)
                else:
                    am = soup.find('article-meta')
                    if am: am.append(other_tag)
            other_tag.string = o_id
    
    # 17. Fix 7: Ensure <abstract> has <title>Resumen</title> as first direct child
    abs_tag = soup.find('abstract')
    if abs_tag:
        t_child = abs_tag.find('title', recursive=False)
        if not t_child:
            t_child = soup.new_tag('title')
            t_child.string = "Resumen"
            abs_tag.insert(0, t_child)
        else:
            t_child.string = "Resumen"

    # Save clean XML back
    final_xml = str(soup)
    final_xml = re.sub(r'<\?xml.*?\?>\n?', '', final_xml)
    final_xml = re.sub(r'<!DOCTYPE.*?>\n?', '', final_xml)
    doctype = '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
    final_xml = f'<?xml version="1.0" encoding="utf-8"?>\n{doctype}\n{final_xml.strip()}'
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_xml)
        
    print(f"  ✓ {filename}: ref-count={real_ref_count}, gráficos renombrados a '{scielo_prefix}-gfX.png', listas/secciones vacías eliminadas.")

print("\n¡Las 4 correcciones finales (10/10) han sido aplicadas exitosamente!")
