from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
import os
import re
import pypandoc
import tempfile
import uuid
import json
from bs4 import BeautifulSoup
from bs4.element import Tag
from dotenv import load_dotenv
from google import genai
from pdf2docx import Converter
from pydantic import BaseModel, Field
from typing import List, Optional

load_dotenv()

# Download pandoc if not installed
try:
    pypandoc.get_pandoc_version()
except OSError:
    pypandoc.download_pandoc()

import unicodedata

def unaccent(s: str) -> str:
    if not s:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

app = FastAPI()

# Mount the static directory to serve index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

# Gemini Client Config
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


# Pydantic Schemas for Metadata Extraction
class Author(BaseModel):
    given_names: str = Field(description="Nombres del autor")
    surname: str = Field(description="Apellidos del autor")
    orcid: Optional[str] = Field(description="ORCID del autor si existe, formato: 0000-0000-0000-0000", default=None)
    email: Optional[str] = Field(description="Correo electrónico del autor", default=None)
    role: Optional[str] = Field(description="Cargo o rol del autor, ej: Abogado, Profesor Investigador", default=None)
    is_corresponding: bool = Field(description="Verdadero si es el autor de correspondencia", default=False)
    affiliation_id: str = Field(description="ID de la afiliación (ej. aff1)")

class Affiliation(BaseModel):
    id: str = Field(description="ID único de esta afiliación, ej: aff1")
    institution: str = Field(description="Nombre principal de la institución o universidad")
    faculty: Optional[str] = Field(description="Facultad o escuela de la institución", default=None)
    department: Optional[str] = Field(description="Departamento o división académica", default=None)
    research_center: Optional[str] = Field(description="Centro, instituto o laboratorio de investigación", default=None)
    city: Optional[str] = Field(description="Ciudad donde se ubica la institución", default=None)
    state: Optional[str] = Field(description="Estado, provincia o entidad federativa", default=None)
    postal_code: Optional[str] = Field(description="Código postal de la institución", default=None)
    country: Optional[str] = Field(description="País de la institución", default=None)

class DateInfo(BaseModel):
    day: Optional[str] = Field(description="Día con dos dígitos", default=None)
    month: Optional[str] = Field(description="Mes con dos dígitos", default=None)
    year: Optional[str] = Field(description="Año con cuatro dígitos", default=None)

class ArticleMetadata(BaseModel):
    article_category: Optional[str] = Field(description="Categoría o tipo de artículo según la revista (ej. Artículo Original, Ensayo, Revisión, etc.)", default=None)
    language: Optional[str] = Field(description="Código ISO de 2 letras del idioma principal del documento ('es', 'en', 'pt')", default="es")
    journal_id: Optional[str] = Field(description="ID o acrónimo corto de la revista si aparece", default=None)
    journal_title: Optional[str] = Field(description="Nombre oficial completo de la revista", default=None)
    publisher_name: Optional[str] = Field(description="Nombre de la institución o editorial publicadora", default=None)
    issn_ppub: Optional[str] = Field(description="ISSN impreso si aparece", default=None)
    issn_epub: Optional[str] = Field(description="ISSN electrónico si aparece", default=None)
    issn: Optional[str] = Field(description="ISSN de la revista si no se especifica tipo", default=None)
    volume: Optional[str] = Field(description="Volumen", default=None)
    issue: Optional[str] = Field(description="Número de revista", default=None)
    elocation_id: Optional[str] = Field(description="e-location ID o identificador de paginación electrónica (ej: e566, e413)", default=None)
    doi: Optional[str] = Field(description="DOI del artículo", default=None)
    article_title_es: Optional[str] = Field(description="Título del artículo en español", default=None)
    article_title_en: Optional[str] = Field(description="Título del artículo en inglés", default=None)
    article_title_pt: Optional[str] = Field(description="Título del artículo en portugués", default=None)
    abstract_es: Optional[str] = Field(description="Resumen en español", default=None)
    abstract_en: Optional[str] = Field(description="Abstract en inglés", default=None)
    abstract_pt: Optional[str] = Field(description="Resumen en portugués (Resumo / Abstrato)", default=None)
    keywords_es: List[str] = Field(description="Palabras clave en español", default_factory=list)
    keywords_en: List[str] = Field(description="Keywords en inglés", default_factory=list)
    keywords_pt: List[str] = Field(description="Palavras-chave en portugués", default_factory=list)
    funding_source: Optional[str] = Field(description="Fuente de financiamiento si está presente", default=None)
    award_id: Optional[str] = Field(description="ID o número de contrato de financiamiento", default=None)
    authors: List[Author] = Field(description="Lista de autores", default_factory=list)
    affiliations: List[Affiliation] = Field(description="Lista de afiliaciones de los autores", default_factory=list)
    received_date: Optional[DateInfo] = Field(description="Fecha de recepción", default=None)
    accepted_date: Optional[DateInfo] = Field(description="Fecha de aceptación", default=None)
    published_date: Optional[DateInfo] = Field(description="Fecha de publicación", default=None)

COUNTRY_ISO_MAP = {
    "mexico": "MX", "méxico": "MX", "mx": "MX",
    "spain": "ES", "españa": "ES", "espana": "ES", "es": "ES",
    "colombia": "CO", "co": "CO",
    "brazil": "BR", "brasil": "BR", "br": "BR",
    "argentina": "AR", "ar": "AR",
    "chile": "CL", "cl": "CL",
    "peru": "PE", "perú": "PE", "pe": "PE",
    "ecuador": "EC", "ec": "EC",
    "cuba": "CU", "cu": "CU",
    "venezuela": "VE", "ve": "VE",
    "united states": "US", "usa": "US", "ee.uu.": "US", "eeuu": "US", "estados unidos": "US", "us": "US",
    "canada": "CA", "canadá": "CA", "ca": "CA",
    "united kingdom": "GB", "uk": "GB", "reino unido": "GB", "gb": "GB",
    "france": "FR", "francia": "FR", "fr": "FR",
    "germany": "DE", "alemania": "DE", "de": "DE",
    "italy": "IT", "italia": "IT", "it": "IT",
    "portugal": "PT", "pt": "PT",
    "uruguay": "UY", "uy": "UY",
    "paraguay": "PY", "py": "PY",
    "bolivia": "BO", "bo": "BO",
    "costa rica": "CR", "cr": "CR",
    "panama": "PA", "panamá": "PA", "pa": "PA",
    "guatemala": "GT", "gt": "GT",
    "honduras": "HN", "hn": "HN",
    "el salvador": "SV", "sv": "SV",
    "nicaragua": "NI", "ni": "NI",
    "dominican republic": "DO", "república dominicana": "DO", "republica dominicana": "DO", "do": "DO",
    "puerto rico": "PR", "pr": "PR"
}

def get_country_iso(country_str: Optional[str]) -> tuple[str, str]:
    if not country_str:
        return "", ""
    clean = country_str.strip()
    clean_unaccent = unaccent(clean).lower()
    for name, code in COUNTRY_ISO_MAP.items():
        if unaccent(name) == clean_unaccent or unaccent(name) in clean_unaccent:
            return clean, code
    if len(clean) == 2 and clean.isalpha():
        return clean.upper(), clean.upper()
    return clean, ""

class RefAuthor(BaseModel):
    surname: str = Field(description="Apellido del autor de la referencia")
    given_names: Optional[str] = Field(description="Nombres del autor", default=None)

class ReferenceItem(BaseModel):
    id: str = Field(description="ID de la referencia, ej. B1, B2", default="B1")
    raw_text: str = Field(description="Texto original completo de la cita bibliográfica")
    publication_type: str = Field(description="Tipo de publicación: journal, book, thesis, conference, webpage, u other", default="other")
    authors: List[RefAuthor] = Field(description="Lista de autores de la cita", default_factory=list)
    article_title: Optional[str] = Field(description="Título del artículo o capítulo", default=None)
    source: Optional[str] = Field(description="Nombre de la revista, libro, sitio web o conferencia", default=None)
    publisher_name: Optional[str] = Field(description="Nombre de la editorial o institución publicadora", default=None)
    year: Optional[str] = Field(description="Año de publicación (4 dígitos)", default=None)
    volume: Optional[str] = Field(description="Volumen", default=None)
    issue: Optional[str] = Field(description="Número de revista", default=None)
    fpage: Optional[str] = Field(description="Página inicial", default=None)
    lpage: Optional[str] = Field(description="Página final", default=None)
    doi: Optional[str] = Field(description="DOI de la referencia si existe", default=None)
    url: Optional[str] = Field(description="URL o enlace si existe", default=None)

class ReferenceList(BaseModel):
    references: List[ReferenceItem] = Field(description="Lista de referencias bibliográficas extraídas", default_factory=list)

def extract_docx_headers_text(docx_path: str) -> str:
    """Extrae el texto ubicado en los encabezados y pies de página del archivo DOCX (que Pandoc omite)."""
    try:
        import docx
        import xml.etree.ElementTree as ET
        doc = docx.Document(docx_path)
        header_texts = []
        for s in doc.sections:
            for h in (s.first_page_header, s.header, s.first_page_footer, s.footer):
                if h and h._element is not None:
                    root = ET.fromstring(h._element.xml)
                    texts = [elem.text for elem in root.iter() if elem.text and elem.text.strip()]
                    if texts:
                        header_texts.append(" ".join(texts))
        return "\n".join(header_texts)
    except Exception as e:
        print(f"Error extrayendo encabezados de DOCX: {e}")
        return ""

def clean_article_title(title_text: str) -> str:
    if not title_text:
        return title_text
    clean = title_text.strip()
    category_prefixes = [
        "INVESTIGACIÓN CUALITATIVA", "INVESTIGACIÓN", "RESEARCH", "ARTÍCULO ORIGINAL",
        "ORIGINAL ARTICLE", "ARTIGO ORIGINAL", "REVISIÓN", "REVIEW", "ARTÍCULO DE REVISIÓN",
        "EDITORIAL", "CARTA AL EDITOR", "CASE REPORT", "REPORTE DE CASO"
    ]
    for cat in category_prefixes:
        if clean.upper().startswith(cat):
            clean = clean[len(cat):].strip().lstrip(':').lstrip('-').strip()
    return clean

def format_abstract_text(text: str) -> str:
    if not text:
        return text
    formatted = text
    # Insertar dos puntos y espacio si encabezados estructurados están pegados a la siguiente palabra (ej. MetodologíaPara -> Metodología: Para)
    formatted = re.sub(r'\b(Introducción|Objetivo|Metodología|Resultados|Conclusiones|Introduction|Objective|Methodology|Results|Conclusions|Introdução|Metodologia|Conclusões)\s*(?=[A-ZÁÉÍÓÚ])', r'\1: ', formatted)
    formatted = re.sub(r':\s*:', ':', formatted)
    formatted = re.sub(r'([\.a-zA-ZáéíóúÁÉÍÓÚñÑ])(?=[A-ZÁÉÍÓÚ][a-zâêîôûãõçáéíóúñ]+\s*:)', r'\1 ', formatted)
    formatted = re.sub(r':(?=[A-ZÁÉÍÓÚa-z])', ': ', formatted)
    formatted = re.sub(r'\s+', ' ', formatted).strip()
    return formatted

def build_structured_abstract_xml(soup: BeautifulSoup, abstract_text: str, tag_name: str = "abstract", lang: str = None) -> Tag:
    attrs = {}
    if lang:
        attrs["xml:lang"] = lang
    abs_tag = soup.new_tag(tag_name, **attrs)
    
    clean_txt = format_abstract_text(abstract_text) if abstract_text else ""
    clean_txt = re.sub(r'^\s*(?:Resumen|Abstract|Resumo)\b[\s:]*', '', clean_txt, flags=re.IGNORECASE).strip()
    if not clean_txt or clean_txt in ["Resumen no disponible.", "Abstract not available."]:
        title = soup.new_tag("title")
        title.string = "Abstract:" if (lang == "en" or tag_name == "trans-abstract") else "Resumen:"
        abs_tag.append(title)
        p = soup.new_tag("p")
        p.string = clean_txt if clean_txt else ("Abstract not available." if lang == "en" else "Resumen no disponible.")
        abs_tag.append(p)
        return abs_tag

    # Buscar secciones estructuradas usando regex (Español, Inglés y Portugués)
    section_pattern = re.compile(
        r'(Introducción|Objetivo|Metodología|Resultados|Conclusiones|Introduction|Objective|Methodology|Results|Conclusions|Introdução|Introducao|Metodologia|Conclusões|Conclusoes|Resumo|Abstrato):\s*',
        re.IGNORECASE
    )
    
    matches = list(section_pattern.finditer(clean_txt))
    if matches:
        first_hdr = matches[0].group(1).lower()
        if matches[0].start() > 0 or first_hdr not in ["introduccion", "introducción", "introduction", "introducao", "introdução"]:
            if lang == "en":
                prefix_header = "Introduction: "
            elif lang == "pt":
                prefix_header = "Introdução: "
            else:
                prefix_header = "Introducción: "
            
            clean_txt = prefix_header + clean_txt
            matches = list(section_pattern.finditer(clean_txt))
            
        for i in range(len(matches)):
            sec_title_name = matches[i].group(1).capitalize() + ":"
            start_pos = matches[i].end()
            end_pos = matches[i+1].start() if i + 1 < len(matches) else len(clean_txt)
            sec_body_text = clean_txt[start_pos:end_pos].strip()
            sec_body_text = re.sub(r'^(?:Introducción|Objetivo|Metodología|Resultados|Conclusiones|Introduction|Objective|Methodology|Results|Conclusions|Introdução|Introducao|Metodologia|Conclusões|Conclusoes|Resumo|Abstrato)[:\s]*', '', sec_body_text, flags=re.IGNORECASE).strip()
            if not sec_body_text:
                continue
            
            sec = soup.new_tag("sec")
            t_tag = soup.new_tag("title")
            t_tag.string = sec_title_name
            sec.append(t_tag)
            
            p_tag = soup.new_tag("p")
            p_tag.string = sec_body_text
            sec.append(p_tag)
            
            abs_tag.append(sec)
    else:
        title = soup.new_tag("title")
        title.string = "Abstract:" if (lang == "en" or tag_name == "trans-abstract") else "Resumen:"
        abs_tag.append(title)
        p = soup.new_tag("p")
        p.string = clean_txt
        abs_tag.append(p)
        
    return abs_tag

async def extract_metadata_from_text(text: str) -> tuple[ArticleMetadata, bool]:
    api_key = os.getenv("GEMINI_API_KEY")
    used_fallback = False
    metadata = None
    if not api_key:
        print("Aviso: No hay GEMINI_API_KEY configurada. Extrayendo metadatos determinísticamente del DOCX...")
        used_fallback = True
    else:
        prompt = """
    Analiza el siguiente texto extraído de un artículo científico (DOCX/PDF) y extrae los metadatos en un formato JSON estricto.
    REGLAS DE EXTRACCIÓN:
    - Extrae el idioma principal del artículo ('es', 'en', 'pt', etc.) en el campo 'language'.
    - Si el artículo contiene título o resumen en varios idiomas (español, inglés, portugués), extrae cada uno en su campo correspondiente.
    - Extrae el nombre de la revista (journal_title), ID corto (journal_id), editorial/publicador (publisher_name), ISSN impreso (issn_ppub), ISSN electrónico (issn_epub), volumen, número (issue), e-location ID (elocation_id) y DOI si aparecen en el encabezado, pie o cuerpo del texto.
    - Para los autores:
      1. Identifica el nombre completo (surname, given_names).
      2. Asocia la afiliación correspondiente usando el mismo ID (ej. "aff1") para autores de la misma institución.
      3. Identifica si es el autor de correspondencia (is_corresponding: true) y su correo electrónico (email).
      4. Extrae su ORCID si está presente (orcid: "0000-0000-0000-0000").
    - Para las afiliaciones:
      1. Asigna un ID único (ej. "aff1", "aff2").
      2. institución: Nombre principal de la universidad u organización.
      3. facultad: Nombre de la facultad o división.
      4. departamento: Nombre del departamento o escuela.
      5. centro de investigación: Centro o instituto si existe.
      6. ciudad, estado, país y código postal según aparezcan en el texto.
    - IMPORTANTE: Extrae exclusivamente la información real presente en el documento. No inventes datos ni asumas instituciones o revistas por defecto. Si un campo no existe en el texto, déjalo nulo.
    
    Texto:
    """ + text[:80000]
    
    import time
    metadata = None
    if client:
        models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-lite']
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': ArticleMetadata,
                        'temperature': 0.1
                    }
                )
                metadata = ArticleMetadata.model_validate_json(response.text)
                break
            except Exception as e:
                print(f"Modelo {model_name} falló extrayendo metadatos: {e}")
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"Cambiando a siguiente modelo por límite de cuota 429...")
                    continue
                time.sleep(3)
            
    if not metadata:
        used_fallback = True
        metadata = ArticleMetadata(article_title_es="Sin Título")
        
    # Regex fallback desde encabezados si falta DOI, elocation_id, volume, issue o ISSNs
    if not metadata.doi or metadata.doi == "10.0000/0000":
        doi_match = re.search(r'10\.\d{4,9}/[^\s<"\']+', text)
        if doi_match:
            metadata.doi = doi_match.group(0).rstrip('.')
            
    if not metadata.elocation_id or metadata.elocation_id == "e000":
        eloc_match = re.search(r':\s*(e\d+)', text, re.IGNORECASE) or re.search(r'\b(e\d{3,6})\b', text, re.IGNORECASE)
        if eloc_match:
            metadata.elocation_id = eloc_match.group(1)
            
    if not metadata.volume:
        vol_match = re.search(r'(?:vol(?:umen)?|volume|v\.)\s*(\d+)', text, re.IGNORECASE) or re.search(r'\b(?:19|20)\d{2}\s*;\s*(\d+)', text) or re.search(r'\b(\d+)\s*\(\s*\d+\s*\)\s*:', text)
        if vol_match:
            metadata.volume = vol_match.group(1)
            
    if not metadata.issue:
        iss_match = re.search(r'(?:no|núm|num|número|issue|n\.)\s*(\d+)', text, re.IGNORECASE) or re.search(r'\(\s*(\d+)\s*\)\s*:', text)
        if iss_match:
            metadata.issue = iss_match.group(1)

    if not metadata.issn and not metadata.issn_epub and not metadata.issn_ppub:
        issn_matches = re.findall(r'(?:ISSN|e-ISSN|ISSN-e|p-ISSN)[:\s\.]*(\d{4}-\d{3}[\dX])', text, re.IGNORECASE)
        if issn_matches:
            metadata.issn = issn_matches[0]

    # Extracción determinista de Revista / Editorial desde encabezados
    if not metadata.journal_title:
        j_match = re.search(r'^(?:Revista|Journal of|Acta|Cuadernos de|Anales de|Boletín)\s+[^\n\d,;]+', text, re.MULTILINE | re.IGNORECASE)
        if j_match:
            metadata.journal_title = j_match.group(0).strip()
            if not metadata.journal_id:
                metadata.journal_id = re.sub(r'[^a-zA-Z0-9]', '', unaccent(metadata.journal_title)).lower()[:15]

    # Extracción determinista de Fechas (Recepción / Aceptación)
    if not metadata.received_date:
        rec_m = re.search(r'(?:recibido|received|recebido)[\s:]*(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', text, re.IGNORECASE)
        if rec_m:
            metadata.received_date = DateInfo(day=rec_m.group(1).zfill(2), month=rec_m.group(2).zfill(2), year=rec_m.group(3))
    if not metadata.accepted_date:
        acc_m = re.search(r'(?:aceptado|accepted|aceito)[\s:]*(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', text, re.IGNORECASE)
        if acc_m:
            metadata.accepted_date = DateInfo(day=acc_m.group(1).zfill(2), month=acc_m.group(2).zfill(2), year=acc_m.group(3))

    # Detección determinista de idioma principal
    if not metadata.language or metadata.language == "es":
        text_lower = text.lower()
        pt_score = sum(1 for w in [" introdução ", " resumo ", " palavras-chave ", " metodologia ", " conclusões "] if w in text_lower)
        en_score = sum(1 for w in [" introduction ", " abstract ", " keywords ", " methodology ", " results ", " conclusions "] if w in text_lower)
        es_score = sum(1 for w in [" introducción ", " resumen ", " palabras clave ", " metodología ", " resultados ", " conclusiones "] if w in text_lower)
        if en_score > es_score and en_score > pt_score:
            metadata.language = "en"
        elif pt_score > es_score and pt_score > en_score:
            metadata.language = "pt"
        else:
            metadata.language = "es"

    # Extracción determinista de Título si no fue extraído o quedó truncado
    if not metadata.article_title_es or metadata.article_title_es in ["Sin Título", "Título no disponible"] or metadata.article_title_es.strip().endswith("de") or len(metadata.article_title_es) < 25:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        title_candidates = []
        for line in lines[:15]:
            line_low = line.lower()
            if any(k in line_low for k in ["issn", "doi:", "http", "www.", "volumen", "volume", "los contenidos de este artículo", "page", "página", "editorial", "copyright", "licencia", "creative commons", "open access"]):
                continue
            if line.isupper() or len(line) > 15:
                if any(line.upper().startswith(p) for p in ["INVESTIGACIÓN", "REVIEW", "REVISIÓN", "ARTÍCULO", "RESEARCH"]):
                    line = re.sub(r'^(INVESTIGACIÓN CUALITATIVA|INVESTIGACIÓN|RESEARCH|ARTÍCULO ORIGINAL|ORIGINAL ARTICLE|ARTIGO ORIGINAL|REVISIÓN|REVIEW|ARTÍCULO DE REVISIÓN|EDITORIAL|CARTA AL EDITOR|CASE REPORT|REPORTE DE CASO)\s*', '', line, flags=re.IGNORECASE).strip()
                if line:
                    title_candidates.append(line)
                connector_words = ("de", "la", "el", "y", "un", "una", "del", "los", "las", "con", "por", "para", "en", "al", "o", "a", "of", "and", "in", "to", "for", "with", "on")
                if len(" ".join(title_candidates)) > 45 and not any(line.lower().rstrip('.').endswith(" " + cw) or line.lower().rstrip('.').endswith(cw) for cw in connector_words):
                    break
        if title_candidates:
            metadata.article_title_es = " ".join(title_candidates)

    if metadata.article_title_es:
        metadata.article_title_es = clean_article_title(metadata.article_title_es)
    if metadata.article_title_en:
        metadata.article_title_en = clean_article_title(metadata.article_title_en)
        if metadata.article_title_es and metadata.article_title_en:
            en_words = metadata.article_title_en.split()
            if len(en_words) >= 3:
                en_prefix = " ".join(en_words[:3])
                if en_prefix in metadata.article_title_es:
                    metadata.article_title_es = metadata.article_title_es.split(en_prefix)[0].strip().rstrip(':').strip()
    if metadata.article_title_pt:
        metadata.article_title_pt = clean_article_title(metadata.article_title_pt)

    # Extracción determinista de Resumen (Español)
    if not metadata.abstract_es or metadata.abstract_es == "Resumen no disponible.":
        abs_es_match = re.search(r'Resumen:\s*(.*?)(?=\n\s*(?:Abstract:|Palabras clave:|Keywords:|Palavras-chave:|1\.|I\.)|$)', text, re.DOTALL | re.IGNORECASE)
        if abs_es_match:
            metadata.abstract_es = format_abstract_text(abs_es_match.group(1).strip())
    else:
        metadata.abstract_es = format_abstract_text(metadata.abstract_es)

    # Extracción determinista de Abstract (Inglés)
    if not metadata.abstract_en or metadata.abstract_en in ["Abstract not available.", "Resumen no disponible."]:
        abs_en_match = re.search(r'Abstract:\s*(.*?)(?=\n\s*(?:Resumen:|Palabras clave:|Keywords:|Key words:|Palavras-chave:|1\.|I\.)|$)', text, re.DOTALL | re.IGNORECASE)
        if abs_en_match:
            metadata.abstract_en = format_abstract_text(abs_en_match.group(1).strip())
    else:
        metadata.abstract_en = format_abstract_text(metadata.abstract_en)

    # Extracción determinista de Resumen (Portugués)
    if not metadata.abstract_pt:
        abs_pt_match = re.search(r'(?:Resumo|Abstrato):\s*(.*?)(?=\n\s*(?:Abstract:|Resumen:|Palabras clave:|Keywords:|Palavras-chave:|1\.|I\.)|$)', text, re.DOTALL | re.IGNORECASE)
        if abs_pt_match:
            metadata.abstract_pt = format_abstract_text(abs_pt_match.group(1).strip())
    else:
        metadata.abstract_pt = format_abstract_text(metadata.abstract_pt)

    # Extracción determinista de Palabras Clave (Español)
    if not metadata.keywords_es or metadata.keywords_es == ["Palabra clave no disponible"] or len(metadata.keywords_es) <= 1:
        kw_es_match = re.search(r'Palabras\s+clave:\s*(.*?)(?=\n\s*(?:Abstract|Resumen|Introducción|Introduction|1\.|I\.)|$)', text, re.DOTALL | re.IGNORECASE)
        if kw_es_match:
            kw_str = kw_es_match.group(1).replace('\n', ' ').strip().rstrip('.')
            metadata.keywords_es = [k.strip() for k in re.split(r'[;,]', kw_str) if k.strip()]

    # Extracción determinista de Keywords (Inglés)
    if not metadata.keywords_en or metadata.keywords_en in [["Keyword not available"], ["Palabra clave no disponible"]] or len(metadata.keywords_en) <= 1:
        kw_en_match = re.search(r'(?:Keywords|Key\s+words):\s*(.*?)(?=\n\s*(?:Abstract|Resumen|Introducción|Introduction|Abstrato|Palavras-chave|1\.|I\.)|$)', text, re.DOTALL | re.IGNORECASE)
        if kw_en_match:
            kw_str = kw_en_match.group(1).replace('\n', ' ').strip().rstrip('.')
            metadata.keywords_en = [k.strip() for k in re.split(r'[;,]', kw_str) if k.strip()]

    # Extracción determinista de Palavras-chave (Portugués)
    if not metadata.keywords_pt:
        kw_pt_match = re.search(r'Palavras-chave:\s*(.*?)(?=\n\s*(?:Abstract|Resumen|Introdução|Introduction|1\.|I\.)|$)', text, re.DOTALL | re.IGNORECASE)
        if kw_pt_match:
            kw_str = kw_pt_match.group(1).replace('\n', ' ').strip().rstrip('.')
            metadata.keywords_pt = [k.strip() for k in re.split(r'[;,]', kw_str) if k.strip()]

    # Sanitizar prefijos en las palabras clave extraídas
    if metadata.keywords_es:
        metadata.keywords_es = [re.sub(r'^(?:Palabras?\s+clave|Keywords?|Key\s+words)[:\s]*', '', k, flags=re.IGNORECASE).strip() for k in metadata.keywords_es if k.strip()]
    if metadata.keywords_en:
        metadata.keywords_en = [re.sub(r'^(?:Palabras?\s+clave|Keywords?|Key\s+words)[:\s]*', '', k, flags=re.IGNORECASE).strip() for k in metadata.keywords_en if k.strip()]
    if metadata.keywords_pt:
        metadata.keywords_pt = [re.sub(r'^(?:Palavras-chave|Palabras?\s+clave|Keywords?|Key\s+words)[:\s]*', '', k, flags=re.IGNORECASE).strip() for k in metadata.keywords_pt if k.strip()]

    return metadata, used_fallback

def enrich_front_metadata_from_soup(soup: BeautifulSoup, metadata: ArticleMetadata):
    """
    Enriquece los metadatos inspeccionando la estructura nativa de párrafos, secciones y notas al pie del soup
    (títulos, autores, notas al pie de afiliación, resumen y abstract narrativo/estructurado, palabras clave).
    """
    body = soup.find('body')
    if not body:
        return
        
    all_p = body.find_all(['p', 'sec'])
    first_texts = [p.get_text(strip=True) for p in all_p[:20] if p.get_text(strip=True)]
    
    # 1. Títulos, Categoría y Autores
    title_es, title_en, authors_raw = None, None, []
    for t in first_texts:
        t_low = unaccent(t.lower())
        if any(k in t_low for k in ['sumario', 'resumen', 'abstract', 'palabras clave', 'keywords', 'introduccion', 'introduction']):
            break
        if t in ['Artículos', 'Articulos', 'Investigación', 'Investigacion', 'Revisión', 'Revision', 'Original Article', 'Artículo Original']:
            if not metadata.article_category:
                metadata.article_category = t
            continue
        if not title_es and len(t) > 20:
            title_es = t
        elif title_es and not title_en and len(t) > 20 and not re.search(r'\d+$', t):
            title_en = t
        elif re.search(r'[A-Za-z\s]+[\d\*†‡F]+$', t) or (len(t.split()) <= 6 and not re.search(r'[;:\.]', t) and not any(k in t_low for k in ["vol", "no", "issn", "doi", "http"])):
            authors_raw.append(t)
            
    if (not metadata.article_title_es or metadata.article_title_es in ['Sin Título', 'Título no disponible']) and title_es:
        metadata.article_title_es = clean_article_title(title_es)
    if not metadata.article_title_en and title_en:
        metadata.article_title_en = clean_article_title(title_en)
        
    # Extraer autores si no existen
    if not metadata.authors and authors_raw:
        for idx, a_raw in enumerate(authors_raw, 1):
            clean_name = re.sub(r'[\d\*†‡F]+$', '', a_raw).strip()
            parts = clean_name.split()
            if len(parts) >= 3:
                given, surname = ' '.join(parts[:-2]), ' '.join(parts[-2:])
            elif len(parts) == 2:
                given, surname = parts[0], parts[1]
            else:
                given, surname = parts[0], ''
            metadata.authors.append(Author(given_names=given, surname=surname, affiliation_id=f'aff{idx}'))
            
    # Extraer afiliaciones desde las primeras notas al pie
    if not metadata.affiliations and metadata.authors:
        for idx, author in enumerate(metadata.authors, 1):
            target_fn = soup.find('fn', id=f'fn{idx}')
            if target_fn:
                fn_text = target_fn.get_text(separator=' ', strip=True)
                clean_fn = re.sub(r'^\s*[\d\*†‡F\.]+\s*', '', fn_text).strip()
                email_m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', clean_fn)
                if email_m:
                    author.email = email_m.group(0)
                orcid_m = re.search(r'000\d-[\dXx]{4}-[\dXx]{4}-[\dXx]{4}', clean_fn)
                if orcid_m:
                    author.orcid = orcid_m.group(0)
                inst_m = re.search(r'(?:Universidad|Instituto|Facultad|Colegio|Centro|Secretaría|Escuela)\s+[^\.,;]+', clean_fn, re.IGNORECASE)
                inst = inst_m.group(0).strip() if inst_m else clean_fn[:80].strip()
                
                country_name = "México"
                for c_name in COUNTRY_ISO_MAP.keys():
                    if len(c_name) > 3 and c_name in clean_fn.lower():
                        country_name = c_name.capitalize()
                        break
                        
                metadata.affiliations.append(Affiliation(id=author.affiliation_id, institution=inst, country=country_name))
                target_fn.decompose()

    # 2. Resumen & Abstract & Keywords
    current_mode = None
    abs_es_list, abs_en_list = [], []
    for p in body.find_all('p'):
        txt = p.get_text(strip=True)
        txt_low = unaccent(txt.lower())
        if txt_low in ['resumen', 'resumo']:
            current_mode = 'resumen'
            continue
        elif txt_low in ['abstract', 'summary']:
            current_mode = 'abstract'
            continue
        elif txt_low.startswith(('palabras clave', 'palabras claves', 'palavras-chave')):
            current_mode = None
            if not metadata.keywords_es or metadata.keywords_es in [['Palabra clave no disponible'], ['Palabras clave']]:
                raw_kw = re.sub(r'^(?:Palabras\s+claves?|Palavras-chave)[:\s]*', '', txt, flags=re.I)
                metadata.keywords_es = [k.strip().rstrip('.') for k in re.split(r'[;,]', raw_kw) if k.strip()]
            continue
        elif txt_low.startswith(('keywords', 'key words')):
            current_mode = None
            if not metadata.keywords_en or metadata.keywords_en in [['Keyword not available'], ['Palabra clave no disponible']]:
                raw_kw = re.sub(r'^(?:Keywords?|Key\s+words?)[:\s]*', '', txt, flags=re.I)
                metadata.keywords_en = [k.strip().rstrip('.') for k in re.split(r'[;,]', raw_kw) if k.strip()]
            continue
        elif any(txt_low.startswith(h) for h in ['i. ', '1. ', 'introduccion', 'introduction', 'sumario:']):
            current_mode = None
            
        if current_mode == 'resumen':
            abs_es_list.append(txt)
        elif current_mode == 'abstract':
            abs_en_list.append(txt)

    if abs_es_list and (not metadata.abstract_es or metadata.abstract_es in ['Resumen no disponible.', 'Abstract not available.']):
        metadata.abstract_es = format_abstract_text('\n'.join(abs_es_list))
    if abs_en_list and (not metadata.abstract_en or metadata.abstract_en in ['Abstract not available.', 'Resumen no disponible.']):
        metadata.abstract_en = format_abstract_text('\n'.join(abs_en_list))

def build_scielo_front(soup: BeautifulSoup, metadata: ArticleMetadata) -> BeautifulSoup:
    """Modifica el soup XML inyectando la estructura de SciELO en el <front> generada dinámicamente a partir del documento."""
    enrich_front_metadata_from_soup(soup, metadata)
    new_front = soup.new_tag("front")
    
    # 2. Journal Meta
    journal_meta = soup.new_tag("journal-meta")
    
    j_id_val = (metadata.journal_id or "").strip()
    j_title_val = (metadata.journal_title or "").strip()
    
    if not j_id_val and j_title_val:
        j_id_val = re.sub(r'[^a-zA-Z0-9]', '', unaccent(j_title_val)).lower()[:20]
        
    if j_id_val:
        jid = soup.new_tag("journal-id", **{"journal-id-type": "publisher-id"})
        jid.string = j_id_val
        journal_meta.append(jid)
        
    if j_title_val:
        jtg = soup.new_tag("journal-title-group")
        jt = soup.new_tag("journal-title")
        jt.string = j_title_val
        jtg.append(jt)
        
        ajt = soup.new_tag("abbrev-journal-title", **{"abbrev-type": "publisher"})
        ajt.string = j_title_val[:25]
        jtg.append(ajt)
        journal_meta.append(jtg)
        
    if metadata.issn_ppub:
        issn_ppub = soup.new_tag("issn", **{"pub-type": "ppub"})
        issn_ppub.string = metadata.issn_ppub
        journal_meta.append(issn_ppub)
    if metadata.issn_epub:
        issn_epub = soup.new_tag("issn", **{"pub-type": "epub"})
        issn_epub.string = metadata.issn_epub
        journal_meta.append(issn_epub)
    elif metadata.issn:
        issn_tag = soup.new_tag("issn", **{"pub-type": "epub"})
        issn_tag.string = metadata.issn
        journal_meta.append(issn_tag)
        
    if metadata.publisher_name:
        publisher = soup.new_tag("publisher")
        pub_name = soup.new_tag("publisher-name")
        pub_name.string = metadata.publisher_name
        publisher.append(pub_name)
        journal_meta.append(publisher)
        
    if len(journal_meta.contents) > 0:
        new_front.append(journal_meta)
        
    # 3. Article Meta
    article_meta = soup.new_tag("article-meta")
    if metadata.doi:
        doi = soup.new_tag("article-id", **{"pub-id-type": "doi"})
        doi.string = metadata.doi
        article_meta.append(doi)
        
    if metadata.elocation_id:
        eloc_num = re.sub(r'^[eE]', '', metadata.elocation_id)
        if eloc_num.isdigit():
            pub_id_other = soup.new_tag("article-id", **{"pub-id-type": "other"})
            pub_id_other.string = eloc_num.zfill(5)
            article_meta.append(pub_id_other)
        
    if metadata.article_category:
        article_categories = soup.new_tag("article-categories")
        subj_group = soup.new_tag("subj-group", **{"subj-group-type": "heading"})
        subject = soup.new_tag("subject")
        subject.string = metadata.article_category
        subj_group.append(subject)
        article_categories.append(subj_group)
        article_meta.append(article_categories)
        
    title_group = soup.new_tag("title-group")
    lang_code = (metadata.language or "es").lower()
    
    if lang_code == "en" and metadata.article_title_en:
        primary_title = clean_article_title(metadata.article_title_en)
        trans_titles = [("es", metadata.article_title_es), ("pt", metadata.article_title_pt)]
    elif lang_code == "pt" and metadata.article_title_pt:
        primary_title = clean_article_title(metadata.article_title_pt)
        trans_titles = [("es", metadata.article_title_es), ("en", metadata.article_title_en)]
    else:
        primary_title = clean_article_title(metadata.article_title_es) if metadata.article_title_es else (clean_article_title(metadata.article_title_en) if metadata.article_title_en else "Título no disponible")
        trans_titles = [("pt", metadata.article_title_pt), ("en", metadata.article_title_en)]
        
    article_title = soup.new_tag("article-title")
    article_title.string = primary_title
    title_group.append(article_title)
    
    for t_lang, t_val in trans_titles:
        if t_val:
            clean_t = clean_article_title(t_val)
            if clean_t and clean_t != primary_title:
                trans_tg = soup.new_tag("trans-title-group", **{"xml:lang": t_lang})
                trans_t = soup.new_tag("trans-title")
                trans_t.string = clean_t
                trans_tg.append(trans_t)
                title_group.append(trans_tg)
                
    article_meta.append(title_group)
    
    # Authors and Affiliations
    contrib_group = soup.new_tag("contrib-group")
    corresp_author = None
    for author in metadata.authors:
        contrib = soup.new_tag("contrib", **{"contrib-type": "author"})
        if author.orcid:
            orcid_match = re.search(r'\d{4}-\d{4}-\d{4}-[\dX]{4}', author.orcid, re.IGNORECASE)
            orcid_val = orcid_match.group() if orcid_match else author.orcid
            orcid = soup.new_tag("contrib-id", **{"contrib-id-type": "orcid"})
            orcid.string = orcid_val
            contrib.append(orcid)
            
        name = soup.new_tag("name")
        surname = soup.new_tag("surname")
        surname.string = author.surname
        given = soup.new_tag("given-names")
        given.string = author.given_names
        name.append(surname)
        name.append(given)
        contrib.append(name)
        
        xref = soup.new_tag("xref", **{"ref-type": "aff", "rid": author.affiliation_id})
        contrib.append(xref)
        
        if author.role:
            role = soup.new_tag("role")
            role.string = author.role
            contrib.append(role)
        
        if author.is_corresponding:
            corresp_author = author
            xref_corresp = soup.new_tag("xref", **{"ref-type": "corresp", "rid": "c1"})
            sup = soup.new_tag("sup")
            sup.string = "*"
            xref_corresp.append(sup)
            contrib.append(xref_corresp)
            
        contrib_group.append(contrib)
        
    for aff in metadata.affiliations:
        aff_tag = soup.new_tag("aff", id=aff.id)
        
        match = re.search(r'\d+', aff.id)
        if match:
            label = soup.new_tag("label")
            label.string = match.group()
            aff_tag.append(label)
            
        inst = soup.new_tag("institution", **{"content-type": "original"})
        original_parts = [aff.institution]
        if aff.faculty: original_parts.append(aff.faculty)
        if aff.research_center: original_parts.append(aff.research_center)
        if aff.department: original_parts.append(aff.department)
        if aff.city: original_parts.append(aff.city)
        if aff.state: original_parts.append(aff.state)
        if aff.country: original_parts.append(aff.country)
        inst.string = ", ".join(p for p in original_parts if p)
        aff_tag.append(inst)
        
        if aff.institution:
            inst_orgname = soup.new_tag("institution", **{"content-type": "orgname"})
            inst_orgname.string = aff.institution
            aff_tag.append(inst_orgname)
            
        orgdivs = []
        if aff.faculty: orgdivs.append(aff.faculty)
        if aff.research_center: orgdivs.append(aff.research_center)
        if aff.department: orgdivs.append(aff.department)
        
        if len(orgdivs) >= 1:
            inst_orgdiv1 = soup.new_tag("institution", **{"content-type": "orgdiv1"})
            inst_orgdiv1.string = orgdivs[0]
            aff_tag.append(inst_orgdiv1)
        if len(orgdivs) >= 2:
            inst_orgdiv2 = soup.new_tag("institution", **{"content-type": "orgdiv2"})
            inst_orgdiv2.string = orgdivs[1]
            aff_tag.append(inst_orgdiv2)
            
        if aff.city or aff.state or aff.postal_code:
            addr_line = soup.new_tag("addr-line")
            if aff.postal_code:
                pc = soup.new_tag("postal-code")
                pc.string = aff.postal_code
                addr_line.append(pc)
            if aff.city:
                city = soup.new_tag("city")
                city.string = aff.city
                addr_line.append(city)
            if aff.state:
                state = soup.new_tag("state")
                state.string = aff.state
                addr_line.append(state)
            aff_tag.append(addr_line)
            
        if aff.country:
            c_name, iso_code = get_country_iso(aff.country)
            country_attrs = {"country": iso_code} if iso_code else {}
            country_tag = soup.new_tag("country", **country_attrs)
            country_tag.string = c_name if c_name else aff.country
            aff_tag.append(country_tag)
            
        for author in metadata.authors:
            if author.affiliation_id == aff.id and author.email:
                clean_email = re.sub(r'^file:///[^\s]+', '', author.email.strip())
                if clean_email:
                    email_tag = soup.new_tag("email")
                    email_tag.string = clean_email
                    aff_tag.append(email_tag)
                    break
        
        contrib_group.append(aff_tag)
        
    if metadata.authors:
        article_meta.append(contrib_group)
        
    if corresp_author:
        author_notes = soup.new_tag("author-notes")
        corresp = soup.new_tag("corresp", id="c1")
        label = soup.new_tag("label")
        label.string = "*"
        corresp.append(label)
        corresp.append(f"Autor para correspondencia: {corresp_author.given_names} {corresp_author.surname} Correo-e: ")
        if corresp_author.email:
            email_tag = soup.new_tag("email")
            email_tag.string = corresp_author.email
            corresp.append(email_tag)
        author_notes.append(corresp)
        article_meta.append(author_notes)
        
    # Pub dates dinámicas
    import datetime
    pub_year = None
    if metadata.published_date and metadata.published_date.year:
        pub_year = metadata.published_date.year
    elif metadata.accepted_date and metadata.accepted_date.year:
        pub_year = metadata.accepted_date.year
    elif metadata.received_date and metadata.received_date.year:
        pub_year = metadata.received_date.year
    else:
        pub_year = str(datetime.datetime.now().year)
        
    pub_date = soup.new_tag("pub-date", **{"date-type": "pub", "publication-format": "electronic"})
    day = soup.new_tag("day")
    day.string = metadata.published_date.day if (metadata.published_date and metadata.published_date.day) else "01"
    month = soup.new_tag("month")
    month.string = metadata.published_date.month if (metadata.published_date and metadata.published_date.month) else "01"
    year = soup.new_tag("year")
    year.string = pub_year
    pub_date.append(day)
    pub_date.append(month)
    pub_date.append(year)
    article_meta.append(pub_date)
    
    pub_date_coll = soup.new_tag("pub-date", **{"date-type": "collection", "publication-format": "electronic"})
    season = soup.new_tag("season")
    season.string = "Jan-Dec"
    year_coll = soup.new_tag("year")
    year_coll.string = year.string
    pub_date_coll.append(season)
    pub_date_coll.append(year_coll)
    article_meta.append(pub_date_coll)
        
    # Volume and Issue
    if metadata.volume:
        vol = soup.new_tag("volume")
        vol.string = metadata.volume
        article_meta.append(vol)
    if metadata.issue:
        iss = soup.new_tag("issue")
        iss.string = metadata.issue
        article_meta.append(iss)
        
    # Elocation-id
    eloc = soup.new_tag("elocation-id")
    eloc.string = metadata.elocation_id if metadata.elocation_id else "e000"
    article_meta.append(eloc)
        
    # History
    if metadata.received_date or metadata.accepted_date:
        history = soup.new_tag("history")
        if metadata.received_date and metadata.received_date.year:
            date_rec = soup.new_tag("date", **{"date-type": "received"})
            if metadata.received_date.day:
                d = soup.new_tag("day")
                d.string = metadata.received_date.day
                date_rec.append(d)
            if metadata.received_date.month:
                m = soup.new_tag("month")
                m.string = metadata.received_date.month
                date_rec.append(m)
            y = soup.new_tag("year")
            y.string = metadata.received_date.year
            date_rec.append(y)
            history.append(date_rec)
            
        if metadata.accepted_date and metadata.accepted_date.year:
            date_acc = soup.new_tag("date", **{"date-type": "accepted"})
            if metadata.accepted_date.day:
                d = soup.new_tag("day")
                d.string = metadata.accepted_date.day
                date_acc.append(d)
            if metadata.accepted_date.month:
                m = soup.new_tag("month")
                m.string = metadata.accepted_date.month
                date_acc.append(m)
            y = soup.new_tag("year")
            y.string = metadata.accepted_date.year
            date_acc.append(y)
            history.append(date_acc)
            
        article_meta.append(history)
        
    # Permissions
    permissions = soup.new_tag("permissions")
    license = soup.new_tag("license", **{"license-type": "open-access", "xlink:href": "https://creativecommons.org/licenses/by-nc-nd/4.0/", "xml:lang": "es"})
    license_p = soup.new_tag("license-p")
    license_p.string = "Este es un artículo publicado en acceso abierto bajo una licencia Creative Commons"
    license.append(license_p)
    permissions.append(license)
    article_meta.append(permissions)
    
    # Abstracts estructurados con sub-secciones <sec>
    abstract = build_structured_abstract_xml(soup, metadata.abstract_es, tag_name="abstract")
    article_meta.append(abstract)
        
    if metadata.abstract_pt and metadata.abstract_pt != metadata.abstract_es:
        trans_abstract_pt = build_structured_abstract_xml(soup, metadata.abstract_pt, tag_name="trans-abstract", lang="pt")
        article_meta.append(trans_abstract_pt)

    if metadata.abstract_en and metadata.abstract_en != metadata.abstract_es and metadata.abstract_en != "Abstract not available.":
        trans_abstract = build_structured_abstract_xml(soup, metadata.abstract_en, tag_name="trans-abstract", lang="en")
        article_meta.append(trans_abstract)
        
    # Keywords
    kwd_group_es = soup.new_tag("kwd-group", **{"xml:lang": "es"})
    title_kw_es = soup.new_tag("title")
    title_kw_es.string = "Palabras clave:"
    kwd_group_es.append(title_kw_es)
    kwds_es = metadata.keywords_es if metadata.keywords_es else ["Palabra clave no disponible"]
    for kwd in kwds_es:
        k = soup.new_tag("kwd")
        k.string = kwd
        kwd_group_es.append(k)
    article_meta.append(kwd_group_es)

    if metadata.keywords_pt:
        kwd_group_pt = soup.new_tag("kwd-group", **{"xml:lang": "pt"})
        title_kw_pt = soup.new_tag("title")
        title_kw_pt.string = "Palavras-chave:"
        kwd_group_pt.append(title_kw_pt)
        for kwd in metadata.keywords_pt:
            k = soup.new_tag("kwd")
            k.string = kwd
            kwd_group_pt.append(k)
        article_meta.append(kwd_group_pt)
        
    kwd_group_en = soup.new_tag("kwd-group", **{"xml:lang": "en"})
    title_kw_en = soup.new_tag("title")
    title_kw_en.string = "Keywords:"
    kwd_group_en.append(title_kw_en)
    kwds_en = metadata.keywords_en if metadata.keywords_en else (metadata.keywords_es if metadata.keywords_es else ["Keyword not available"])
    for kwd in kwds_en:
        k = soup.new_tag("kwd")
        k.string = kwd
        kwd_group_en.append(k)
    article_meta.append(kwd_group_en)
        
    # Funding Group
    if metadata.funding_source or metadata.award_id:
        funding_group = soup.new_tag("funding-group")
        award_group = soup.new_tag("award-group")
        if metadata.funding_source:
            funding_source = soup.new_tag("funding-source")
            funding_source.string = metadata.funding_source
            award_group.append(funding_source)
        if metadata.award_id:
            award_id = soup.new_tag("award-id")
            award_id.string = metadata.award_id
            award_group.append(award_id)
        funding_group.append(award_group)
        article_meta.append(funding_group)
        
    # Counts
    counts = soup.new_tag("counts")
    fig_count = soup.new_tag("fig-count", count="0")
    table_count = soup.new_tag("table-count", count="0")
    eq_count = soup.new_tag("equation-count", count="0")
    ref_count = soup.new_tag("ref-count", count="0")
    counts.append(fig_count)
    counts.append(table_count)
    counts.append(eq_count)
    counts.append(ref_count)
    article_meta.append(counts)
        
    new_front.append(article_meta)
    return new_front

def clean_body_duplicate_metadata(soup: BeautifulSoup, metadata: ArticleMetadata):
    body = soup.find('body')
    if not body:
        return
        
    keywords_to_remove = ["resumen", "abstract", "palabras clave", "keywords", "recibido", "aceptado", "publicado", "doi", "sumario"]
    if metadata.article_title_en:
        keywords_to_remove.append(metadata.article_title_en.lower())
    if metadata.article_title_es:
        keywords_to_remove.append(metadata.article_title_es.lower())
    for author in metadata.authors:
        keywords_to_remove.append(author.surname.lower())
        if author.email:
            keywords_to_remove.append(author.email.lower())
            
    # Remove tables that are just headers
    for t in list(body.find_all('table-wrap', limit=4)):
        text_lower = t.get_text(strip=True).lower()
        if any(h in text_lower for h in ["revista ", "issn", "doi.org", "http://", "https://", "creative commons", "licencia"]):
            if len(t.find_all('tr')) <= 3:
                t.decompose()

    # Remove recurring header/footer images (e.g. logos repeated on every page)
    from collections import Counter
    img_sources = []
    for g in body.find_all(['inline-graphic', 'graphic']):
        if g and getattr(g, 'attrs', None) is not None:
            src = g.get('xlink:href') or g.get('href')
            if src:
                img_sources.append(src)
            
    img_counts = Counter(img_sources)
    for g in body.find_all(['inline-graphic', 'graphic']):
        if g and getattr(g, 'attrs', None) is not None:
            src = g.get('xlink:href') or g.get('href')
            if src and img_counts[src] > 1:
                p = g.find_parent('p')
                if p and not p.get_text(strip=True):
                    p.decompose()
                else:
                    g.decompose()

    # Remove lone graphics at the very beginning (usually header images)
    for p in list(body.find_all('p', limit=5)):
        if not p.get_text(strip=True) and p.find('inline-graphic'):
            p.decompose()
            
    # Limpiamos los nodos al inicio del body que preceden a la primera sección real
    from bs4.element import Tag
    import unicodedata
    def unaccent(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

    lang = (metadata.language or "es").lower()
    for child in list(body.children):
        if not isinstance(child, Tag):
            continue
        text_clean = unaccent(child.get_text(strip=True).lower())
        title_elem = child.find('title')
        title_clean = unaccent(title_elem.get_text(strip=True).lower()) if title_elem else ''
        
        is_foreign = False
        if lang == "es":
            is_foreign = any(w in title_clean or w in text_clean for w in ["introducao", "abstrato", "resumo", "palavras-chave", "introduction", "abstract", "key words", "keywords"])
        elif lang == "en":
            is_foreign = any(w in title_clean or w in text_clean for w in ["introducao", "abstrato", "resumo", "palavras-chave", "introduccion", "resumen", "palabras clave"])
        elif lang == "pt":
            is_foreign = any(w in title_clean or w in text_clean for w in ["introduction", "abstract", "key words", "keywords", "introduccion", "resumen", "palabras clave"])
            
        is_structured_abstract = sum(1 for kw in ["objetivo", "objective", "metodologia", "methodology", "resultados", "results", "conclusiones", "conclusion", "conclusoes"] if kw in text_clean) >= 2
        
        is_main_body_start = (
            any(w in title_clean or (w in text_clean[:60] and len(text_clean) < 100) for w in ["introduccion", "introduction", "introducao", "metodologia", "methodology", "material y metodos", "antecedentes", "marco teorico", "marco conceptual", "desarrollo"])
            or bool(re.match(r'^(?:[i|v|x|l|c|d|m]+\.|\d+(?:\.\d+)*[\.\)])\s+[A-Za-z]', text_clean))
        ) and not any(w in title_clean or w in text_clean for w in ["sumario", "resumen", "abstract", "resumo", "palabras clave", "keywords", "palavras-chave"]) and not is_structured_abstract
        
        if is_main_body_start and not is_foreign:
            break
            
        child.decompose()

    # Eliminar tbodys vacíos o tablas que quedaron vacías (error: Element tbody content does not follow the DTD)
    for tbody in body.find_all('tbody'):
        if not tbody.find('tr'):
            table = tbody.find_parent('table-wrap')
            if table:
                table.decompose()
            else:
                tbody.decompose()

def extract_structured_abstracts_from_body(soup: BeautifulSoup, metadata: ArticleMetadata):
    body = soup.find('body')
    if not body or metadata is None:
        return
        
    import unicodedata
    def unaccent(s):
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
        
    from bs4.element import Tag
    def safe_decompose_abstract_sec(node):
        if not isinstance(node, Tag):
            return
        if node.name == 'sec':
            for child in list(node.children):
                if isinstance(child, Tag) and child.name == 'sec':
                    node.insert_before(child)
            node.decompose()
        else:
            node.decompose()

    for p in list(body.find_all(['p', 'sec'], limit=35)):
        if not isinstance(p, Tag):
            continue
        txt = p.get_text(strip=True)
        txt_clean = unaccent(txt.lower())
        sec_title_txt = unaccent(p.find('title').get_text(strip=True).lower()) if (isinstance(p, Tag) and p.find('title')) else ""
        
        # Spanish Abstract (Structured or Unstructured)
        already_has_valid_es = metadata.abstract_es and len(metadata.abstract_es) > 100 and "introduccion" in unaccent(metadata.abstract_es.lower())
        if not already_has_valid_es and ("introduccion" in txt_clean or "resumen" in txt_clean) and sum(1 for kw in ["objetivo", "metodologia", "resultados", "conclusiones", "conclusion"] if kw in txt_clean) >= 3:
            clean_txt = re.sub(r'^(?:Resumen|Resumen:)\s*', '', txt, flags=re.IGNORECASE).strip()
            if len(clean_txt) > 50:
                metadata.abstract_es = format_abstract_text(clean_txt)
                safe_decompose_abstract_sec(p)
                # Update <front>
                front = soup.find('front')
                if front:
                    old_abstract = front.find('abstract')
                    new_abstract = build_structured_abstract_xml(soup, metadata.abstract_es, tag_name="abstract")
                    if old_abstract:
                        old_abstract.replace_with(new_abstract)
                    elif front.find('article-meta'):
                        front.find('article-meta').append(new_abstract)
                continue

        # Continuous Spanish Resumen (Unstructured)
        if sec_title_txt in ["resumen", "resumen:"] or txt_clean.startswith("resumen:"):
            clean_txt = re.sub(r'^(?:Resumen|Resumen:)\s*', '', txt, flags=re.IGNORECASE).strip()
            if len(clean_txt) > 30 and (not metadata.abstract_es or metadata.abstract_es == "Resumen no disponible."):
                metadata.abstract_es = format_abstract_text(clean_txt)
                front = soup.find('front')
                if front:
                    abstract_tag = front.find('abstract')
                    if abstract_tag:
                        abstract_tag.clear()
                        title = soup.new_tag('title')
                        title.string = "Resumen:"
                        abstract_tag.append(title)
                        p_abs = soup.new_tag('p')
                        p_abs.string = format_abstract_text(clean_txt)
                        abstract_tag.append(p_abs)
            safe_decompose_abstract_sec(p)
            continue
                
        # English Abstract (Structured or Unstructured)
        if ("introduction" in txt_clean or "abstract" in txt_clean) and sum(1 for kw in ["objective", "methodology", "results", "conclusions", "conclusion"] if kw in txt_clean) >= 3:
            clean_txt = re.sub(r'^(?:Abstract|Abstract:)\s*', '', txt, flags=re.IGNORECASE).strip()
            if len(clean_txt) > 50:
                metadata.abstract_en = format_abstract_text(clean_txt)
                safe_decompose_abstract_sec(p)
                continue

        # Continuous English Abstract (Unstructured)
        if sec_title_txt in ["abstract", "abstract:"] or txt_clean.startswith("abstract:"):
            clean_txt = re.sub(r'^(?:Abstract|Abstract:)\s*', '', txt, flags=re.IGNORECASE).strip()
            if len(clean_txt) > 30 and (not metadata.abstract_en or metadata.abstract_en == "Abstract not available."):
                metadata.abstract_en = format_abstract_text(clean_txt)
                front = soup.find('front')
                if front:
                    trans_abstract_tag = front.find('trans-abstract', **{"xml:lang": "en"})
                    if trans_abstract_tag:
                        trans_abstract_tag.clear()
                        title = soup.new_tag('title')
                        title.string = "Abstract:"
                        trans_abstract_tag.append(title)
                        p_abs = soup.new_tag('p')
                        p_abs.string = format_abstract_text(clean_txt)
                        trans_abstract_tag.append(p_abs)
            safe_decompose_abstract_sec(p)
            continue
                
        # Portuguese Abstract (Resumo/Abstrato - single or multi-paragraph)
        if ("introducao" in txt_clean or "abstrato" in txt_clean or "resumo" in txt_clean) and sum(1 for kw in ["objetivo", "metodologia", "resultados", "conclusoes", "conclusao"] if kw in txt_clean) >= 2:
            clean_txt = re.sub(r'^(?:Resumo|Resumo:|Abstrato|Abstrato:)\s*', '', txt, flags=re.IGNORECASE).strip()
            if len(clean_txt) > 30:
                metadata.abstract_pt = format_abstract_text(clean_txt)
                safe_decompose_abstract_sec(p)
                continue
                
        # Portuguese Abstract multi-paragraph collection starting with Abstrato/Resumo header
        if txt_clean in ["abstrato", "abstrato:", "resumo", "resumo:"]:
            pt_parts = []
            curr = p.next_sibling
            safe_decompose_abstract_sec(p)
            while curr:
                nxt = curr.next_sibling
                if isinstance(curr, Tag):
                    c_txt = curr.get_text(strip=True)
                    c_clean = unaccent(c_txt.lower())
                    if any(c_clean.startswith(kw) for kw in ["introducao", "objetivo", "metodologia", "resultados", "conclusoes", "conclusao", "palavras-chave"]):
                        pt_parts.append(c_txt)
                        safe_decompose_abstract_sec(curr)
                    else:
                        break
                curr = nxt
            if pt_parts:
                full_pt = "\n".join(pt_parts)
                metadata.abstract_pt = format_abstract_text(full_pt)
                continue
            
        # Lone Keywords / Titles sections in body
        if any(txt_clean.startswith(prefix) for prefix in ["palabras clave", "keywords", "key words", "palavras-chave"]):
            # Extract keywords if not present in front
            kw_match = re.sub(r'^(?:palabras\s+clave|keywords|key\s+words|palavras-chave):\s*', '', txt, flags=re.IGNORECASE).rstrip('.')
            if kw_match and (not metadata.keywords_es or metadata.keywords_es == ["Palabra clave no disponible"]):
                kw_list = [k.strip() for k in re.split(r'[;,]', kw_match) if k.strip()]
                if kw_list:
                    metadata.keywords_es = kw_list
                    front = soup.find('front')
                    if front:
                        kwd_grp = front.find('kwd-group', **{"xml:lang": "es"})
                        if kwd_grp:
                            kwd_grp.clear()
                            t_kw = soup.new_tag('title')
                            t_kw.string = "Palabras clave:"
                            kwd_grp.append(t_kw)
                            for kw in kw_list:
                                k_tag = soup.new_tag('kwd')
                                k_tag.string = kw
                                kwd_grp.append(k_tag)
            safe_decompose_abstract_sec(p)
            continue

def restructure_body_to_sections(soup: BeautifulSoup):
    """
    Convierte párrafos que simulan ser títulos de sección en verdaderas etiquetas <sec> de JATS,
    preservando la capitalización original del manuscrito y evitando convertir tablas o figuras.
    Detecta negritas (<bold>), numerales romanos (I., II., III., etc.) y encabezados canónicos.
    """
    body = soup.find('body')
    if not body:
        return
        
    # Limpieza de marcas de resaltado de Word (<named-content content-type="mark">)
    for nc in soup.find_all('named-content'):
        if nc.get('content-type') == 'mark' or 'mark' in str(nc.get('content-type', '')):
            nc.unwrap()
            
    children = list(body.children)
    current_sec = None
    
    # Patrón para numerales romanos (ej. I., II., III., IV.), números de sección (ej. 1., 1.1) o títulos canónicos
    section_title_regex = re.compile(
        r'^(?:'
        r'[IVXLCDM]+\.|\d+[\.\)]|\d+\.\d+'
        r'|SUMARIO|RESUMEN|ABSTRACT|INTRODUCCIÓN|INTRODUCTION|METODOLOGÍA|METHODOLOGY|MATERIALES|MATERIAL Y MÉTODOS|RESULTADOS|RESULTS|DISCUSIÓN|DISCUSSION|CONCLUSIONES|CONCLUSIONS|REFERENCIAS|REFERENCES|BIBLIOGRAFÍA'
        r')(?:\s+|$)',
        re.IGNORECASE
    )
    
    for child in children:
        if getattr(child, 'name', None) == 'p':
            text = child.get_text(strip=True)
            text_lower = text.lower()
            
            if any(text_lower.startswith(prefix) for prefix in ['tabla', 'grafica', 'gráfica', 'figura', 'chart', 'figure', 'fuente:', 'nota:', 'source:', 'note:']):
                continue
                
            bold = child.find('bold')
            is_sec_title = False
            clean_title = ""
            
            if bold and len(text) > 2:
                bold_text = bold.get_text(strip=True)
                clean_bold = bold_text.rstrip(':').strip()
                
                # Caso A: El párrafo completo es el título (ej. <p><bold>Introducción</bold></p>)
                if text == bold_text or text.rstrip(':').strip() == clean_bold or len(bold_text) > (len(text) * 0.8):
                    is_sec_title = True
                    clean_title = clean_bold
                # Caso B: Subtítulo incrustado al inicio (ej. <p><bold>Introducción:</bold> Texto del párrafo...</p>)
                elif text.startswith(bold_text) and len(clean_bold) < 60:
                    new_sec = soup.new_tag("sec")
                    sec_title = soup.new_tag("title")
                    sec_title.string = clean_bold
                    new_sec.append(sec_title)
                    
                    bold.decompose()
                    remainder = child.get_text(strip=True)
                    if remainder.startswith(':'):
                        remainder = remainder[1:].strip()
                    child.string = remainder
                    
                    child.insert_before(new_sec)
                    if child.parent:
                        child.extract()
                    if remainder:
                        new_sec.append(child)
                    current_sec = new_sec
                    continue

            # Si no se detectó por negrita, pero coincide con el patrón de numeral romano o encabezado canónico corto
            if not is_sec_title and len(text) < 130 and section_title_regex.match(text):
                is_sec_title = True
                clean_title = text.rstrip(':').strip()

            if is_sec_title and clean_title:
                new_sec = soup.new_tag("sec")
                sec_title = soup.new_tag("title")
                sec_title.string = clean_title
                new_sec.append(sec_title)
                
                child.insert_before(new_sec)
                child.extract()
                current_sec = new_sec
                continue
                    
        if current_sec and getattr(child, 'name', None) != 'sec':
            if child.parent:
                child.extract()
            current_sec.append(child)

def format_tables(soup: BeautifulSoup):
    """
    Formatea las tablas según el estándar JATS SciELO SPS:
    <table-wrap id="t1">
        <label>Tabla 1</label>
        <caption><title>Título de la tabla</title></caption>
        <table>...</table>
        <table-wrap-foot>
            <fn id="TFN1">
                <p>Fuente: ...</p>
            </fn>
        </table-wrap-foot>
    </table-wrap>
    """
    main_body = soup.find('body')
    sub_article = soup.find('sub-article')
    containers = [main_body] if main_body else []
    if sub_article:
        containers.append(sub_article)
        
    for container in containers:
        is_sub = container.name == 'sub-article'
        t_prefix = "en-t" if is_sub else "t"
        label_word = "Table" if is_sub else "Tabla"
        
        table_wraps = list(container.find_all('table-wrap'))
        table_counter = 1
        processed_tables = []
        
        for tbl_wrap in table_wraps:
            detected_num = None
            caption_title_str = ""
            
            # Check previous 2 siblings for title/label paragraph
            prev_nodes = []
            curr = tbl_wrap
            for _ in range(2):
                p_node = curr.find_previous_sibling(['p', 'sec'])
                if p_node:
                    prev_nodes.append(p_node)
                    curr = p_node

            for p_elem in prev_nodes:
                p_txt = p_elem.get_text(strip=True)
                m = re.search(r'^(?:Tabla|Table|Tabela)\s*(\d+)[\.\:]?\s*(.*)$', p_txt, re.IGNORECASE)
                if m:
                    detected_num = int(m.group(1))
                    caption_title_str = m.group(2).strip().lstrip('.').lstrip(':').strip()
                    p_elem.decompose()
                    break

            if not detected_num:
                lbl = tbl_wrap.find('label')
                cap = tbl_wrap.find('caption')
                lbl_txt = lbl.get_text(strip=True) if lbl else ""
                cap_txt = cap.get_text(strip=True) if cap else ""
                
                m_cap = re.search(r'^(?:Tabla|Table|Tabela)\s*(\d+)[\.\:]?\s*(.*)$', cap_txt, re.IGNORECASE)
                m_lbl = re.search(r'\b(\d+)\b', lbl_txt)
                
                if m_cap:
                    detected_num = int(m_cap.group(1))
                    caption_title_str = m_cap.group(2).strip().lstrip('.').lstrip(':').strip()
                elif m_lbl:
                    detected_num = int(m_lbl.group(1))
                    
            if not detected_num:
                detected_num = table_counter
                table_counter += 1
            else:
                table_counter = max(table_counter, detected_num + 1)
                
            t_id = f"{t_prefix}{detected_num}"
            tbl_wrap['id'] = t_id
            
            label_str = f"{label_word} {detected_num}"
            label = tbl_wrap.find('label')
            if not label:
                label = soup.new_tag('label')
                label.string = label_str
                tbl_wrap.insert(0, label)
            else:
                label.string = label_str
                
            caption = tbl_wrap.find('caption')
            if caption_title_str:
                if not caption:
                    caption = soup.new_tag('caption')
                    tbl_wrap.insert(1, caption)
                t_title = caption.find('title')
                if not t_title:
                    t_title = soup.new_tag('title')
                    caption.append(t_title)
                t_title.string = caption_title_str
            elif caption:
                t_title = caption.find('title')
                if t_title:
                    t_txt = t_title.get_text(strip=True)
                    m_clean = re.search(r'^(?:Tabla|Table|Tabela)\s*\d*[\.\:]?\s*(.*)$', t_txt, re.IGNORECASE)
                    if m_clean and m_clean.group(1).strip():
                        t_title.string = m_clean.group(1).strip()
                        
            # Unwrap table-wrap if it is direct child of <p>
            p_parent = tbl_wrap.parent
            if p_parent and p_parent.name == 'p':
                p_parent.insert_after(tbl_wrap)
                if not p_parent.get_text(strip=True):
                    p_parent.decompose()

            # Remove empty <tr> rows with no cell text
            for tr in list(tbl_wrap.find_all('tr')):
                cells_text = "".join(td.get_text(strip=True) for td in tr.find_all(['td', 'th']))
                if not cells_text:
                    tr.decompose()

            # Unwrap <xref> inside <label>
            if label:
                for xr in list(label.find_all('xref')):
                    xr.unwrap()

            # Consolidate and deduplicate <table-wrap-foot>
            next_p = tbl_wrap.find_next_sibling('p')
            foot_text = None
            if next_p:
                np_txt = next_p.get_text(strip=True)
                if np_txt.lower().startswith(('fuente:', 'nota:', 'source:', 'note:', 'elaboración', 'elaboracion')):
                    foot_text = np_txt
                    next_p.decompose()
                    
            foot = tbl_wrap.find('table-wrap-foot')
            if foot_text:
                if not foot:
                    foot = soup.new_tag('table-wrap-foot')
                    tbl_wrap.append(foot)
            
            if foot:
                txt_content = foot.get_text(separator=' ', strip=True)
                if foot_text and foot_text not in txt_content:
                    txt_content = f"{txt_content} {foot_text}".strip()
                txt_clean = re.sub(r'^(Fuente:[^\.]*[\.]?)\s+\1$', r'\1', txt_content, flags=re.IGNORECASE).strip()
                if not txt_clean:
                    txt_clean = "Source: Self-developed" if is_sub else "Fuente: Elaboración propia"
                foot.clear()
                tfn_prefix = "en-TFN" if is_sub else "TFN"
                fn_tag = soup.new_tag('fn', id=f"{tfn_prefix}{detected_num}", **{'fn-type': 'other'})
                p_foot = soup.new_tag('p')
                p_foot.string = txt_clean
                fn_tag.append(p_foot)
                foot.append(fn_tag)

            processed_tables.append((detected_num, tbl_wrap))

        # Re-ubicar las tablas en el lugar donde son citadas en el texto si no están en orden
        for num, tbl in processed_tables:
            t_id = tbl.get('id')
            ref_xref = container.find('xref', **{'ref-type': 'table', 'rid': t_id})
            if ref_xref:
                parent_p = ref_xref.find_parent(['p', 'sec'])
                if parent_p and parent_p != tbl.parent:
                    parent_p.insert_after(tbl)

def fix_footnotes(soup: BeautifulSoup):
    """
    1. Filtra y remueve notas al pie impropias (fechas de arbitraje/historial, etc. en fn-group).
    2. Renumera secuencialmente desde 1 las notas al pie que aparecen en el cuerpo (body),
       sincronizando <xref ref-type="fn" rid="fnX"><sup>X</sup></xref> y <fn id="fnX"><label>X</label>...</fn>.
    """
    body = soup.find('body')
    
    # 1. Limpieza de notas de historial / arbitraje en <fn-group>
    for fn in list(soup.find_all('fn')):
        fn_text = fn.get_text(strip=True)
        # Detectar notas con fechas de recepción / aceptación (ej. "09/11/2025 Aceptado: 20/12/2025")
        if re.search(r'\b\d{2}/\d{2}/\d{4}\b', fn_text) or any(k in fn_text.lower() for k in ["aceptado:", "recibido:", "received:", "accepted:"]):
            # Intentar extraer fechas para <history> si no existen o están en blanco/00
            m_rec = re.search(r'(?:recibido|received)[\s:]*(\d{1,2}/\d{1,2}/\d{4})', fn_text, re.IGNORECASE)
            m_acc = re.search(r'(?:aceptado|accepted)[\s:]*(\d{1,2}/\d{1,2}/\d{4})', fn_text, re.IGNORECASE)
            
            history = soup.find('history')
            if history:
                if m_rec:
                    d_rec = history.find('date', **{'date-type': 'received'})
                    if d_rec and d_rec.find('day') and d_rec.find('day').string in ['00', '0', None]:
                        pts = m_rec.group(1).split('/')
                        if len(pts) == 3:
                            d_rec.find('day').string = pts[0].zfill(2)
                            d_rec.find('month').string = pts[1].zfill(2)
                            d_rec.find('year').string = pts[2]
                if m_acc:
                    d_acc = history.find('date', **{'date-type': 'accepted'})
                    if d_acc and d_acc.find('day') and d_acc.find('day').string in ['00', '0', None]:
                        pts = m_acc.group(1).split('/')
                        if len(pts) == 3:
                            d_acc.find('day').string = pts[0].zfill(2)
                            d_acc.find('month').string = pts[1].zfill(2)
                            d_acc.find('year').string = pts[2]
            fn.decompose()
            continue

    # 2. Mapa de notas existentes por su id original
    all_fns = {fn.get('id'): fn for fn in soup.find_all('fn') if fn.get('id')}
    
    # 3. Recorrer llamadas en el cuerpo <body> para re-indexar a base 1 (fn1, fn2, fn3...)
    fn_counter = 1
    processed_fn_ids = set()
    fn_id_map = {}
    
    if body:
        for xref in body.find_all('xref', **{"ref-type": "fn"}):
            old_rid = xref.get('rid')
            if not old_rid:
                continue
                
            if old_rid not in fn_id_map:
                new_id = f"fn{fn_counter}"
                fn_id_map[old_rid] = new_id
                fn_counter += 1
            else:
                new_id = fn_id_map[old_rid]
                
            xref['rid'] = new_id
            
            # Extraer el número secuencial (ej. "1", "2"...)
            seq_num = new_id.replace("fn", "")
            
            # Limpiar residuo del texto anterior ("1F", "2F", etc.)
            from bs4.element import NavigableString
            prev = xref.previous_sibling
            if prev and isinstance(prev, NavigableString):
                clean_text = re.sub(r'\b\d+[FfNn]$|\d+[FfNn]$', '', str(prev))
                prev.replace_with(clean_text)
                
            # Actualizar el <sup> con el número secuencial correcto
            sup = xref.find('sup')
            if not sup:
                xref.clear()
                sup = soup.new_tag("sup")
                sup.string = seq_num
                xref.append(sup)
            else:
                sup.string = seq_num

            # Actualizar la nota de destino <fn> en <fn-group>
            target_fn = all_fns.get(old_rid)
            if target_fn and target_fn not in processed_fn_ids:
                target_fn['id'] = new_id
                target_fn['fn-type'] = "other"
                label = target_fn.find('label')
                if not label:
                    label = soup.new_tag('label')
                    target_fn.insert(0, label)
                label.string = seq_num
                processed_fn_ids.add(target_fn)

    # 4. Renumerar cualquier otra nota al pie <fn> restante que no estuviera vinculada en el body
    for fn in soup.find_all('fn'):
        if fn not in processed_fn_ids:
            new_id = f"fn{fn_counter}"
            fn['id'] = new_id
            fn['fn-type'] = "other"
            seq_num = str(fn_counter)
            label = fn.find('label')
            if not label:
                label = soup.new_tag('label')
                fn.insert(0, label)
            label.string = seq_num
            fn_counter += 1

def fix_section_title_case(soup: BeautifulSoup):
    """
    Mantiene la capitalización estándar (Sentence Case / Title Case) en los títulos de sección:
    Si un título de sección está en mayúsculas sostenidas (ej. 'II. CONCEPTUALIZACIÓN Y CLASIFICACIÓN...'),
    lo convierte a capitalización normal 'II. Conceptualización y clasificación de la discapacidad'.
    """
    for sec in soup.find_all('sec'):
        title = sec.find('title')
        if not title or not title.string:
            continue
            
        t_text = title.string.strip()
        letters_only = re.sub(r'^[I|V|X|L|C|D|M]+\.\s*', '', t_text)
        if letters_only.isupper() and len(letters_only) > 3:
            match_roman = re.match(r'^([I|V|X|L|C|D|M]+\.\s*)(.*)', t_text)
            if match_roman:
                roman_prefix = match_roman.group(1)
                rest = match_roman.group(2).lower().capitalize()
                title.string = f"{roman_prefix}{rest}"
            else:
                title.string = t_text.lower().capitalize()

def format_figures(soup: BeautifulSoup):
    """
    Recomendación 2: Detección y Conversión de Gráficos/Figuras.
    Reconoce elementos de gráficos/figuras (Gráfica X, Figura X, Chart X)
    y genera la estructura <fig id="f1"><label>...</label><caption>...</caption><graphic xlink:href="..."/><attrib>...</attrib></fig>.
    """
    body = soup.find('body')
    if not body:
        return
        
    fig_counter = 1
    
    # 1. Buscar texto de Gráfica X / Figura X en párrafos o títulos del body
    from bs4.element import Tag
    for node in list(body.find_all(['p', 'title', 'sec'])):
        if not isinstance(node, Tag):
            continue
        text = node.get_text(strip=True)
        match = re.search(r'^(Gráfica|Grafica|Figura|Chart|Figure)\s*(\d+)', text, re.IGNORECASE)
        if match:
            fig_label = f"{match.group(1).capitalize()} {match.group(2)}"
            caption_title = re.sub(r'^(Gráfica|Grafica|Figura|Chart|Figure)\s*\d+[\s:\.\-]*', '', text, flags=re.IGNORECASE).strip()
            
            fig = soup.new_tag('fig', id=f"f{fig_counter}")
            lbl_tag = soup.new_tag('label')
            lbl_tag.string = fig_label
            fig.append(lbl_tag)
            
            if caption_title:
                cap_tag = soup.new_tag('caption')
                title_tag = soup.new_tag('title')
                title_tag.string = caption_title
                cap_tag.append(title_tag)
                fig.append(cap_tag)
                
            graphic = node.find(['graphic', 'inline-graphic']) or (node.parent.find(['graphic', 'inline-graphic']) if (node.parent and hasattr(node.parent, 'find')) else None)
            graphic_attrs = dict(graphic.attrs) if (graphic and hasattr(graphic, 'attrs')) else {'xlink:href': f"fig{fig_counter}.jpg"}
            if graphic and hasattr(graphic, 'decompose'):
                graphic.decompose()
                
            new_graphic = soup.new_tag('graphic', **graphic_attrs)
            fig.append(new_graphic)
            
            next_sibling = node.find_next_sibling('p')
            if next_sibling:
                ns_text = next_sibling.get_text(strip=True)
                if ns_text.lower().startswith(('nota:', 'fuente:', 'note:', 'source:')):
                    attrib_tag = soup.new_tag('attrib')
                    attrib_tag.string = ns_text
                    fig.append(attrib_tag)
                    next_sibling.decompose()
                    
            node.replace_with(fig)
            fig_counter += 1

    # 2. Formatear gráficos sueltos restantes
    for graphic in body.find_all(['inline-graphic', 'graphic']):
        if graphic.find_parent('fig'):
            continue
            
        fig = soup.new_tag('fig', id=f"f{fig_counter}")
        label = soup.new_tag('label')
        label.string = f"Figura {fig_counter}"
        fig.append(label)
        
        caption = soup.new_tag('caption')
        title = soup.new_tag('title')
        title.string = f"Figura {fig_counter}"
        caption.append(title)
        fig.append(caption)
        
        new_graphic = soup.new_tag('graphic', **graphic.attrs)
        fig.append(new_graphic)
        
        graphic.replace_with(fig)
        fig_counter += 1

def clean_phantom_sections(soup: BeautifulSoup):
    """Elimina secciones fantasmas o vacías que se crean por saltos de línea con formato de título en Word."""
    body = soup.find('body')
    if not body:
        return
    for sec in list(body.find_all('sec')):
        title = sec.find('title')
        # Si la sección está vacía o solo contiene un título sin texto
        if not sec.get_text(strip=True):
            sec.decompose()
        elif title and not title.get_text(strip=True) and len(list(sec.children)) == 1:
            sec.decompose()
            
    # Clean empty lists
    for lst in list(body.find_all('list')):
        if not lst.get_text(strip=True):
            lst.decompose()

def auto_link_cross_references(soup: BeautifulSoup):
    """Garantiza la vinculación bidireccional <xref> entre el texto, las referencias y las figuras/tablas."""
    # 1. Transformar citas numéricas de texto <sup>(1)</sup>, <sup>(8,9)</sup>, <sup>(3-7)</sup> en <xref ref-type="bibr">
    for container in soup.find_all(['body', 'sub-article']):
        for sup in list(container.find_all('sup')):
            if sup.find_parent('xref') or sup.find_parent('ref-list') or sup.find_parent('ref') or sup.find_parent('mixed-citation') or sup.find_parent('element-citation') or sup.find_parent('back') or sup.find_parent('label') or sup.find_parent('caption') or sup.get_text(strip=True) in ['*', '']:
                continue
            txt = sup.get_text(strip=True)
            m = re.match(r'^\(?([\d\s\,\-\–\—]+)\)?$', txt)
            if m:
                raw_nums = m.group(1).strip()
                parts = [p.strip() for p in raw_nums.split(',') if p.strip()]
                new_nodes = []
                for idx, part in enumerate(parts):
                    if idx > 0:
                        sep = soup.new_tag('sup')
                        sep.string = ","
                        new_nodes.append(sep)
                    if '-' in part or '–' in part or '—' in part:
                        range_parts = re.split(r'[\-\–\—]', part)
                        if len(range_parts) == 2 and range_parts[0].isdigit() and range_parts[1].isdigit():
                            start_n, end_n = int(range_parts[0]), int(range_parts[1])
                            if start_n < 1000 and end_n < 1000 and (end_n - start_n) <= 50:
                                rids = " ".join([f"B{n}" for n in range(start_n, end_n + 1)])
                                xref = soup.new_tag('xref', **{'ref-type': 'bibr', 'rid': rids})
                                sup_elem = soup.new_tag('sup')
                                sup_elem.string = part
                                xref.append(sup_elem)
                                new_nodes.append(xref)
                            else:
                                sup_elem = soup.new_tag('sup')
                                sup_elem.string = part
                                new_nodes.append(sup_elem)
                        else:
                            sup_elem = soup.new_tag('sup')
                            sup_elem.string = part
                            new_nodes.append(sup_elem)
                    elif part.isdigit() and int(part) < 1000:
                        xref = soup.new_tag('xref', **{'ref-type': 'bibr', 'rid': f"B{part}"})
                        sup_elem = soup.new_tag('sup')
                        sup_elem.string = part
                        xref.append(sup_elem)
                        new_nodes.append(xref)
                    else:
                        sup_elem = soup.new_tag('sup')
                        sup_elem.string = part
                        new_nodes.append(sup_elem)
                
                if new_nodes:
                    for node in reversed(new_nodes):
                        sup.insert_after(node)
                    sup.decompose()

    # 1.5 Citas numéricas inline entre paréntesis normales (17), (18), (8,9), (13-15)
    main_body = soup.find('body')
    sub_article = soup.find('sub-article')
    containers = [main_body] if main_body else []
    if sub_article:
        containers.append(sub_article)
        
    for container in containers:
        for p in container.find_all('p'):
            if p.find_parent('table-wrap') or p.find_parent('fig') or p.find_parent('ref-list') or p.find_parent('ref') or p.find_parent('mixed-citation') or p.find_parent('element-citation') or p.find_parent('back') or p.find_parent('label') or p.find_parent('caption'):
                continue
            for text_node in list(p.find_all(string=True)):
                if not text_node.parent or text_node.parent.name in ['xref', 'sup', 'title', 'ref', 'mixed-citation', 'element-citation', 'ref-list', 'label', 'caption']:
                    continue
                txt_val = str(text_node)
                matches = list(re.finditer(r'\(([\d\s\,\-\–\—]+)\)', txt_val))
                if not matches:
                    continue
                curr_txt = txt_val
                new_elements = []
                last_idx = 0
                for match in matches:
                    start, end = match.span()
                    prefix = curr_txt[last_idx:start]
                    raw_nums = match.group(1).strip()
                    parts = [pt.strip() for pt in raw_nums.split(',') if pt.strip()]
                    nodes = [prefix, "("]
                    for idx, part in enumerate(parts):
                        if idx > 0:
                            nodes.append(",")
                        if '-' in part or '–' in part or '—' in part:
                            r_parts = re.split(r'[\-\–\—]', part)
                            if len(r_parts) == 2 and r_parts[0].isdigit() and r_parts[1].isdigit():
                                s_n, e_n = int(r_parts[0]), int(r_parts[1])
                                if s_n < 1000 and e_n < 1000 and (e_n - s_n) <= 50:
                                    for n_idx, n in enumerate(range(s_n, e_n + 1)):
                                        if n_idx > 0:
                                            nodes.append("-")
                                        xref = soup.new_tag('xref', **{'ref-type': 'bibr', 'rid': f"B{n}"})
                                        xref.string = str(n)
                                        nodes.append(xref)
                                else:
                                    nodes.append(part)
                            else:
                                nodes.append(part)
                        elif part.isdigit() and int(part) < 1000:
                            xref = soup.new_tag('xref', **{'ref-type': 'bibr', 'rid': f"B{part}"})
                            xref.string = part
                            nodes.append(xref)
                        else:
                            nodes.append(part)
                    nodes.append(")")
                    new_elements.extend(nodes)
                    last_idx = end
                new_elements.append(curr_txt[last_idx:])
                for elem in reversed(new_elements):
                    if isinstance(elem, str):
                        if elem:
                            text_node.insert_after(elem)
                    else:
                        text_node.insert_after(elem)
                text_node.extract()

    # 2. Transformar menciones a Tablas y Figuras en el texto en <xref>
    for container in containers:
        if not container: continue
        is_sub = container.name == 'sub-article'
        t_prefix = "en-t" if is_sub else "t"
        f_prefix = "en-f" if is_sub else "f"
        
        for p in container.find_all('p'):
            if p.find_parent('table-wrap') or p.find_parent('fig') or p.find_parent('ref-list') or p.find_parent('ref') or p.find_parent('back') or p.find_parent('label') or p.find_parent('caption'):
                continue
            for text_node in list(p.find_all(string=True)):
                if not text_node.parent or text_node.parent.name in ['xref', 'title', 'label', 'caption']:
                    continue
                txt_val = str(text_node)
                
                def repl_tbl(match):
                    prefix, num = match.group(1), match.group(2)
                    return f'<xref ref-type="table" rid="{t_prefix}{num}">{prefix} {num}</xref>'
                    
                def repl_fig(match):
                    prefix, num = match.group(1), match.group(2)
                    return f'<xref ref-type="fig" rid="{f_prefix}{num}">{prefix} {num}</xref>'
                    
                new_txt = re.sub(r'\b(Tabla|Table|Tabela)\s+(\d+)\b', repl_tbl, txt_val, flags=re.IGNORECASE)
                new_txt = re.sub(r'\b(Figura|Figure)\s+(\d+)\b', repl_fig, new_txt, flags=re.IGNORECASE)
                
                if new_txt != txt_val:
                    try:
                        fragment = BeautifulSoup(f"<span>{new_txt}</span>", 'xml').find('span')
                        if fragment:
                            for child in reversed(list(fragment.children)):
                                text_node.insert_after(child)
                            text_node.extract()
                    except Exception:
                        pass

    # Cleanup: unwrap any <xref ref-type="bibr"> inside <ref-list>, <ref>, <mixed-citation>, <element-citation>, <label>
    for ref_parent in soup.find_all(['ref-list', 'ref', 'mixed-citation', 'element-citation', 'label']):
        for xr in list(ref_parent.find_all('xref')):
            xr.unwrap()

def format_sections(soup: BeautifulSoup):
    """Mapea las secciones canónicas según el estándar SciELO SPS / JATS DTD v1.1."""
    body = soup.find('body')
    if not body:
        return
        
    for sec in body.find_all('sec'):
        title = sec.find('title')
        if not title:
            continue
            
        text = unaccent(title.get_text(strip=True).lower())
        if "introduc" in text:
            sec['sec-type'] = 'intro'
        elif any(k in text for k in ["material", "metodo", "method", "metodolog"]):
            sec['sec-type'] = 'methods'
        elif any(k in text for k in ["caso clin", "clinical case", "case report", "relato de caso", "estudio de caso", "case study", "casos"]):
            sec['sec-type'] = 'cases'
        elif "resultado" in text or "result" in text:
            sec['sec-type'] = 'results'
        elif "discus" in text or "discuss" in text:
            sec['sec-type'] = 'discussion'
        elif "conclusi" in text or "conclus" in text:
            sec['sec-type'] = 'conclusions'

def extract_bibliography_paragraphs(soup: BeautifulSoup) -> tuple[list[dict], str]:
    body = soup.find('body')
    default_title = "Referencias"
    if not body:
        return [], default_title
        
    ref_nodes = []
    section_title = default_title
    
    # 1. Buscar en secciones <sec> cuyo <title> contenga "referenc", "bibliograf", "fuentes", "works cited", "obras citadas"
    for sec in list(body.find_all('sec')):
        title = sec.find('title')
        if title:
            raw_title_text = title.get_text(strip=True)
            title_text = raw_title_text.lower()
            if any(k in title_text for k in ["bibliograf", "referenc", "fuentes", "works cited", "obras citadas"]):
                section_title = raw_title_text
                for p in list(sec.find_all('p')):
                    raw_html = p.decode_contents()
                    raw_text = p.get_text(strip=True)
                    if raw_text and len(raw_text) > 10:
                        ref_nodes.append({'raw_text': raw_text, 'raw_html': raw_html})
                sec.decompose()
                return ref_nodes, section_title

    # 2. Buscar por sec/p cuyo texto empiece por Referencias, Bibliografía o Fuentes, o párrafos numerados al final
    p_tags = list(body.find_all('p'))
    in_ref_section = False
    ref_ps = []
    for p in p_tags:
        text = p.get_text(strip=True)
        text_lower = text.lower()
        if not in_ref_section:
            if any(text_lower.startswith(prefix) for prefix in ["bibliografía", "bibliografia", "referencias", "fuentes", "references"]):
                in_ref_section = True
                section_title = text
                ref_ps.append(p)
            elif re.match(r'^\s*\[?1\]?[\.\s]+[A-Z]', text):
                in_ref_section = True
                ref_ps.append(p)
        else:
            ref_ps.append(p)
            
    if in_ref_section and len(ref_ps) >= 1:
        for p in ref_ps:
            text = p.get_text(strip=True)
            if p == ref_ps[0] and any(text.lower().startswith(k) for k in ["bibliografía", "bibliografia", "referencias", "fuentes", "references"]):
                p.decompose()
                continue
            raw_html = p.decode_contents()
            raw_text = text
            if raw_text and len(raw_text) > 10:
                ref_nodes.append({'raw_text': raw_text, 'raw_html': raw_html})
            p.decompose()
            
    return ref_nodes, section_title

def parse_reference_item_fallback(raw_text: str, ref_id: str = "B1") -> ReferenceItem:
    import re
    clean_text = re.sub(r'^\s*\[?\d+\]?[\.\s]*', '', raw_text).strip()
    
    doi_match = re.search(r'10\.\d{4,9}/[^\s<"\']+', clean_text)
    doi = doi_match.group(0).rstrip('.') if doi_match else None
    
    url_match = re.search(r'https?://[^\s<"\']+', clean_text)
    url = url_match.group(0).rstrip('.') if url_match else None
    
    year_match = re.search(r'\b(19\d\d|20\d\d)\b', clean_text)
    year = year_match.group(1) if year_match else None
    
    vol_match = re.search(r'\b(\d+)\s*\(\s*(\d+)\s*\)', clean_text)
    volume = vol_match.group(1) if vol_match else None
    issue = vol_match.group(2) if vol_match else None
    
    page_match = re.search(r':\s*(\d+)\s*[-–]\s*(\d+)', clean_text)
    fpage = page_match.group(1) if page_match else None
    lpage = page_match.group(2) if page_match else None
    
    parts = [p.strip() for p in clean_text.split('.') if p.strip()]
    authors = []
    article_title = None
    source = None
    
    if len(parts) >= 1:
        author_tokens = parts[0].split(',')
        for at in author_tokens:
            at_clean = at.strip()
            if at_clean and not any(char.isdigit() for char in at_clean):
                subparts = at_clean.split()
                if len(subparts) >= 2:
                    authors.append(RefAuthor(surname=subparts[0], given_names=" ".join(subparts[1:])))
                elif len(subparts) == 1:
                    authors.append(RefAuthor(surname=subparts[0]))
                    
    if len(parts) >= 2:
        article_title = parts[1]
    if len(parts) >= 3:
        source = parts[2]
        
    pub_type = "journal" if (volume or issue or doi or "revista" in clean_text.lower() or "journal" in clean_text.lower()) else "other"
    
    return ReferenceItem(
        id=ref_id,
        raw_text=raw_text,
        publication_type=pub_type,
        authors=authors,
        article_title=article_title,
        source=source,
        year=year,
        volume=volume,
        issue=issue,
        fpage=fpage,
        lpage=lpage,
        doi=doi,
        url=url
    )

async def parse_references_with_gemini(ref_items: List[dict]) -> List[ReferenceItem]:
    if not ref_items:
        return []
        
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and client:
        texts = [f"[{idx+1}] {item['raw_text']}" for idx, item in enumerate(ref_items)]
        combined_text = "\n".join(texts)

        prompt = """
        Analiza la siguiente lista de citas bibliográficas de un artículo científico.
        Para cada una de las referencias (en orden B1, B2, B3...):
        - ID: asigna B1, B2, B3...
        - raw_text: asigna el texto original completo de la cita.
        - publication_type: 'journal' (artículo de revista), 'book' (libro), 'thesis' (tesis), 'conference' (conferencia), 'webpage' (sitio web / vídeo / blog), u 'other'.
        - authors: lista de autores con surname y given_names.
        - article_title: título del artículo o capítulo.
        - source: nombre de la revista, libro, sitio web o conferencia.
        - publisher_name: editorial o institución.
        - year: año de publicación de 4 dígitos.
        - volume, issue, fpage, lpage, doi, url si están presentes.
        
        Instrucciones estrictas:
        - No inventes información. Si un dato no aparece en la cita, déjalo nulo.
        
        Citas:
        """ + combined_text[:60000]

        import time
        models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-lite']
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': ReferenceList,
                        'temperature': 0.1
                    }
                )
                parsed = ReferenceList.model_validate_json(response.text)
                if parsed and parsed.references:
                    return parsed.references
            except Exception as e:
                print(f"Modelo {model_name} falló parseando referencias: {e}")
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    continue
                time.sleep(3)
                
    # Fallback si IA no responde
    return [parse_reference_item_fallback(item['raw_text'], f"B{idx+1}") for idx, item in enumerate(ref_items)]

def build_ref_list_xml(soup: BeautifulSoup, references: List[ReferenceItem], raw_nodes: List[dict], section_title: str = "Referencias") -> BeautifulSoup:
    ref_list = soup.new_tag('ref-list')
    title = soup.new_tag('title')
    title.string = section_title if section_title else "Referencias"
    ref_list.append(title)
    
    if references:
        for idx, ref in enumerate(references, start=1):
            ref_id = f"B{idx}"
            ref_tag = soup.new_tag('ref', id=ref_id)
            
            mixed = soup.new_tag('mixed-citation')
            raw_html = raw_nodes[idx-1]['raw_html'] if idx <= len(raw_nodes) else ref.raw_text
            mixed_soup = BeautifulSoup(f"<span>{raw_html}</span>", 'xml')
            for child in list(mixed_soup.span.contents):
                mixed.append(child)
            ref_tag.append(mixed)
            
            pub_type = ref.publication_type if ref.publication_type in ['journal', 'book', 'thesis', 'conference', 'webpage'] else 'other'
            elem = soup.new_tag('element-citation', **{"publication-type": pub_type})
            
            if ref.authors:
                pg = soup.new_tag('person-group', **{"person-group-type": "author"})
                for a in ref.authors:
                    name_tag = soup.new_tag('name')
                    sn = soup.new_tag('surname')
                    sn.string = a.surname
                    name_tag.append(sn)
                    if a.given_names:
                        gn = soup.new_tag('given-names')
                        gn.string = a.given_names
                        name_tag.append(gn)
                    pg.append(name_tag)
                elem.append(pg)
                
            if ref.article_title:
                at = soup.new_tag('article-title')
                at.string = ref.article_title
                elem.append(at)
                
            if ref.source:
                src = soup.new_tag('source')
                src.string = ref.source
                elem.append(src)
                
            if ref.publisher_name:
                pn = soup.new_tag('publisher-name')
                pn.string = ref.publisher_name
                elem.append(pn)
                
            if ref.year:
                yr = soup.new_tag('year')
                yr.string = ref.year
                elem.append(yr)
                
            if ref.volume:
                vol = soup.new_tag('volume')
                vol.string = ref.volume
                elem.append(vol)
                
            if ref.issue:
                iss = soup.new_tag('issue')
                iss.string = ref.issue
                elem.append(iss)
                
            if ref.fpage:
                fp = soup.new_tag('fpage')
                fp.string = ref.fpage
                elem.append(fp)
            if ref.lpage:
                lp = soup.new_tag('lpage')
                lp.string = ref.lpage
                elem.append(lp)
                
            if ref.doi:
                clean_doi = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', ref.doi.strip(), flags=re.IGNORECASE)
                clean_doi = re.sub(r'^doi:\s*', '', clean_doi, flags=re.IGNORECASE)
                doi_tag = soup.new_tag('pub-id', **{"pub-id-type": "doi"})
                doi_tag.string = clean_doi
                elem.append(doi_tag)
                
            if ref.url:
                clean_url = ref.url.strip()
                url_tag = soup.new_tag('ext-link', **{"ext-link-type": "uri", "xlink:href": clean_url})
                url_tag.string = clean_url
                elem.append(url_tag)
                
            ref_tag.append(elem)
            ref_list.append(ref_tag)
    elif raw_nodes:
        for idx, node in enumerate(raw_nodes, start=1):
            ref_tag = soup.new_tag('ref', id=f"B{idx}")
            mixed = soup.new_tag('mixed-citation')
            mixed_soup = BeautifulSoup(f"<span>{node['raw_html']}</span>", 'xml')
            for child in list(mixed_soup.span.contents):
                mixed.append(child)
            ref_tag.append(mixed)
            
            elem = soup.new_tag('element-citation', **{"publication-type": "other"})
            src = soup.new_tag('source')
            src.string = node['raw_text']
            elem.append(src)
            ref_tag.append(elem)
            ref_list.append(ref_tag)
    else:
        ref_tag = soup.new_tag('ref', id="B1")
        mixed = soup.new_tag('mixed-citation')
        mixed.string = "1. Referencia no disponible en el texto original."
        ref_tag.append(mixed)
        
        elem = soup.new_tag('element-citation', **{"publication-type": "other"})
        src = soup.new_tag('source')
        src.string = "Referencia no disponible"
        elem.append(src)
        ref_tag.append(elem)
        ref_list.append(ref_tag)
            
    return ref_list

def extract_and_clean_eng_front_stub(soup_eng: BeautifulSoup, metadata: ArticleMetadata):
    body_eng = soup_eng.find('body')
    if not body_eng:
        return
        
    for elem in list(body_eng.find_all(['p', 'sec'], limit=80)):
        if not isinstance(elem, Tag):
            continue
        txt = elem.get_text(strip=True)
        txt_low = txt.lower()
        title_elem = elem.find('title')
        title_clean = title_elem.get_text(strip=True).lower() if title_elem else ''
        
        # English Keywords (sec or p) - match strictly English headers
        if ("key words" in title_clean or "keywords" in title_clean or txt_low.startswith("key words:") or txt_low.startswith("keywords:")) and "palavras-chave" not in title_clean and not txt_low.startswith("palavras-chave:"):
            p_kw = elem.find('p') if elem.name == 'sec' else elem
            if p_kw:
                raw_kw = re.sub(r'^(?:Key words|Keywords):\s*', '', p_kw.get_text(strip=True), flags=re.IGNORECASE).rstrip('.')
                kw_list = [re.sub(r'\s+', ' ', k).strip() for k in re.split(r'[;,]', raw_kw) if k.strip()]
                if kw_list:
                    metadata.keywords_en = kw_list
            elem.decompose()
            continue
            
        # English Abstract
        if ("objective:" in txt_low or "methodology:" in txt_low or "results:" in txt_low or "conclusions:" in txt_low) and len(txt) > 80:
            clean_abs = re.sub(r'^(?:Abstract|Abstract:)\s*', '', txt, flags=re.IGNORECASE).strip()
            if clean_abs:
                if not any(clean_abs.lower().startswith(p) for p in ["introduction:", "introducción:", "abstract:"]):
                    clean_abs = "Introduction: " + clean_abs
                metadata.abstract_en = format_abstract_text(clean_abs)
            elem.decompose()
            continue
            
        # Purge Spanish / Portuguese metadata header blocks in English DOCX before Introduction body section
        if any(txt_low.startswith(p) for p in ["resumen", "introducción:", "palabras clave:", "abstrato", "introdução:", "palavras-chave:"]) or txt_low in ["resumen", "abstrato", "abstract"]:
            elem.decompose()

def process_eng_docx_to_subarticle(soup_main: BeautifulSoup, eng_docx_path: str, metadata: ArticleMetadata):
    """
    Convierte el archivo DOCX en inglés (_ENG.docx) y construye el elemento <sub-article article-type="translation" id="s1" xml:lang="en">
    para ser adjuntado al nodo <article> principal.
    """
    from bs4 import BeautifulSoup
    from bs4.element import Tag
    import pypandoc
    
    xml_output_eng = pypandoc.convert_file(
        eng_docx_path, 
        to='jats', 
        format='docx', 
        extra_args=['--standalone']
    )
    soup_eng = BeautifulSoup(xml_output_eng, 'xml')
    
    # Extraer metadatos de cabecera y limpiar el body en inglés
    extract_and_clean_eng_front_stub(soup_eng, metadata)
    
    sub_article = soup_main.new_tag('sub-article', **{
        'article-type': 'translation',
        'id': 's1',
        'xml:lang': 'en'
    })
    
    front_stub = soup_main.new_tag('front-stub')
    
    art_cats = soup_main.new_tag('article-categories')
    subj_grp = soup_main.new_tag('subj-group', **{'subj-group-type': 'heading'})
    subj = soup_main.new_tag('subject')
    
    cat_val = metadata.article_category or "Original Article"
    cat_map = {
        "artículo original": "Original Article",
        "articulo original": "Original Article",
        "artículos": "Original Articles",
        "articulos": "Original Articles",
        "investigación": "Research Article",
        "investigacion": "Research Article",
        "revisión": "Review Article",
        "revision": "Review Article",
        "ensayo": "Essay",
        "reporte de caso": "Case Report",
        "caso clínico": "Clinical Case",
        "carta al editor": "Letter to the Editor"
    }
    subj.string = cat_map.get(unaccent(cat_val).lower(), cat_val)
    subj_grp.append(subj)
    art_cats.append(subj_grp)
    front_stub.append(art_cats)
    
    # Título en Inglés
    title_group = soup_main.new_tag('title-group')
    art_title = soup_main.new_tag('article-title')
    eng_title_text = clean_article_title(metadata.article_title_en)
    if not eng_title_text or eng_title_text in ["Title not available", "RESEARCH", "INVESTIGACIÓN"]:
        for p in soup_eng.find_all(['title', 'p'], limit=10):
            t = clean_article_title(p.get_text(strip=True))
            if t and len(t) > 15 and not any(t.lower().startswith(prefix) for prefix in ["abstract", "keywords", "issn", "doi:", "vol", "http"]):
                eng_title_text = t
                break
    if eng_title_text and eng_title_text != "Title not available":
        metadata.article_title_en = eng_title_text
    art_title.string = clean_article_title(eng_title_text) if eng_title_text else "Title not available"
    title_group.append(art_title)
    front_stub.append(title_group)
    
    # Abstract en Inglés
    eng_abstract_text = format_abstract_text(metadata.abstract_en)
    if not eng_abstract_text or eng_abstract_text in ["Abstract not available.", "Resumen no disponible."]:
        for p in soup_eng.find_all(['p', 'sec'], limit=15):
            txt = p.get_text(strip=True)
            txt_low = txt.lower()
            if ("objective:" in txt_low or "methodology:" in txt_low or "results:" in txt_low or "conclusions:" in txt_low) and len(txt) > 80:
                eng_abstract_text = format_abstract_text(txt)
                break
    if eng_abstract_text and eng_abstract_text != "Abstract not available.":
        metadata.abstract_en = eng_abstract_text
                
    abstract_tag = build_structured_abstract_xml(soup_main, eng_abstract_text, tag_name="abstract", lang="en")
    front_stub.append(abstract_tag)
    
    # Keywords en Inglés
    kwd_group = soup_main.new_tag('kwd-group', **{'xml:lang': 'en'})
    kwd_title = soup_main.new_tag('title')
    kwd_title.string = "Key words:"
    kwd_group.append(kwd_title)
    
    kwds = []
    if metadata.keywords_en and metadata.keywords_en != ["Keyword not available"]:
        kwds = metadata.keywords_en
    else:
        kwd_node = soup_eng.find('kwd-group')
        if kwd_node:
            kwds = [k.get_text(strip=True) for k in kwd_node.find_all('kwd') if k.get_text(strip=True)]
            if not kwds:
                raw_kw_txt = kwd_node.get_text(strip=True)
                kwds = [k.strip().rstrip('.') for k in re.split(r'[;,]', raw_kw_txt) if k.strip() and k.lower() not in ["key words:", "keywords:"]]
                
    if not kwds or kwds == ["Keyword not available"]:
        for p in soup_eng.find_all(['p', 'sec'], limit=15):
            txt = p.get_text(strip=True)
            txt_low = txt.lower()
            if "key words" in txt_low or "keywords" in txt_low:
                raw_kw = re.sub(r'^(?:Key words|Keywords):\s*', '', txt, flags=re.IGNORECASE).rstrip('.')
                kwds = [k.strip() for k in re.split(r'[;,]', raw_kw) if k.strip()]
                break

    if kwds:
        metadata.keywords_en = kwds
    else:
        kwds = ["Keyword not available"]

    for kw in kwds:
        if kw.lower() in ["key words:", "keywords:"]:
            continue
        k = soup_main.new_tag('kwd')
        k.string = kw
        kwd_group.append(k)
    front_stub.append(kwd_group)
    
    sub_article.append(front_stub)
    
    # Limpiar metadatos de cabecera en inglés hasta la primera sección de Introduction
    for child in list(soup_eng.find('body').children):
        if not isinstance(child, Tag):
            continue
        text_clean = unaccent(child.get_text(strip=True).lower())
        title_elem = child.find('title')
        title_clean = unaccent(title_elem.get_text(strip=True).lower()) if title_elem else ''
        
        if "introduction" in title_clean or "introduction" in text_clean[:50]:
            break
        child.decompose()

    restructure_body_to_sections(soup_eng)
    clean_phantom_sections(soup_eng)
    format_figures(soup_eng)
    
    from docx_table_parser import build_jats_table_from_docx, sanitize_named_content_and_local_paths
    sanitize_named_content_and_local_paths(soup_eng)
    build_jats_table_from_docx(eng_docx_path, soup_eng)
    format_tables(soup_eng)
    
    format_sections(soup_eng)
    fix_section_title_case(soup_eng)
    auto_link_cross_references(soup_eng)
    fix_footnotes(soup_eng)
    
    body_eng = soup_eng.find('body')
    if body_eng:
        new_body = soup_main.new_tag('body')
        for child in list(body_eng.children):
            if isinstance(child, Tag):
                txt_clean = unaccent(child.get_text(strip=True).lower())
                title_elem = child.find('title')
                title_clean = unaccent(title_elem.get_text(strip=True).lower()) if title_elem else ''
                
                # Detener la ingesta del body en inglés si se alcanza la bibliografía o bloques en español/portugués al final
                if any(k in title_clean for k in ["references", "referencias", "bibliograf", "works cited"]) or any(k in txt_clean[:40] for k in ["references", "referencias"]):
                    break
                if any(k in title_clean or k in txt_clean[:40] for k in ["resumen", "palavras-chave", "abstrato", "introducao", "palabras clave"]):
                    break
                    
                new_body.append(BeautifulSoup(str(child), 'xml'))
        sub_article.append(new_body)
    return sub_article


def validate_sps(xml_str: str) -> dict:
    """
    Validador estricto SciELO SPS basado en lxml.etree y XPath.
    Audita el XML generado por BeautifulSoup para certificar el cumplimiento de la norma.
    """
    from lxml import etree
    errors = []
    warnings = []
    
    # 1. Parseo estricto sintáctico XML con lxml
    try:
        parser = etree.XMLParser(recover=False)
        xml_doc = etree.fromstring(xml_str.encode('utf-8'), parser=parser)
    except etree.XMLSyntaxError as e:
        return {
            "is_valid": False,
            "errors": [f"Error sintáctico XML: {str(e)}"],
            "warnings": []
        }

    # 2. Regla SciELO SPS: Verificar que ref-list contenga al menos un elemento <ref>
    if xml_doc.xpath('//ref-list') and not xml_doc.xpath('//ref-list/ref'):
        errors.append("SciELO SPS exige al menos un elemento <ref> dentro de <ref-list>.")

    # 3. Regla SciELO SPS: Atributo 'country' en <country> debe ser un código ISO 3166-1 alpha-2 de 2 letras
    for country_elem in xml_doc.xpath('//aff/country'):
        iso_code = country_elem.get('country')
        if not iso_code or len(iso_code) != 2 or not iso_code.isupper():
            errors.append(f"El atributo 'country' en <country> debe ser un código ISO de 2 letras mayúsculas (ej. MX, ES). Valor actual: '{iso_code}'")

    # 4. Regla SciELO SPS: Verificar que todas las citas cruzadas <xref rid="..."> apunten a un id existente
    all_ids = set(xml_doc.xpath('//@id'))
    for xref in xml_doc.xpath('//xref'):
        rid = xref.get('rid')
        if rid:
            for target_id in rid.split():
                if target_id not in all_ids:
                    warnings.append(f"Referencia cruzada <xref rid='{target_id}'> huérfana: no existe ningún elemento con id='{target_id}'.")

    # 5. Regla SciELO SPS: Atributos específicos en <article>
    article_nodes = xml_doc.xpath('//article')
    if article_nodes:
        art = article_nodes[0]
        if art.get('specific-use') != 'sps-1.9':
            warnings.append(f"Atributo specific-use debe ser 'sps-1.9'. Valor actual: '{art.get('specific-use')}'")
        if art.get('dtd-version') != '1.1':
            warnings.append(f"Atributo dtd-version debe ser '1.1'. Valor actual: '{art.get('dtd-version')}'")

    # 6. Regla SciELO SPS: <pub-date> debe contener <year>
    for pub_date in xml_doc.xpath('//pub-date'):
        if not pub_date.xpath('year'):
            errors.append("El elemento <pub-date> debe incluir la etiqueta <year>.")

    is_valid = len(errors) == 0
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings
    }

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/convert")
async def convert_docx(file: UploadFile = File(...), eng_file: Optional[UploadFile] = File(None)):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_extension = os.path.splitext(file.filename)[1].lower() if file.filename else ".docx"
        input_path = os.path.join(tmpdir, f"{uuid.uuid4()}.docx")
        
        eng_input_path = None
        if eng_file and eng_file.filename:
            eng_input_path = os.path.join(tmpdir, f"{uuid.uuid4()}_ENG.docx")
            with open(eng_input_path, "wb") as f:
                f.write(await eng_file.read())
        
        if file_extension == ".pdf":
            pdf_path = os.path.join(tmpdir, f"{uuid.uuid4()}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(await file.read())
            
            try:
                cv = Converter(pdf_path)
                # Convertir todo el PDF a docx
                cv.convert(input_path, start=0, end=None)
                cv.close()
            except Exception as e:
                import traceback
                traceback.print_exc()
                return Response(content=f"Error converting PDF to DOCX: {str(e)}", status_code=500)
        else:
            with open(input_path, "wb") as f:
                f.write(await file.read())
        
        try:
            xml_output = pypandoc.convert_file(
                input_path, 
                to='jats', 
                format='docx', 
                extra_args=['--standalone']
            )
            
            soup = BeautifulSoup(xml_output, 'xml')
            header_text = extract_docx_headers_text(input_path)
            raw_text = header_text + "\n" + soup.get_text(separator='\n', strip=True)
            
            metadata, used_fallback = await extract_metadata_from_text(raw_text)
            
            old_front = soup.find('front')
            scielo_front = build_scielo_front(soup, metadata)
            
            if old_front:
                old_front.replace_with(scielo_front)
            elif soup.article:
                soup.article.insert(0, scielo_front)
                
            # Limpiar metadatos duplicados en el body
            clean_body_duplicate_metadata(soup, metadata)
            
            # Convertir párrafos a secciones (sec)
            restructure_body_to_sections(soup)
            
            # Extraer abstracts estructurados y no estructurados antes de limpiar
            extract_structured_abstracts_from_body(soup, metadata)
            
            # Limpiar secciones vacías o fantasma
            clean_phantom_sections(soup)
            
            # Formatear imágenes a la estructura <fig> de SciELO
            format_figures(soup)
            
            # Formatear tablas a la estructura <table-wrap> de SciELO desde doc.element.body
            from docx_table_parser import build_jats_table_from_docx, sanitize_named_content_and_local_paths
            sanitize_named_content_and_local_paths(soup)
            build_jats_table_from_docx(input_path, soup)
            format_tables(soup)
            
            # Asignar sec-type canónico a las secciones y corregir capitalización a Sentence Case
            format_sections(soup)
            fix_section_title_case(soup)
            
            # Corregir y validar enlaces e id de referencias cruzadas <xref>
            auto_link_cross_references(soup)
            
            # Corregir footnotes y x-refs
            fix_footnotes(soup)
            
            # SciELO Style Fixes: fn-type en <fn>
            for fn in soup.find_all('fn'):
                if not fn.has_attr('fn-type'):
                    fn['fn-type'] = "other"
                    
            # Extraer referencias del body y parsearlas con Gemini
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
                
                # Garantizar orden de marcado igual al experto: <ref-list> primero, luego <fn-group>
                fn_group = back.find('fn-group')
                if fn_group:
                    fn_group.extract()
                    back.append(fn_group)

            # Si se proporcionó la traducción en inglés (_ENG.docx), procesar e insertar <sub-article>
            if eng_input_path and os.path.exists(eng_input_path):
                sub_art_tag = process_eng_docx_to_subarticle(soup, eng_input_path, metadata)
                if sub_art_tag and soup.article:
                    old_sub = soup.article.find('sub-article')
                    if old_sub:
                        old_sub.decompose()
                    soup.article.append(sub_art_tag)
                    
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
                soup.article['xml:lang'] = metadata.language if metadata.language else "es"
            
            # Actualizar counts dinámicamente
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
            
            # Añadir DOCTYPE requerido por SciELO SPS
            import re
            final_xml = str(soup)
            # Limpiar cualquier declaración XML o DOCTYPE vieja generada por BeautifulSoup
            final_xml = re.sub(r'<\?xml.*?\?>\n?', '', final_xml)
            final_xml = re.sub(r'<!DOCTYPE.*?>\n?', '', final_xml)
            
            # Recomendación 3: Inactivar la extracción de rutas locales (file:///)
            final_xml = re.sub(r'(?:xlink:href|href)="file:///[^"]+"', '', final_xml)
            final_xml = re.sub(r'file:///[^\s<"\']+', '', final_xml)
            
            # SciELO SPS: Todos los atributos href deben convertirse a xlink:href
            final_xml = re.sub(r'(?<!xlink:)\bhref="', r'xlink:href="', final_xml)
            
            doctype = '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
            final_xml = f'<?xml version="1.0" encoding="utf-8"?>\n{doctype}\n{final_xml.strip()}'
            
            # Auditoría y Validación Final SciELO SPS con lxml.etree
            validation_report = validate_sps(final_xml)
            print(f"Resultado de Validación SciELO SPS lxml: Válido={validation_report['is_valid']}, Errores={len(validation_report['errors'])}, Advertencias={len(validation_report['warnings'])}")
            if validation_report['errors']:
                print("Errores de validación:", validation_report['errors'])
            if validation_report['warnings']:
                print("Advertencias de validación:", validation_report['warnings'])

            headers = {
                "X-SPS-Validation-Valid": str(validation_report["is_valid"]).lower(),
                "X-SPS-Errors-Count": str(len(validation_report["errors"])),
                "X-SPS-Warnings-Count": str(len(validation_report["warnings"])),
                "X-Metadata-Extraction-Fallback": str(used_fallback).lower()
            }
            
            return Response(content=final_xml.encode('utf-8'), media_type="application/xml; charset=utf-8", headers=headers)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(content=f"Error processing document: {str(e)}", status_code=500)
