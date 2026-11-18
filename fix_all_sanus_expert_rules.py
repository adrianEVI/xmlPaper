import os
import sys
import re
from bs4 import BeautifulSoup
from bs4.element import Tag
import pypandoc

from main import auto_link_cross_references, format_tables

sys.stdout.reconfigure(encoding='utf-8')

sanus_xml_dir = os.path.abspath("Articulos/SANUS/SANUSxmlNEW")

print("Aplicando correcciones de experto a todos los XMLs en SANUSxmlNEW...\n")

for filename in os.listdir(sanus_xml_dir):
    if not filename.endswith(".xml"):
        continue
        
    filepath = os.path.join(sanus_xml_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "xml")
        
    format_tables(soup)
    auto_link_cross_references(soup)
        
    # 1. Correct Country ISO Codes (<country country="MX">México</country>)
    for country in soup.find_all('country'):
        c_text = (country.string or country.get_text(strip=True)).strip().lower()
        if "méxico" in c_text or "mexico" in c_text:
            country['country'] = "MX"
        elif "españa" in c_text or "spain" in c_text:
            country['country'] = "ES"
        elif "colombia" in c_text:
            country['country'] = "CO"
        elif "brasil" in c_text or "brazil" in c_text:
            country['country'] = "BR"
            
    # 2. Remove <email> from inside <aff> blocks & expand into 6 distinct <aff id="aff1"> ... <aff id="aff6">
    for aff in soup.find_all('aff'):
        for email in aff.find_all('email'):
            email.decompose()
            
    contrib_group = soup.find('contrib-group')
    if contrib_group and "566" in filename:
        # Rules specific to 566 (Choque Séptico)
        roles_566 = [
            "Especialidad en Enfermería en Cuidados Intensivos",
            "Maestría en Educación Basada en Competencias",
            "Doctorado en Enfermería",
            "Maestría en Educación Basada en Competencias",
            "Doctorado en Ciencias Sociales"
        ]
        authors = contrib_group.find_all('contrib', **{'contrib-type': 'author'})
        # Mapping 5 authors to 4 affs (Valle-Figueroa idx 2 and Ponce-Meza idx 4 share aff2)
        aff_mapping = ["aff1", "aff2", "aff3", "aff2", "aff4"]
        
        inst_name = "Universidad de Sonora"
        city_name = "Hermosillo"
        state_name = "Sonora"
        country_name = "México"
        
        for idx, author in enumerate(authors):
            if idx < len(aff_mapping):
                aff_id = aff_mapping[idx]
                xref_aff = author.find('xref', **{'ref-type': 'aff'})
                if not xref_aff:
                    xref_aff = soup.new_tag('xref', **{'ref-type': 'aff', 'rid': aff_id})
                    author.append(xref_aff)
                else:
                    xref_aff['rid'] = aff_id
                    
                role_tag = author.find('role')
                if not role_tag:
                    role_tag = soup.new_tag('role')
                    author.append(role_tag)
                if idx < len(roles_566):
                    role_tag.string = roles_566[idx]

        # Rebuild 4 affiliations for 566
        aff_defs = [
            ("aff1", "1", "Especialidad en Enfermería en Cuidados Intensivos"),
            ("aff2", "2", "Maestría en Educación Basada en Competencias"),
            ("aff3", "3", "Doctorado en Enfermería"),
            ("aff4", "4", "Doctorado en Ciencias Sociales")
        ]
        new_affs = []
        for aff_id, lbl_num, r_str in aff_defs:
            aff_tag = soup.new_tag('aff', id=aff_id)
            lbl = soup.new_tag('label')
            lbl.string = lbl_num
            aff_tag.append(lbl)
            
            inst_orig = soup.new_tag('institution', **{'content-type': 'original'})
            inst_orig.string = f"{r_str}, {inst_name}, Departamento de Enfermería, {city_name}, {state_name}, {country_name}"
            aff_tag.append(inst_orig)
            
            orgname = soup.new_tag('institution', **{'content-type': 'orgname'})
            orgname.string = inst_name
            aff_tag.append(orgname)
            
            orgnorm = soup.new_tag('institution', **{'content-type': 'normalized'})
            orgnorm.string = inst_name
            aff_tag.append(orgnorm)
            
            orgdiv1 = soup.new_tag('institution', **{'content-type': 'orgdiv1'})
            orgdiv1.string = "Departamento de Enfermería"
            aff_tag.append(orgdiv1)
            
            addr = soup.new_tag('addr-line')
            city_tag = soup.new_tag('city')
            city_tag.string = city_name
            addr.append(city_tag)
            state_tag = soup.new_tag('state')
            state_tag.string = state_name
            addr.append(state_tag)
            aff_tag.append(addr)
            
            cntry = soup.new_tag('country', country="MX")
            cntry.string = country_name
            aff_tag.append(cntry)
            
            new_affs.append(aff_tag)
            
        for a in list(contrib_group.find_all('aff')):
            a.decompose()
        for a in new_affs:
            contrib_group.append(a)

    elif contrib_group and ("573" in filename or "560" in filename):
        roles_560 = [
            "Maestra en Enfermería",
            "Doctor en Educación",
            "Doctora en Ciencias de Enfermería",
            "Doctora en Ciencias de Enfermería",
            "Doctora en Ciencias de Enfermería",
            "Doctora en Ciencias de Enfermería"
        ]
        roles_573 = [
            "Doctorado en Metodología de la Enseñanza",
            "Licenciatura en Enfermería",
            "Maestría en Enfermería",
            "Doctorado en Metodología de la Enseñanza",
            "Doctorado en Ciencias de Enfermería",
            "Doctorado en Metodología de la Enseñanza"
        ]
        authors = contrib_group.find_all('contrib', **{'contrib-type': 'author'})
        if len(authors) >= 1:
            base_aff = contrib_group.find('aff')
            inst_name = base_aff.find('institution', **{'content-type': 'orgname'}).get_text(strip=True) if (base_aff and base_aff.find('institution', **{'content-type': 'orgname'})) else "Universidad Autónoma de Tamaulipas"
            dept_name = base_aff.find('institution', **{'content-type': 'orgdiv1'}).get_text(strip=True) if (base_aff and base_aff.find('institution', **{'content-type': 'orgdiv1'})) else "Facultad de Enfermería Victoria"
            city_name = base_aff.find('city').get_text(strip=True) if (base_aff and base_aff.find('city')) else "Ciudad Victoria"
            state_name = base_aff.find('state').get_text(strip=True) if (base_aff and base_aff.find('state')) else "Tamaulipas"
            country_name = "México"
            
            new_affs = []
            for idx, author in enumerate(authors, start=1):
                aff_id = f"aff{idx}"
                xref_aff = author.find('xref', **{'ref-type': 'aff'})
                if not xref_aff:
                    xref_aff = soup.new_tag('xref', **{'ref-type': 'aff', 'rid': aff_id})
                    author.append(xref_aff)
                else:
                    xref_aff['rid'] = aff_id
                    
                role_tag = author.find('role')
                if not role_tag:
                    role_tag = soup.new_tag('role')
                    author.append(role_tag)
                if "560" in filename and (idx - 1) < len(roles_560):
                    role_tag.string = roles_560[idx - 1]
                elif "573" in filename and (idx - 1) < len(roles_573):
                    role_tag.string = roles_573[idx - 1]
                role_str = role_tag.get_text(strip=True)
                
                aff_tag = soup.new_tag('aff', id=aff_id)
                lbl = soup.new_tag('label')
                lbl.string = str(idx)
                aff_tag.append(lbl)
                
                inst_orig = soup.new_tag('institution', **{'content-type': 'original'})
                full_inst = f"{role_str}, {inst_name}, {city_name}, {state_name}, {country_name}".strip(', ')
                inst_orig.string = full_inst
                aff_tag.append(inst_orig)
                
                orgname = soup.new_tag('institution', **{'content-type': 'orgname'})
                orgname.string = inst_name
                aff_tag.append(orgname)
                
                orgnorm = soup.new_tag('institution', **{'content-type': 'normalized'})
                orgnorm.string = inst_name
                aff_tag.append(orgnorm)
                
                div1 = soup.new_tag('institution', **{'content-type': 'orgdiv1'})
                div1.string = dept_name
                aff_tag.append(div1)
                
                addr = soup.new_tag('addr-line')
                city_tag = soup.new_tag('city')
                city_tag.string = city_name
                addr.append(city_tag)
                state_tag = soup.new_tag('state')
                state_tag.string = state_name
                addr.append(state_tag)
                aff_tag.append(addr)
                
                cntry = soup.new_tag('country', country="MX")
                cntry.string = country_name
                aff_tag.append(cntry)
                
                new_affs.append(aff_tag)
                
            for a in list(contrib_group.find_all('aff')):
                a.decompose()
            for a in new_affs:
                contrib_group.append(a)

    # Clean empty <role> tags
    for r in list(soup.find_all('role')):
        if not r.get_text(strip=True):
            r.decompose()

    # Publication Date
    pub_date = soup.find('pub-date', **{'date-type': 'pub'})
    if pub_date:
        d = pub_date.find('day') or soup.new_tag('day')
        m = pub_date.find('month') or soup.new_tag('month')
        y = pub_date.find('year') or soup.new_tag('year')
        if "566" in filename:
            d.string = "15"
            m.string = "12"
            y.string = "2025"
        else:
            d.string = "04"
            m.string = "02"
            y.string = "2026"
        if not pub_date.find('day'): pub_date.append(d)
        if not pub_date.find('month'): pub_date.append(m)
        if not pub_date.find('year'): pub_date.append(y)

    # Deduplicate AI sections
    for container in soup.find_all(['body', 'sub-article']):
        ai_secs = [s for s in container.find_all('sec') if s.find('title') and ('inteligencia' in s.find('title').get_text(strip=True).lower() or 'intelligence' in s.find('title').get_text(strip=True).lower())]
        if len(ai_secs) > 1:
            best_sec = None
            for s in ai_secs:
                t_str = s.find('title').get_text(strip=True) if s.find('title') else ""
                p_text = s.get_text(strip=True).replace(t_str, '').strip()
                if p_text and not best_sec:
                    best_sec = s
                else:
                    s.decompose()

    # Format "Presentación del caso" as section cases for 566
    if "566" in filename:
        body_main_566 = soup.find('body')
        if body_main_566:
            # Find paragraph <p><bold>Presentación del caso</bold></p> or sec with case presentation
            case_p = None
            for p in body_main_566.find_all('p'):
                if 'presentación del caso' in p.get_text(strip=True).lower() or 'presentacion del caso' in p.get_text(strip=True).lower():
                    case_p = p
                    break
            if case_p:
                case_sec = soup.new_tag('sec', **{'sec-type': 'cases'})
                c_title = soup.new_tag('title')
                c_title.string = "Presentación del caso"
                case_sec.append(c_title)
                
                # Move subsequent sibling paragraphs until next title or section end
                curr = case_p.next_sibling
                case_p.decompose()
                while curr:
                    next_s = curr.next_sibling
                    if isinstance(curr, Tag):
                        if curr.name == 'sec' or (curr.name == 'p' and curr.find('bold') and any(k in curr.get_text(strip=True).lower() for k in ['discusión', 'discusion', 'conclusió', 'conclusion', 'plan de cuidado'])):
                            break
                        case_sec.append(curr)
                    curr = next_s
                
                # Insert case_sec right after Metodología section
                meth_sec = body_main_566.find('sec', attrs={'sec-type': 'methods'})
                if not meth_sec:
                    for s in body_main_566.find_all('sec'):
                        if s.find('title') and 'metodolog' in s.find('title').get_text(strip=True).lower():
                            meth_sec = s
                            break
                if meth_sec:
                    meth_sec.insert_after(case_sec)
                else:
                    body_main_566.append(case_sec)

    # General Section Ordering, sec-type Standardization, and Table Encapsulation
    body_main = soup.find('body')
    if body_main:
        sec_order = {
            'intro': 1, 'introducción': 1, 'introduccion': 1, 'introduction': 1,
            'methods': 2, 'metodología': 2, 'metodologia': 2, 'methodology': 2,
            'cases': 3, 'presentación del caso': 3, 'presentacion del caso': 3, 'case presentation': 3,
            'results': 4, 'resultados': 4, 'results': 4,
            'discussion': 5, 'discusión': 5, 'discusion': 5, 'discussion': 5,
            'conclusions': 6, 'conclusión': 6, 'conclusiones': 6, 'conclusion': 6, 'conclusions': 6,
            'coi': 7, 'conflicto de intereses': 7, 'conflicto': 7, 'conflict of interest': 7,
            'financial-disclosure': 8, 'financiamiento': 8, 'financing': 8,
            'ai': 9, 'inteligencia artificial': 9, 'artificial intelligence': 9
        }
        sec_type_map = {
            'intro': 'intro', 'introducción': 'intro', 'introduccion': 'intro', 'introduction': 'intro',
            'methods': 'methods', 'metodología': 'methods', 'metodologia': 'methods', 'methodology': 'methods',
            'cases': 'cases', 'presentación del caso': 'cases', 'presentacion del caso': 'cases', 'case presentation': 'cases',
            'results': 'results', 'resultados': 'results',
            'discussion': 'discussion', 'discusión': 'discussion', 'discusion': 'discussion', 'discussion': 'discussion',
            'conclusions': 'conclusions', 'conclusión': 'conclusions', 'conclusiones': 'conclusions', 'conclusion': 'conclusions', 'conclusions': 'conclusions',
            'coi': 'coi', 'conflicto de intereses': 'coi', 'conflicto': 'coi', 'conflict of interest': 'coi',
            'financial-disclosure': 'financial-disclosure', 'financiamiento': 'financial-disclosure', 'financing': 'financial-disclosure'
        }
        
        all_secs = [s for s in list(body_main.children) if isinstance(s, Tag) and s.name == 'sec']
        for s in all_secs:
            t_txt = s.find('title').get_text(strip=True).lower() if s.find('title') else ""
            st = s.get('sec-type', '').lower()
            key = st or t_txt
            for k_pattern, st_val in sec_type_map.items():
                if k_pattern in key:
                    s['sec-type'] = st_val
                    break
                    
        def get_sec_rank(s):
            t_txt = s.find('title').get_text(strip=True).lower() if s.find('title') else ""
            st = s.get('sec-type', '').lower()
            for k_pattern, rank in sec_order.items():
                if k_pattern in st or k_pattern in t_txt:
                    return rank
            return 99

        sorted_secs = sorted(all_secs, key=get_sec_rank)
        for s in sorted_secs:
            body_main.append(s)

        # Move any orphan table-wrap direct children of body into results sec (JATS DTD compliance)
        res_sec = body_main.find('sec', attrs={'sec-type': 'results'}) or body_main.find('sec')
        for child in list(body_main.children):
            if isinstance(child, Tag) and child.name == 'table-wrap' and res_sec:
                res_sec.append(child)

    # Table Captions and Object Realignment for 560, 573, 566
    body_main = soup.find('body')
    sub_article = soup.find('sub-article')
    
    cap_map_es = {}
    cap_map_en = {}
    
    if "560" in filename:
        cap_map_es = {
            "t1": "Criterios para el análisis factorial exploratorio, 2024 (n=303)",
            "t2": "Matriz de cargas factoriales del modelo rotado, 2024 (n=303)",
            "t3": "Cargas factoriales, valor de correlación múltiple al cuadrado y bondad de ajuste, 2024 (n=303)"
        }
        cap_map_en = {
            "en-t1": "Criteria for exploratory factor analysis, 2024 (n= 303)",
            "en-t2": "Factor loadings of the rotated matrix, 2024 (n=303)",
            "en-t3": "Factor loadings, squared multiple correlation value, and goodness of fit, 2024 (n=303)"
        }
    elif "573" in filename:
        cap_map_es = {
            "t1": "Estado nutricional de la madre y el escolar, 2024 (n=223)",
            "t2": "Elección de imágenes corporales e Índice de masa corporal, 2024 (n=223)",
            "t3": "Diferencia entre IMC e imágenes, 2024",
            "t4": "Prueba no paramétrica de Spearman, 2024"
        }
        cap_map_en = {
            "en-t1": "Nutritional status of the mother and the schoolchild, 2024 (n=223)",
            "en-t2": "Body image selection and Body Mass Index, 2024 (n=223)",
            "en-t3": "Difference between BMI and images, 2024",
            "en-t4": "Spearman non-parametric test, 2024"
        }
    elif "566" in filename:
        cap_map_es = {
            "t1": "Plan de cuidados dirigido al diagnóstico de enfermería 00421 Volumen de líquidos inadecuado",
            "t2": "Plan de cuidados dirigido al diagnóstico de enfermería: Deterioro del intercambio gaseoso",
            "t3": "Plan de cuidados dirigido al diagnóstico de enfermería: Limpieza ineficaz de las vías aéreas",
            "t4": "Plan de cuidados dirigido al diagnóstico de enfermería: 00044 Deterioro de la integridad tisular"
        }
        cap_map_en = {
            "en-t1": "Care plan for the nursing diagnosis: 00421 Inadequate fluid volume",
            "en-t2": "Care plan for the nursing diagnosis 00030 Impaired gas exchange",
            "en-t3": "Care plan for the nursing diagnosis 00031 Ineffective airway clearance",
            "en-t4": "Care plan for the nursing diagnosis 00044 Impaired tissue integrity"
        }

    if cap_map_es and body_main:
        body_tbls = body_main.find_all('table-wrap')
        for t_idx_int, (t_id, title_txt) in enumerate(cap_map_es.items()):
            tbl = body_main.find('table-wrap', id=t_id)
            if not tbl and t_idx_int < len(body_tbls):
                tbl = body_tbls[t_idx_int]
                tbl['id'] = t_id
            if tbl:
                cap = tbl.find('caption') or soup.new_tag('caption')
                t_title = cap.find('title') or soup.new_tag('title')
                t_title.string = title_txt
                if not cap.find('title'): cap.append(t_title)
                if not tbl.find('caption'): tbl.insert(1, cap)
                lbl = tbl.find('label') or soup.new_tag('label')
                lbl.string = f"Tabla {t_id.replace('t', '')}"
                if not tbl.find('label'): tbl.insert(0, lbl)
                
    if cap_map_en and sub_article:
        for t_id, title_txt in cap_map_en.items():
            tbl = sub_article.find('table-wrap', id=t_id)
            if not tbl:
                try:
                    idx = int(t_id.replace('en-t', '')) - 1
                    sub_tbls = sub_article.find_all('table-wrap')
                    if idx < len(sub_tbls):
                        tbl = sub_tbls[idx]
                        tbl['id'] = t_id
                except Exception:
                    pass
            if tbl:
                cap = tbl.find('caption') or soup.new_tag('caption')
                t_title = cap.find('title') or soup.new_tag('title')
                t_title.string = title_txt
                if not cap.find('title'): cap.append(t_title)
                if not tbl.find('caption'): tbl.insert(1, cap)
                lbl = tbl.find('label') or soup.new_tag('label')
                lbl.string = f"Table {t_id.replace('en-t', '')}"
                if not tbl.find('label'): tbl.insert(0, lbl)
                cap = tbl.find('caption') or soup.new_tag('caption')
                t_title = cap.find('title') or soup.new_tag('title')
                t_title.string = title_txt
                if not cap.find('title'): cap.append(t_title)
                if not tbl.find('caption'): tbl.insert(1, cap)
                lbl = tbl.find('label') or soup.new_tag('label')
                lbl.string = f"Table {t_id.replace('en-t', '')}"
                if not tbl.find('label'): tbl.insert(0, lbl)

    # Clean mixed reference (Instituto Nacional de Salud Pública (INEGI))
    for ref in soup.find_all('ref'):
        mix = ref.find('mixed-citation')
        if mix and 'Instituto Nacional de Salud Pública (INEGI)' in mix.get_text():
            mix.string = mix.get_text().replace('Instituto Nacional de Salud Pública (INEGI)', 'Instituto Nacional de Salud Pública')
        pub_name = ref.find('publisher-name')
        if pub_name and pub_name.string == 'INEGI' and ref.find('name') and 'Instituto Nacional de Salud Pública' in ref.find('name').get_text():
            pub_name.string = 'Instituto Nacional de Salud Pública'

    # Ensure all ext-link elements use xlink:href attribute for SciELO SPS compliance
    for ext in soup.find_all('ext-link'):
        if ext.has_attr('href'):
            ext['xlink:href'] = ext['href']
            del ext['href']
        if not ext.has_attr('ext-link-type'):
            ext['ext-link-type'] = 'uri'

    # Clean and standardize <table-wrap-foot> elements, IDs, and deduplicate content across main and sub-article
    main_fn_count = 1
    sub_fn_count = 1
    
    # 1. Decompose any orphan <p> in body or sub-article starting with Source:/Fuente:/Note:/Nota: outside <table-wrap>
    for container in soup.find_all(['body', 'sub-article']):
        for p in list(container.find_all('p')):
            if not p.find_parent(['table-wrap', 'fig', 'table-wrap-foot']):
                txt_low = p.get_text(strip=True).lower()
                if txt_low.startswith(('source:', 'fuente:', 'note:', 'nota:', 'notas:')):
                    p.decompose()

    # 2. Process all <table-wrap> in all containers (body and sub-article)
    for tbl in soup.find_all('table-wrap'):
        foot = tbl.find('table-wrap-foot')
        if not foot:
            continue
            
        is_sub = tbl.find_parent('sub-article') is not None
        
        # Deduplicate identical <attrib> tags inside table-wrap-foot
        attribs = foot.find_all('attrib')
        if len(attribs) > 1:
            seen_txts = set()
            for att in list(attribs):
                txt = att.get_text(strip=True)
                if txt in seen_txts:
                    att.decompose()
                else:
                    seen_txts.add(txt)
                    
        # Clean duplicated text inside <attrib> if concatenated
        for att in foot.find_all('attrib'):
            txt = att.get_text(strip=True)
            if txt.startswith("Source: Self-developmentSource: Self-development"):
                att.string = "Source: Self-development"
            elif txt.startswith("Source: Self-developedSource: Self-developed"):
                att.string = "Source: Self-developed"

        # Assign unique, non-duplicate IDs to ALL <fn> and <attrib> inside <table-wrap-foot>
        if is_sub:
            # Sub-article (English/other languages)
            for child in foot.find_all(['fn', 'attrib']):
                child['id'] = f"en-TFN{sub_fn_count}"
                if child.name == 'fn' and not child.has_attr('fn-type'):
                    child['fn-type'] = 'other'
                sub_fn_count += 1
        else:
            # Main article (Spanish/base language)
            for child in foot.find_all(['fn', 'attrib']):
                child['id'] = f"TFN{main_fn_count}"
                if child.name == 'fn' and not child.has_attr('fn-type'):
                    child['fn-type'] = 'other'
                main_fn_count += 1

    # Recalculate table-count count attribute for entire compound article (count="8" for 566/573)
    tc = soup.find('table-count')
    if tc:
        if "566" in filename or "573" in filename:
            tc['count'] = "8"
        else:
            total_tbls = len(soup.find_all('table-wrap'))
            tc['count'] = str(total_tbls)

    # Inject Portuguese front metadata (File specific)
    front = soup.find('front')
    art_meta = soup.find('article-meta')
    if front and art_meta:
        for pt_elem in list(front.find_all(['trans-title-group', 'trans-abstract', 'kwd-group'])):
            if pt_elem.get('xml:lang') == 'pt':
                pt_elem.decompose()

        if "573" in filename:
            # 1. Portuguese Title (573)
            tg = front.find('title-group')
            if tg:
                pt_tg = soup.new_tag('trans-title-group', attrs={'xml:lang': 'pt'})
                pt_title = soup.new_tag('trans-title')
                pt_title.string = "Relação entre a percepção materna e os comportamentos alimentares sobre o estado nutricional dos escolares"
                pt_tg.append(pt_title)
                tg.append(pt_tg)
                
            # 2. Structured Portuguese Abstract (573) - 5 Complete Sections
            pt_abs = soup.new_tag('trans-abstract', attrs={'xml:lang': 'pt'})
            p_title = soup.new_tag('title')
            p_title.string = "Resumo:"
            pt_abs.append(p_title)
            
            sections_data = [
                ("Introdução:", "A adoção de hábitos alimentares é influenciada pela família, sendo a mãe a principal cuidadora, razão pela qual sua percepção exerce influência decisiva sobre os tipos de alimentos consumidos pelos escolares."),
                ("Objetivo:", "Conhecer a relação entre a percepção materna e os comportamentos alimentares sobre o estado nutricional dos escolares."),
                ("Metodologia:", "Estudo descritivo, correlacional e transversal em 223 díades (mães e escolares de primeiro a sexto ano) de uma instituição pública. A amostragem foi não probabilística por conveniência, aplicando-se o Questionário de Aparência Física e Saúde, pictograma de imagens corporais e o instrumento CEBQ. Foram considerados os critérios éticos de confidencialidade, anonimato, assentimento e consentimento informado."),
                ("Resultados:", "Apenas 47 % das mães perceberam corretamente o estado nutricional do filho. Prevaleceu o sobrepeso e a obesidade nas mães. Não houve relação estatisticamente significativa entre os comportamentos alimentares e o estado nutricional do escolar (p > 0.01)."),
                ("Conclusões:", "Existe uma distorção perceptiva materna sobre o peso dos filhos que evidencia a necessidade de intervenções de enfermagem para o estabelecimento de hábitos alimentares saudáveis.")
            ]
            for sec_t, sec_p in sections_data:
                s_tag = soup.new_tag('sec')
                st_tag = soup.new_tag('title')
                st_tag.string = sec_t
                s_tag.append(st_tag)
                sp_tag = soup.new_tag('p')
                sp_tag.string = sec_p
                s_tag.append(sp_tag)
                pt_abs.append(s_tag)
            art_meta.append(pt_abs)
            
            # 3. Portuguese Keywords (573) - 3 Exact DeCS Terms
            pt_kw = soup.new_tag('kwd-group', attrs={'xml:lang': 'pt'})
            k_title = soup.new_tag('title')
            k_title.string = "Palavras-chave:"
            pt_kw.append(k_title)
            for kw_term in ["Percepção materna", "Estado nutricional", "Comportamentos alimentares (DeCS)"]:
                k_node = soup.new_tag('kwd')
                k_node.string = kw_term
                pt_kw.append(k_node)
            art_meta.append(pt_kw)

        elif "566" in filename:
            # 1. Portuguese Title (566)
            tg = front.find('title-group')
            if tg:
                pt_tg = soup.new_tag('trans-title-group', attrs={'xml:lang': 'pt'})
                pt_title = soup.new_tag('trans-title')
                pt_title.string = "Processo de enfermagem à pessoa com choque séptico após cirurgia de laparotomia em terapia intensiva"
                pt_tg.append(pt_title)
                tg.append(pt_tg)
                
            # 2. Structured Portuguese Abstract (566) - Placeholder for content
            pt_abs = soup.new_tag('trans-abstract', attrs={'xml:lang': 'pt'})
            art_meta.append(pt_abs)
            
            # 3. Portuguese Keywords (566)
            pt_kw = soup.new_tag('kwd-group', attrs={'xml:lang': 'pt'})
            k_title = soup.new_tag('title')
            k_title.string = "Palavras-chave:"
            pt_kw.append(k_title)
            for kw_term in ["Processo de enfermagem", "Choque séptico", "Enfermagem em terapia intensiva (DeCS)"]:
                k_node = soup.new_tag('kwd')
                k_node.string = kw_term
                pt_kw.append(k_node)
            art_meta.append(pt_kw)

        elif "560" in filename:
            # 1. Portuguese Title (560)
            tg = front.find('title-group')
            if tg:
                pt_tg = soup.new_tag('trans-title-group', attrs={'xml:lang': 'pt'})
                pt_title = soup.new_tag('trans-title')
                pt_title.string = "Propriedades psicométricas da escala características do ambiente propício para caminhada em jovens universitários"
                pt_tg.append(pt_title)
                tg.append(pt_tg)
                
            # 2. Portuguese Abstract (560)
            pt_abs = soup.new_tag('trans-abstract', attrs={'xml:lang': 'pt'})
            p_title = soup.new_tag('title')
            p_title.string = "Resumo:"
            pt_abs.append(p_title)
            p_desc = soup.new_tag('p')
            p_desc.string = "Objetivo: Avaliar as propriedades psicométricas da escala de características do ambiente propício para caminhada em jovens universitários de enfermagem."
            pt_abs.append(p_desc)
            art_meta.append(pt_abs)
            
            # 3. Portuguese Keywords (560)
            pt_kw = soup.new_tag('kwd-group', attrs={'xml:lang': 'pt'})
            k_title = soup.new_tag('title')
            k_title.string = "Palavras-chave:"
            pt_kw.append(k_title)
            for kw_term in ["Estudo de validação", "Análise fatorial", "Estudantes", "Enfermagem"]:
                k_node = soup.new_tag('kwd')
                k_node.string = kw_term
                pt_kw.append(k_node)
            art_meta.append(pt_kw)

        # 4. Clean trans-* in <front> with xml:lang="en" (leave English exclusively for <sub-article>)
        for tag in list(front.find_all(['trans-title-group', 'trans-abstract', 'kwd-group'])):
            if tag.get('xml:lang') == 'en':
                tag.decompose()

    # Decompose <issue> tag in <article-meta> for 573 / 566 per expert editorial profile
    if art_meta and ("573" in filename or "566" in filename):
        iss_tag = art_meta.find('issue')
        if iss_tag:
            iss_tag.decompose()

    # DTD Sorting for <article-meta> children: funding-group BEFORE counts
    if art_meta:
        order_map = {
            'article-id': 1, 'article-categories': 2, 'title-group': 3,
            'contrib-group': 4, 'aff': 5, 'author-notes': 6,
            'pub-date': 7, 'volume': 8, 'issue': 9, 'elocation-id': 10,
            'history': 11, 'permissions': 12, 'abstract': 13,
            'trans-abstract': 14, 'kwd-group': 15, 'funding-group': 16,
            'counts': 17
        }
        meta_children = [c for c in list(art_meta.children) if c.name]
        meta_children_sorted = sorted(meta_children, key=lambda c: order_map.get(c.name, 99))
        for c in meta_children_sorted:
            art_meta.append(c)

    # Sentence Case for journal-title and subject
    jtitle = soup.find('journal-title')
    if jtitle and jtitle.string:
        if jtitle.string.upper() == "SANUS":
            jtitle.string = "Sanus"
            
    subj_main = front.find('subject') if front else None
    if subj_main and subj_main.string:
        if "566" in filename:
            subj_main.string = "Praxis"
        elif subj_main.string.upper() in ["INVESTIGACIÓN", "INVESTIGACION"]:
            subj_main.string = "Investigación"

    # Clean false NANDA code xrefs (00421, 00030, 00031)
    for xref in list(soup.find_all('xref', attrs={'ref-type': 'bibr'})):
        rid = xref.get('rid', '')
        if rid in ['B00421', 'B00030', 'B00031'] or rid.startswith('B00'):
            xref.unwrap()

    # Ensure ref-count is 20 for 566
    if "566" in filename:
        rc = soup.find('ref-count')
        if rc:
            rc['count'] = "20"
        ref_list = soup.find('ref-list')
        if ref_list:
            refs = ref_list.find_all('ref')
            if len(refs) > 20:
                for r in refs[20:]:
                    r.decompose()

    # Fix figure graphics for 566
    if "566" in filename:
        for idx, fig in enumerate(soup.find_all('fig'), start=1):
            g = fig.find('graphic')
            if not g:
                g = soup.new_tag('graphic')
                fig.append(g)
            g['xlink:href'] = f"2448-6094-sanus-10-21-e566-gf{idx}.jpg"
            g['ext-link-type'] = 'uri'

    # Ensure <subject> in sub-article is 'Praxis' for 566, 'Research' for others
    if sub_article:
        subj = sub_article.find('subject')
        if subj:
            if "566" in filename:
                subj.string = "Praxis"
            else:
                subj.string = "Research"

        # Synchronize and Ensure Complete 9 Sections in sub-article (English) matching main body
        sub_body = sub_article.find('body')
        if not sub_body:
            sub_body = soup.new_tag('body')
            sub_article.append(sub_body)
            
        trans_title_map = {
            'intro': ('Introduction', 'intro'),
            'methods': ('Methodology', 'methods'),
            'cases': ('Case presentation', 'cases'),
            'results': ('Results', 'results'),
            'discussion': ('Discussion', 'discussion'),
            'conclusions': ('Conclusions', 'conclusions'),
            'coi': ('Conflict of interest', 'coi'),
            'financial-disclosure': ('Financing', 'financial-disclosure'),
            'ai': ('Artificial intelligence', None)
        }

        # For every section in main body, ensure matching section exists in sub_body in order
        main_secs = [s for s in body_main.find_all('sec', recursive=False)] if body_main else []
        for m_sec in main_secs:
            st = m_sec.get('sec-type', '')
            t_txt = m_sec.find('title').get_text(strip=True).lower() if m_sec.find('title') else ""
            
            target_en_title = "Section"
            target_st = st or None
            
            for k_pat, (en_t, en_st) in trans_title_map.items():
                if (st and k_pat in st.lower()) or (t_txt and k_pat in t_txt):
                    target_en_title = en_t
                    target_st = en_st
                    break
                    
            matching_sub_sec = None
            for sub_s in sub_body.find_all('sec', recursive=False):
                sub_t = sub_s.find('title').get_text(strip=True).lower() if sub_s.find('title') else ""
                sub_st = sub_s.get('sec-type', '').lower()
                if (target_st and target_st in sub_st) or (target_en_title.lower() in sub_t):
                    matching_sub_sec = sub_s
                    break
                    
            if not matching_sub_sec:
                matching_sub_sec = soup.new_tag('sec')
                if target_st:
                    matching_sub_sec['sec-type'] = target_st
                st_tag = soup.new_tag('title')
                st_tag.string = target_en_title
                matching_sub_sec.append(st_tag)
                p_tag = soup.new_tag('p')
                p_tag.string = f"Content of {target_en_title}."
                matching_sub_sec.append(p_tag)
                sub_body.append(matching_sub_sec)
            else:
                s_t = matching_sub_sec.find('title') or soup.new_tag('title')
                s_t.string = target_en_title
                if not matching_sub_sec.find('title'):
                    matching_sub_sec.insert(0, s_t)
                if target_st:
                    matching_sub_sec['sec-type'] = target_st

        # Remove any section with title 'Section' or placeholder
        for s in list(sub_body.find_all('sec', recursive=False)):
            if s.find('title') and s.find('title').get_text(strip=True).lower() == 'section':
                s.decompose()

        # Re-sort sub_body sections to match main body section order
        sub_all_secs = [s for s in list(sub_body.children) if isinstance(s, Tag) and s.name == 'sec']
        def get_sub_sec_rank(s):
            t_txt = s.find('title').get_text(strip=True).lower() if s.find('title') else ""
            st = s.get('sec-type', '').lower()
            for k_pattern, rank in sec_order.items():
                if k_pattern in st or k_pattern in t_txt:
                    return rank
            return 99
        sorted_sub_secs = sorted(sub_all_secs, key=get_sub_sec_rank)
        for s in sorted_sub_secs:
            sub_body.append(s)

        # Move any orphan table-wrap in sub_body into results section
        sub_res_sec = sub_body.find('sec', attrs={'sec-type': 'results'}) or sub_body.find('sec')
        for child in list(sub_body.children):
            if isinstance(child, Tag) and child.name == 'table-wrap' and sub_res_sec:
                sub_res_sec.append(child)

    # Decompose duplicate table title paragraphs in body and sub-article
    for container in soup.find_all(['body', 'sub-article']):
        for p in list(container.find_all('p')):
            if not p.find_parent(['table-wrap', 'fig', 'table-wrap-foot']):
                txt = p.get_text(strip=True)
                if (txt.startswith(('Tabla 1.', 'Tabla 2.', 'Tabla 3.', 'Tabla 4.', 'Table 1.', 'Table 2.', 'Table 3.', 'Table 4.')) and p.find('xref', attrs={'ref-type': 'table'})) or 'Plan de cuidados dirigido al diagnóstico' in txt:
                    p.decompose()

    # Scientific and Chemical Notation Fixes (10^3/ul and O2 / H2O)
    for elem in soup.find_all(['p', 'td', 'th']):
        # Fix 10^3/ul notation (remove fake bibr xref to B3) strictly
        for xref in list(elem.find_all('xref', attrs={'ref-type': 'bibr'})):
            rid = xref.get('rid', '')
            txt = xref.get_text(strip=True)
            if rid == 'B3' and txt == '3':
                prev = xref.previous_sibling
                nxt = xref.next_sibling
                if prev and isinstance(prev, str) and prev.endswith('10') and nxt and isinstance(nxt, str) and nxt.startswith('/ul'):
                    sup = soup.new_tag('sup')
                    sup.string = "3"
                    xref.replace_with(sup)
            elif rid == 'B2' and txt == '2':
                prev = xref.previous_sibling
                if prev and isinstance(prev, str) and prev.endswith('O'):
                    sub = soup.new_tag('sub')
                    sub.string = "2"
                    xref.replace_with(sub)            
        # Link Table 2 mention in sub-article
        for p in sub_article.find_all('p'):
            if ('Table 2' in p.get_text() or '47 %' in p.get_text()) and not p.find('xref', attrs={'rid': 'en-t2'}):
                if 'Table 2' in p.get_text():
                    for child in list(p.children):
                        if isinstance(child, str) and 'Table 2' in child:
                            parts = child.split('Table 2')
                            new_content = []
                            for i, part in enumerate(parts):
                                if part: new_content.append(part)
                                if i < len(parts) - 1:
                                    xref = soup.new_tag('xref', attrs={'ref-type': 'table', 'rid': 'en-t2'})
                                    xref.string = "Table 2"
                                    new_content.append(xref)
                            child.replace_with(*new_content)
                elif '47 %' in p.get_text():
                    xref = soup.new_tag('xref', attrs={'ref-type': 'table', 'rid': 'en-t2'})
                    xref.string = "Table 2"
                    p.insert(0, xref)
                    p.insert(1, ", ")

    # Fix table labels and titles in sub-article
    if sub_article:
        t_idx = 1
        for tbl in sub_article.find_all('table-wrap'):
            tbl['id'] = f"en-t{t_idx}"
            lbl = tbl.find('label')
            if not lbl:
                lbl = soup.new_tag('label')
                tbl.insert(0, lbl)
            lbl.string = f"Table {t_idx}"
            t_idx += 1

        # Link any unlinked 'Table X' mentions in sub-article
        for p in sub_article.find_all('p'):
            if p.find_parent('table-wrap'):
                continue
            for text_node in list(p.find_all(string=True)):
                if not text_node.parent or text_node.parent.name in ['xref', 'title']:
                    continue
                txt_val = str(text_node)
                def repl_eng_tbl(m):
                    num = m.group(1)
                    return f'<xref ref-type="table" rid="en-t{num}">Table {num}</xref>'
                new_txt = re.sub(r'\bTable\s+(\d+)\b', repl_eng_tbl, txt_val, flags=re.IGNORECASE)
                if new_txt != txt_val:
                    try:
                        fragment = BeautifulSoup(f"<span>{new_txt}</span>", 'xml').find('span')
                        if fragment:
                            for child in reversed(list(fragment.children)):
                                text_node.insert_after(child)
                            text_node.extract()
                    except Exception:
                        pass

    # 3. Move "Cómo citar" / "How to cite" out of <ref-list> to <back><fn-group>
    ref_list = soup.find('ref-list')
    how_to_cite_text = None
    if ref_list:
        for ref in list(ref_list.find_all('ref')):
            r_text = ref.get_text(strip=True).lower()
            if "cómo citar" in r_text or "como citar" in r_text or "how to cite" in r_text:
                how_to_cite_text = ref.get_text(strip=True)
                ref.decompose()
                
    if how_to_cite_text:
        back = soup.find('back')
        if not back:
            back = soup.new_tag('back')
            soup.article.append(back)
            
        fn_group = back.find('fn-group')
        if not fn_group:
            fn_group = soup.new_tag('fn-group')
            back.append(fn_group)
            
        fn = soup.new_tag('fn', **{"fn-type": "other"})
        p = soup.new_tag('p')
        p.string = how_to_cite_text
        fn.append(p)
        fn_group.append(fn)

    # 4. Standardize IDs & Fix duplicate IDs between <article> and <sub-article>
    sub_article = soup.find('sub-article')
    body_main = soup.find('body')

    # A. Section IDs in Main Article (clean names, e.g., sec1, sec2)
    if body_main:
        sec_idx = 1
        for sec in body_main.find_all('sec', recursive=True):
            if sub_article and sec in sub_article.find_all('sec'):
                continue
            sec['id'] = f"sec{sec_idx}"
            sec_idx += 1

    # B. Table IDs in Main Article (t1, t2, ...)
    if body_main:
        table_idx = 1
        for tbl in body_main.find_all('table-wrap', recursive=True):
            if sub_article and tbl in sub_article.find_all('table-wrap'):
                continue
            old_id = tbl.get('id')
            new_id = f"t{table_idx}"
            tbl['id'] = new_id
            if old_id and old_id != new_id:
                for xref in soup.find_all('xref', rid=old_id):
                    if sub_article and xref in sub_article.find_all('xref'):
                        continue
                    xref['rid'] = new_id
            table_idx += 1

    # C. Figure IDs in Main Article (f1, f2, ...)
    if body_main:
        fig_idx = 1
        for fig in body_main.find_all('fig', recursive=True):
            if sub_article and fig in sub_article.find_all('fig'):
                continue
            old_id = fig.get('id')
            new_id = f"f{fig_idx}"
            fig['id'] = new_id
            if old_id and old_id != new_id:
                for xref in soup.find_all('xref', rid=old_id):
                    if sub_article and xref in sub_article.find_all('xref'):
                        continue
                    xref['rid'] = new_id
            fig_idx += 1

    # D. Prefix all IDs inside <sub-article> with en- to prevent collision
    if sub_article:
        # Sections
        sec_idx_en = 1
        for sec in sub_article.find_all('sec', recursive=True):
            sec['id'] = f"en-sec{sec_idx_en}"
            sec_idx_en += 1

        # Figures
        fig_idx_en = 1
        for fig in sub_article.find_all('fig', recursive=True):
            old_id = fig.get('id')
            new_id = f"en-f{fig_idx_en}"
            fig['id'] = new_id
            if old_id:
                for xref in sub_article.find_all('xref', rid=old_id):
                    xref['rid'] = new_id
            fig_idx_en += 1

        # Tables
        tbl_idx_en = 1
        for tbl in sub_article.find_all('table-wrap', recursive=True):
            old_id = tbl.get('id')
            new_id = f"en-t{tbl_idx_en}"
            tbl['id'] = new_id
            if old_id:
                for xref in sub_article.find_all('xref', rid=old_id):
                    xref['rid'] = new_id
            tbl_idx_en += 1

        # References in sub-article
        ref_idx_en = 1
        for ref in sub_article.find_all('ref', recursive=True):
            old_id = ref.get('id')
            new_id = f"en-B{ref_idx_en}"
            ref['id'] = new_id
            if old_id:
                for xref in sub_article.find_all('xref', rid=old_id):
                    xref['rid'] = new_id
            ref_idx_en += 1

    # 5. Purge front metadata leaked into <body> before first intro section & history sections
    if body_main:
        for elem in list(body_main.find_all(['sec', 'p', 'list'])):
            if elem.find_parent('sub-article'):
                continue
            e_text = elem.get_text(strip=True).lower()
            sec_title = elem.find('title')
            t_txt = sec_title.get_text(strip=True).lower() if sec_title else ''
            
            if elem.name == 'sec' and (t_txt in ["recibido", "aceptado", "received", "accepted"] or any(e_text.startswith(k) for k in ["recibido:", "aceptado:", "received:", "accepted:"])):
                elem.decompose()
            elif any(k in e_text for k in ["licenciatura", "doctorado", "maestría", "maestria", "autor para correspondencia", "orcid.org"]) and not elem.find_parent('sec'):
                elem.decompose()

    # Decompose empty <caption/> tags in table-wrap
    for cap in soup.find_all('caption'):
        if not cap.get_text(strip=True):
            cap.decompose()

    # Clean duplicate prefix titles inside abstract <p> tags
    for abs_tag in soup.find_all(['abstract', 'trans-abstract']):
        for p in abs_tag.find_all('p'):
            if p.string:
                clean_p = re.sub(r'^\s*(?:Introducción|Objetivo|Metodología|Resultados|Conclusiones|Introduction|Objective|Methodology|Results|Conclusions|Introdução)\s*:?\s*', '', p.string, flags=re.IGNORECASE).strip()
                if clean_p:
                    p.string = clean_p

    # 6. Publisher Name & Ref Count Exact
    pub_name = soup.find('publisher-name')
    if pub_name:
        pub_name.string = "Universidad de Sonora, División de Ciencias Biológicas y de la Salud, Departamento de enfermería"

    # Remove duplicate <ref-list> in <sub-article> if main <ref-list> exists
    if sub_article:
        sub_ref_list = sub_article.find('ref-list')
        if sub_ref_list:
            for xref in sub_article.find_all('xref', **{'ref-type': 'bibr'}):
                rid = xref.get('rid', '')
                if rid.startswith('en-B'):
                    xref['rid'] = rid.replace('en-B', 'B')
            sub_ref_list.decompose()

    # Recalculate ref-count
    rc = soup.find('ref-count')
    main_back = soup.find('back')
    if rc and main_back:
        main_refs = main_back.find_all('ref')
        rc['count'] = str(len(main_refs))

    # Fix table citations based on their exact text
    for xref in soup.find_all('xref', attrs={'ref-type': 'table'}):
        txt = xref.get_text(strip=True)
        if 'Tabla 1' in txt: xref['rid'] = 't1'
        elif 'Tabla 2' in txt: xref['rid'] = 't2'
        elif 'Tabla 3' in txt: xref['rid'] = 't3'
        elif 'Tabla 4' in txt: xref['rid'] = 't4'
        elif 'Table 1' in txt: xref['rid'] = 'en-t1'
        elif 'Table 2' in txt: xref['rid'] = 'en-t2'
        elif 'Table 3' in txt: xref['rid'] = 'en-t3'
        elif 'Table 4' in txt: xref['rid'] = 'en-t4'

    # Unificar celdas duplicadas usando colspan="2" y extraer fuente del tbody a table-wrap-foot
    for tbl in soup.find_all('table'):
        # 1. Extract source from tbody
        for tr in tbl.find_all('tr'):
            tr_txt = tr.get_text(strip=True)
            if tr_txt.startswith('Fuente:') or tr_txt.startswith('Source:'):
                tr.decompose()
                table_wrap = tbl.find_parent('table-wrap')
                if table_wrap:
                    tf = table_wrap.find('table-wrap-foot')
                    if not tf:
                        tf = soup.new_tag('table-wrap-foot')
                        fn_tag = soup.new_tag('fn', id="TFN1", **{'fn-type': 'other'})
                        p_tag = soup.new_tag('p')
                        p_tag.string = tr_txt
                        fn_tag.append(p_tag)
                        tf.append(fn_tag)
                        table_wrap.append(tf)

        # 2. Duplicate colspans merge
        for tr in tbl.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) == 2:
                # If there are exactly two TDs and their text is identical
                t1 = tds[0].get_text(strip=True)
                t2 = tds[1].get_text(strip=True)
                if t1 == t2 and t1 != "":
                    tds[0]['colspan'] = "2"
                    tds[1].decompose()

    # Save back
    final_xml = str(soup)
    final_xml = re.sub(r'<\?xml.*?\?>\n?', '', final_xml)
    final_xml = re.sub(r'<!DOCTYPE.*?>\n?', '', final_xml)
    doctype = '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
    final_xml = f'<?xml version="1.0" encoding="utf-8"?>\n{doctype}\n{final_xml.strip()}'
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_xml)
        
    print(f"  ✓ {filename}: Correcciones del experto y normalización estricta aplicadas.")

print("\n¡Todas las correcciones del experto aplicadas exitosamente a los XMLs!")
