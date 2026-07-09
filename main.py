from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
import os
import pypandoc
import tempfile
import uuid
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional

load_dotenv()

# Download pandoc if not installed
try:
    pypandoc.get_pandoc_version()
except OSError:
    pypandoc.download_pandoc()

app = FastAPI()

# Mount the static directory to serve index.html
app.mount("/static", StaticFiles(directory="static"), name="static")

# Gemini Client Config
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# Pydantic Schemas for Metadata Extraction
class Author(BaseModel):
    given_names: str = Field(description="Nombres del autor")
    surname: str = Field(description="Apellidos del autor")
    orcid: Optional[str] = Field(description="ORCID del autor si existe, formato: 0000-0000-0000-0000", default=None)
    email: Optional[str] = Field(description="Correo electrónico del autor", default=None)
    affiliation_id: str = Field(description="ID de la afiliación (ej. aff1)")

class Affiliation(BaseModel):
    id: str = Field(description="ID único de esta afiliación, ej: aff1")
    institution: str = Field(description="Nombre de la institución (Universidad, Centro de investigación, etc.)")
    country: Optional[str] = Field(description="País de la institución", default=None)

class DateInfo(BaseModel):
    day: Optional[str] = Field(description="Día con dos dígitos", default=None)
    month: Optional[str] = Field(description="Mes con dos dígitos", default=None)
    year: Optional[str] = Field(description="Año con cuatro dígitos", default=None)

class ArticleMetadata(BaseModel):
    article_category: Optional[str] = Field(description="Categoría del artículo (ej. Artículos, Nota Crítica)", default="Artículos")
    journal_title: Optional[str] = Field(description="Nombre de la revista", default=None)
    issn: Optional[str] = Field(description="ISSN de la revista", default=None)
    doi: Optional[str] = Field(description="DOI del artículo", default=None)
    article_title: str = Field(description="Título del artículo")
    abstract_es: Optional[str] = Field(description="Resumen en español", default=None)
    abstract_en: Optional[str] = Field(description="Abstract en inglés", default=None)
    keywords_es: List[str] = Field(description="Palabras clave en español", default_factory=list)
    keywords_en: List[str] = Field(description="Keywords en inglés", default_factory=list)
    authors: List[Author] = Field(description="Lista de autores", default_factory=list)
    affiliations: List[Affiliation] = Field(description="Lista de afiliaciones de los autores", default_factory=list)
    received_date: Optional[DateInfo] = Field(description="Fecha de recepción", default=None)
    accepted_date: Optional[DateInfo] = Field(description="Fecha de aceptación", default=None)
    published_date: Optional[DateInfo] = Field(description="Fecha de publicación", default=None)

async def extract_metadata_from_text(text: str) -> ArticleMetadata:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Advertencia: No hay GEMINI_API_KEY. Devolviendo metadatos vacíos.")
        return ArticleMetadata(article_title="Sin Título")
        
    prompt = """
    Analiza el siguiente texto extraído del principio de un artículo científico.
    Extrae todos los metadatos relevantes como título, autores, afiliaciones (instituciones), 
    resumen, palabras clave, fechas de recepción/aceptación/publicación, DOI y categoría del artículo si están presentes.
    
    Texto:
    """ + text[:4000]
    
    # Volvemos a usar gemini-2.5-flash. Si hay error 503, solo es cuestión de reintentar en unos segundos.
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'response_schema': ArticleMetadata,
            'temperature': 0.1
        }
    )
    
    # Parsear el string JSON a nuestro modelo Pydantic
    return ArticleMetadata.model_validate_json(response.text)

def build_scielo_front(soup: BeautifulSoup, metadata: ArticleMetadata) -> BeautifulSoup:
    """Modifica el soup XML inyectando la estructura de SciELO en el <front>"""
    # 1. Crear el nuevo <front>
    new_front = soup.new_tag("front")
    
    # 2. Journal Meta
    journal_meta = soup.new_tag("journal-meta")
    
    jid = soup.new_tag("journal-id", **{"journal-id-type": "publisher-id"})
    jid.string = "journal_id"
    journal_meta.append(jid)
    
    if metadata.journal_title:
        jtg = soup.new_tag("journal-title-group")
        jt = soup.new_tag("journal-title")
        jt.string = metadata.journal_title
        jtg.append(jt)
        
        ajt = soup.new_tag("abbrev-journal-title", **{"abbrev-type": "publisher"})
        ajt.string = "Abbrev. title"
        jtg.append(ajt)
        
        journal_meta.append(jtg)
    if metadata.issn:
        issn = soup.new_tag("issn", **{"pub-type": "epub"})
        issn.string = metadata.issn
        journal_meta.append(issn)
    
    # Publisher dummy para imitar el original
    publisher = soup.new_tag("publisher")
    pub_name = soup.new_tag("publisher-name")
    pub_name.string = "Institución Editora"
    publisher.append(pub_name)
    journal_meta.append(publisher)
    
    new_front.append(journal_meta)
    
    # 3. Article Meta
    article_meta = soup.new_tag("article-meta")
    if metadata.doi:
        doi = soup.new_tag("article-id", **{"pub-id-type": "doi"})
        doi.string = metadata.doi
        article_meta.append(doi)
        
    # Article categories
    if metadata.article_category:
        article_categories = soup.new_tag("article-categories")
        subj_group = soup.new_tag("subj-group", **{"subj-group-type": "heading"})
        subject = soup.new_tag("subject")
        subject.string = metadata.article_category
        subj_group.append(subject)
        article_categories.append(subj_group)
        article_meta.append(article_categories)
        
    title_group = soup.new_tag("title-group")
    article_title = soup.new_tag("article-title")
    article_title.string = metadata.article_title
    title_group.append(article_title)
    article_meta.append(title_group)
    
    # Authors and Affiliations
    contrib_group = soup.new_tag("contrib-group")
    for author in metadata.authors:
        contrib = soup.new_tag("contrib", **{"contrib-type": "author"})
        if author.orcid:
            orcid = soup.new_tag("contrib-id", **{"contrib-id-type": "orcid"})
            orcid.string = author.orcid
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
        contrib_group.append(contrib)
        
    for aff in metadata.affiliations:
        aff_tag = soup.new_tag("aff", id=aff.id)
        inst = soup.new_tag("institution", **{"content-type": "original"})
        inst.string = aff.institution
        aff_tag.append(inst)
        
        # SciELO requiere el atributo 'country' con un código ISO 3166 válido (ej. ES, MX, US). Usamos ES por defecto.
        country = soup.new_tag("country", country="ES")
        country.string = aff.country if aff.country else "País Desconocido"
        aff_tag.append(country)
        
        contrib_group.append(aff_tag)
        
    if metadata.authors:
        article_meta.append(contrib_group)
        
    # Pub dates (debe ir ANTES de elocation-id según el DTD de JATS)
    if metadata.published_date and metadata.published_date.year:
        pub_date = soup.new_tag("pub-date", **{"date-type": "pub", "publication-format": "electronic"})
        if metadata.published_date.day:
            day = soup.new_tag("day")
            day.string = metadata.published_date.day
            pub_date.append(day)
        if metadata.published_date.month:
            month = soup.new_tag("month")
            month.string = metadata.published_date.month
            pub_date.append(month)
        year = soup.new_tag("year")
        year.string = metadata.published_date.year
        pub_date.append(year)
        article_meta.append(pub_date)
        
    # Elocation-id
    eloc = soup.new_tag("elocation-id")
    eloc.string = "e000"
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
    
    # Abstracts
    if metadata.abstract_es:
        abstract = soup.new_tag("abstract")
        title = soup.new_tag("title")
        title.string = "Resumen:"
        abstract.append(title)
        p = soup.new_tag("p")
        p.string = metadata.abstract_es
        abstract.append(p)
        article_meta.append(abstract)
        
    if metadata.abstract_en:
        trans_abstract = soup.new_tag("trans-abstract", **{"xml:lang": "en"})
        title = soup.new_tag("title")
        title.string = "Abstract:"
        trans_abstract.append(title)
        p = soup.new_tag("p")
        p.string = metadata.abstract_en
        trans_abstract.append(p)
        article_meta.append(trans_abstract)
        
    # Keywords
    if metadata.keywords_es:
        kwd_group = soup.new_tag("kwd-group", **{"xml:lang": "es"})
        title = soup.new_tag("title")
        title.string = "Palabras clave:"
        kwd_group.append(title)
        for kwd in metadata.keywords_es:
            k = soup.new_tag("kwd")
            k.string = kwd
            kwd_group.append(k)
        article_meta.append(kwd_group)
        
    if metadata.keywords_en:
        kwd_group = soup.new_tag("kwd-group", **{"xml:lang": "en"})
        title = soup.new_tag("title")
        title.string = "Keywords:"
        kwd_group.append(title)
        for kwd in metadata.keywords_en:
            k = soup.new_tag("kwd")
            k.string = kwd
            kwd_group.append(k)
        article_meta.append(kwd_group)
        
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
        
    keywords_to_remove = ["resumen", "abstract", "palabras clave", "keywords", "recibido", "aceptado", "publicado", "doi"]
    if metadata.article_title:
        keywords_to_remove.append(metadata.article_title.lower())
    for author in metadata.authors:
        keywords_to_remove.append(author.surname.lower())
        if author.email:
            keywords_to_remove.append(author.email.lower())
            
    # Limpiamos los primeros 25 parrafos buscando coincidencias
    for p in body.find_all('p', limit=25):
        text = p.get_text(strip=True)
        text_lower = text.lower()
        should_remove = False
        
        for kw in keywords_to_remove:
            if kw and kw in text_lower:
                should_remove = True
                break
                
        if "issn" in text_lower or text_lower.startswith("núm.") or text_lower.startswith("vol."):
            should_remove = True
            
        if "orcid.org" in text_lower or "correo:" in text_lower:
            should_remove = True
            
        if should_remove:
            p.decompose()

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/convert")
async def convert_docx(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, f"{uuid.uuid4()}.docx")
        
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
            raw_text = soup.get_text(separator='\n', strip=True)
            
            metadata = await extract_metadata_from_text(raw_text)
            
            old_front = soup.find('front')
            scielo_front = build_scielo_front(soup, metadata)
            
            if old_front:
                old_front.replace_with(scielo_front)
            elif soup.article:
                soup.article.insert(0, scielo_front)
                
            # Limpiar metadatos duplicados en el body
            clean_body_duplicate_metadata(soup, metadata)
            
            # SciELO Style Fixes: fn-type and ref-list
            for fn in soup.find_all('fn'):
                if not fn.has_attr('fn-type'):
                    fn['fn-type'] = "other"
                    
            back = soup.find('back')
            if not back:
                back = soup.new_tag('back')
                if soup.article:
                    soup.article.append(back)
            if back and not back.find('ref-list'):
                ref_list = soup.new_tag('ref-list')
                title = soup.new_tag('title')
                title.string = "Referencias"
                ref_list.append(title)
                
                # SciELO requiere al menos un elemento <ref> dentro de <ref-list>
                ref = soup.new_tag('ref', id="B1")
                
                mixed_citation = soup.new_tag('mixed-citation')
                mixed_citation.string = "1. Referencia no disponible en el texto original."
                ref.append(mixed_citation)
                
                # SciELO exige element-citation
                element_citation = soup.new_tag('element-citation', **{"publication-type": "other"})
                source = soup.new_tag('source')
                source.string = "Referencia no disponible"
                element_citation.append(source)
                ref.append(element_citation)
                
                ref_list.append(ref)
                
                back.append(ref_list)
                
            if soup.article:
                soup.article['xmlns:mml'] = "http://www.w3.org/1998/Math/MathML"
                soup.article['xmlns:xlink'] = "http://www.w3.org/1999/xlink"
                soup.article['article-type'] = "research-article"
                soup.article['dtd-version'] = "1.1"
                soup.article['specific-use'] = "sps-1.9"
                soup.article['xml:lang'] = "es"
            
            # Actualizar ref-count dinámicamente según la cantidad real de <ref>
            rc = soup.find('ref-count')
            if rc:
                rc['count'] = str(len(soup.find_all('ref')))
            
            # Añadir DOCTYPE requerido por SciELO SPS
            import re
            final_xml = str(soup)
            # Limpiar cualquier declaración XML o DOCTYPE vieja generada por BeautifulSoup
            final_xml = re.sub(r'<\?xml.*?\?>\n?', '', final_xml)
            final_xml = re.sub(r'<!DOCTYPE.*?>\n?', '', final_xml)
            
            doctype = '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">'
            final_xml = f'<?xml version="1.0" encoding="utf-8"?>\n{doctype}\n{final_xml.strip()}'
            
            return Response(content=final_xml, media_type="application/xml")
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(content=f"Error processing document: {str(e)}", status_code=500)
