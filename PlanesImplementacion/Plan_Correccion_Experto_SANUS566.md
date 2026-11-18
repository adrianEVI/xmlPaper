# Plan de Implementación: Corrección Integral de SANUS 566 (Choque Séptico)

Se estructuran las correcciones específicas para eliminar la contaminación de metadatos del artículo 573 y resolver los 10 puntos críticos señalados por el experto para el artículo 566.

---

## User Review Required

> [!IMPORTANT]
> **Puntos Críticos de Ajuste para SANUS 566:**
> 1. **Metadatos en Portugués para 566:**
>    - **Título:** *"Processo de enfermagem à pessoa com choque séptico após cirurgia de laparotomia em terapia intensiva"*
>    - **Palabras Clave:** `Processo de enfermagem`, `Choque séptico`, `Enfermagem em terapia intensiva (DeCS)`
> 2. **Grados Académicos y Afiliaciones Fieles (4 Afiliaciones):**
>    - López-Navarro: *Especialidad en Enfermería en Cuidados Intensivos*
>    - Valle-Figueroa & Ponce-Meza: *Maestría en Educación Basada en Competencias* (comparten `aff2`)
>    - Quintana-Zavala: *Doctorado en Enfermería* (`aff3`)
>    - Figueroa-Ibarra: *Doctorado en Ciencias Sociales* (`aff4`)
> 3. **Captions Reales de Tablas en 566 (4 Tablas ES + 4 Tablas EN = 8 total):**
>    - Sustituir los captions heredados del 573 por los correspondientes al proceso de atención de enfermería NANDA (Tabla 1 a Tabla 4 en ES y EN).
> 4. **Prevención de Citas Falsas para Códigos NANDA:**
>    - Evitar que los códigos de diagnóstico NANDA (`00421`, `00030`, `00031`) se transformen en etiquetas `<xref ref-type="bibr">`.
> 5. **Sección Semántica `cases`:**
>    - Convertir *"Presentación del caso"* en una sección autónoma `<sec sec-type="cases"><title>Presentación del caso</title>...</sec>`.
> 6. **Fecha de Publicación y Categoría Sub-Artículo:**
>    - Fecha: `15/12/2025`
>    - Categoría en Sub-artículo: `<subject>Praxis</subject>`
> 7. **Conteo de Referencias (`ref-count count="20"`) y Figuras:**
>    - Asignar `2448-6094-sanus-10-21-e566-gf1.jpg` y `2448-6094-sanus-10-21-e566-gf2.jpg`.

---

## Proposed Changes

### 1. Actualización de las Reglas Específicas de 566 (`fix_all_sanus_expert_rules.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Separar estrictamente la lógica de `566` de la de `573`.
- Definir `roles_566` e inyectar las 4 afiliaciones compartidas.
- Definir el metadato portugués exclusivo de `566`.
- Definir `cap_map_es` y `cap_map_en` específicos de `566`.
- Ignorar códigos NANDA (`00421`, `00030`, `00031`) en la vinculación de `<xref>`.
- Inyectar la sección `<sec sec-type="cases">` en "Presentación del caso".
- Fijar la fecha `15/12/2025` y el subject `Praxis` para `566`.

---

## Verification Plan

### Automated Tests & Verification
1. **Verificación de Metadatos PT y Roles en 566:**
   - Comprobar que en `566_ESP.xml` el título portugués mencione *"choque séptico"* y existan 4 afiliaciones.
2. **Verificación de Tablas y Conteo:**
   - Comprobar `count="8"` en `table-count` y que `t1` a `t4` tengan sus captions reales de NANDA.
3. **Verificación de Códigos NANDA y Conteo de Refs:**
   - Confirmar que `00421` no sea un `<xref ref-type="bibr">` y que `ref-count` sea 20.
