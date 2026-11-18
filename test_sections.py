from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from typing import Optional

class Affiliation(BaseModel):
    id: str = Field(description="ID único de esta afiliación, ej: aff1")
    institution: str = Field(description="Nombre principal de la institución o universidad (ej. Universidad Nacional Autónoma de México)")
    faculty: Optional[str] = Field(description="Facultad o escuela de la institución (ej. Facultad de Derecho, Facultad de Medicina)", default=None)
    department: Optional[str] = Field(description="Departamento o división académica (ej. Departamento de Bioquímica)", default=None)
    research_center: Optional[str] = Field(description="Centro, instituto o laboratorio de investigación (ej. Centro de Ciencias de la Complejidad, Instituto de Investigaciones Jurídicas)", default=None)
    city: Optional[str] = Field(description="Ciudad donde se ubica la institución", default=None)
    state: Optional[str] = Field(description="Estado, provincia o entidad federativa", default=None)
    postal_code: Optional[str] = Field(description="Código postal de la institución", default=None)
    country: Optional[str] = Field(description="País de la institución", default=None)

xml = """<?xml version="1.0" encoding="utf-8"?>
<body>
    <sec id="intro">
        <title>Introducción</title>
        <p>Texto</p>
    </sec>
    <sec id="methods">
        <title>Materiales y métodos</title>
        <p>Texto</p>
    </sec>
</body>
"""
soup = BeautifulSoup(xml, 'xml')

def format_sections(soup: BeautifulSoup):
    body = soup.find('body')
    if not body:
        return
        
    for sec in body.find_all('sec'):
        title = sec.find('title')
        if not title:
            continue
            
        text = title.get_text(strip=True).lower()
        if "introduc" in text:
            sec['sec-type'] = 'intro'
        elif "material" in text or "método" in text or "metodo" in text:
            sec['sec-type'] = 'materials|methods'
        elif "resultado" in text and "discus" in text:
            sec['sec-type'] = 'results|discussion'
        elif "resultado" in text:
            sec['sec-type'] = 'results'
        elif "discus" in text:
            sec['sec-type'] = 'discussion'
        elif "conclusi" in text:
            sec['sec-type'] = 'conclusions'

format_sections(soup)
print(soup.prettify())

# Test Affiliation with faculty, department, research_center, city, state, country
aff = Affiliation(
    id="aff1", 
    institution="Universidad Nacional Autónoma de México", 
    faculty="Facultad de Medicina",
    department="Departamento de Bioquímica",
    research_center="Instituto de Investigaciones Biomédicas",
    city="Ciudad de México", 
    state="CDMX",
    postal_code="04510", 
    country="México"
)
aff_tag = soup.new_tag("aff", id=aff.id)

import re
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

inst_orgname = soup.new_tag("institution", **{"content-type": "orgname"})
inst_orgname.string = aff.institution
aff_tag.append(inst_orgname)

orgdivs = []
if aff.faculty:
    orgdivs.append(aff.faculty)
if aff.research_center:
    orgdivs.append(aff.research_center)
if aff.department:
    orgdivs.append(aff.department)
    
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

print(aff_tag.prettify())
