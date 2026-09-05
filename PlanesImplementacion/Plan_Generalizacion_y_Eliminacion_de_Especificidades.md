# Plan de Implementación: Generalización del Sistema y Eliminación de Lógicas Específicas por Archivo

## Resumen Ejecutivo

Actualmente, el repositorio cuenta con una arquitectura dividida en dos grupos de código:
1. **Módulos Principales del Motor de Conversión** (`main.py`, `docx_table_parser.py`): Contienen la lógica general de extracción, estructuración JATS/SciELO y validación, pero albergan varias reglas fijas, palabras clave ad-hoc (ej. códigos NANDA, enfermería, marcas de revista como SANUS/Biolex) y valores por defecto fijos.
2. **Scripts de Corrección por Lotes y Parches Históricos** (`fix_all_sanus_expert_rules.py`, `sync_expert_precision.py`, `update_all_xmls_header_metadata.py`, `process_sanus_batch.py`, etc.): Contienen ramas condicionales explícitas basadas en el nombre del archivo (ej. `if "566" in filename:`, `if "573" in filename:`), asignando roles, afiliaciones, abstracts, fechas y figuras de forma estática para artículos específicos.

El objetivo de este plan es inventariar minuciosamente todas las dependencias específicas de archivos/revistas y proponer su reemplazo por algoritmos dinámicos y generalizables.

---

## 1. Diagnóstico e Inventario de Código Específico

### A. Archivos y Scripts de Corrección con Condicionales por Nombre de Archivo (`filename`)

| Archivo | Fragmento / Lógica Específica Detectada | Motivo de Especificidad |
| :--- | :--- | :--- |
| [`fix_all_sanus_expert_rules.py`](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py#L45-L270) | `if contrib_group and "566" in filename:`<br>`elif contrib_group and ("573" in filename or "560" in filename):`<br>`if "561" in filename:`<br>`if "549" in filename:` | Inyecta manualmente roles, afiliaciones, abstracts en portugués, pies de tabla y nombres de figuras según el número del archivo. |
| [`update_all_xmls_header_metadata.py`](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/update_all_xmls_header_metadata.py#L38-L54) | `order_map = {"549": "00113", "560": "00112", "561": "00304", "564": "00111", "566": "00202", "573": "00110"}` | Mapea de forma rígida IDs de artículos a números fijos `00xxx` basados en números de archivo. |
| [`sync_expert_precision.py`](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/sync_expert_precision.py#L11-L17) | `articles = [("549", "2448-6094-sanus-10-21-e549.xml", ...), ("566", ...)]` | Lista estática de nombres de archivo y pares de sincronización específicos de SANUS. |
| [`sync_biolex_expert_precision.py`](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/sync_biolex_expert_precision.py#L11-L26) | Lista estática de archivos `2007-5545-biolex-...` | Sincronización estática exclusiva para archivos del lote Biolex. |
| [`process_sanus_batch.py`](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/process_sanus_batch.py#L159-L166) | `scielo_map = {"549_ESP.docx": "2448-...", "566_ESP.docx": "..."}` | Mapeo fijo de nombres de archivo Word a nombres SciELO estándar. |
| [`apply_10_out_of_10_expert_fixes.py`](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/apply_10_out_of_10_expert_fixes.py) | Parches codificados para artículos específicos de enfermería. | Reglas de reemplazo de texto orientadas al documento 566. |

---

### B. Módulos Centrales (`main.py` y `docx_table_parser.py`)

Aun cuando `main.py` es el núcleo del servicio FastAPI, contiene varias reglas ad-hoc adaptadas a los ejemplos de prueba:

#### 1. En [`docx_table_parser.py`](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/docx_table_parser.py#L138):
- **Línea 138:**
  ```python
  if len(l.strip()) > 110 and not any(kw in l.lower() for kw in ['00421', 'diagnóstico', 'volumen']):
  ```
  - **Problema:** Contiene el código numérico `'00421'` (código de diagnóstico NANDA exclusivo del artículo 566) y palabras específicas (`'diagnóstico'`, `'volumen'`) para evitar dividir líneas en una tabla particular.

#### 2. En [`main.py`](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py):
- **Líneas 300, 314-315:** Búsqueda específica por nombre de revista `"SANUS"`:
  ```python
  vol_match = re.search(r'SANUS\.\s*\d{4};\s*(\d+)', text, re.IGNORECASE)
  ...
  if any(k in line_low for k in ["sanus", "issn", "doi:", "http", "www.", ...]):
  ```
  - **Problema:** Si el manuscrito proviene de otra revista (ej. *Revista Iberoamericana*, *Salud Pública*, *Nature*), este patrón no capturará el volumen en el encabezado.
- **Líneas 387-425 (`build_scielo_front`):** Bifurcación exclusiva `"biolex"` vs `"sanus"`:
  ```python
  is_biolex = "biolex" in jid_val or "biolex" in jtitle_val
  jid.string = "biolex" if is_biolex else (metadata.journal_id if metadata.journal_id else "sanus")
  ...
  # Hardcoded ISSNs y Publisher names:
  if is_biolex:
      issn_ppub.string = "2007-5634"
      issn_epub.string = "2007-5545"
      pub_name.string = "Universidad de Sonora, División de Ciencias Sociales"
  else:
      issn.string = metadata.issn if metadata.issn else "2448-6094"
      pub_name.string = metadata.publisher_name if metadata.publisher_name else "Universidad de Sonora, División de Ciencias Biológicas y de la Salud, Departamento de enfermería"
  ```
  - **Problema:** Cualquier artículo de cualquier otra institución o revista recibe por defecto los ISSNs y nombres de facultad de la Universidad de Sonora o de Sanus.
- **Línea 601:** `country.string = aff.country if aff.country else "México"` e inferencia ISO por defecto a `MX`.
- **Línea 640:** Año por defecto fijo `"2024"` en lugar de calcularlo dinámicamente o dejarlo nulo/extraído.
- **Línea 811:** Filtros de limpieza con palabras de enfermería:
  ```python
  elif "volumen" in text_lower and not any(w in text_lower for w in ["líquidos", "liquidos", "nanda", "diagnóstico"]):
  ```
- **Línea 1656:** Mapeo de secciones con términos específicos de enfermería:
  ```python
  elif "caso" in text or "proceso de enfermer" in text or "caso clín" in text:
      sec['sec-type'] = 'cases'
  ```
- **Líneas 2025, 2037:** Hardcoding en el sub-artículo en inglés:
  ```python
  subj.string = "Research"  # No traduce ni extrae la categoría real
  ...
  not any(t.lower().startswith(prefix) for prefix in ["abstract", "keywords", "sanus", "issn"])
  ```
- **Línea 2346:** `soup.article['xml:lang'] = "es"` (asume idioma principal español siempre, incluso si se procesa un artículo redactado originalmente en inglés o portugués).

---

## 2. Plan de Generalización Propuesto

### Fase 1: Limpieza y Generalización del Core (`main.py` y `docx_table_parser.py`)

1. **Extracción Dinámica y Universal de Metadatos de Revista (`journal-meta`):**
   - Eliminar las ramas `if is_biolex:` con valores fijos.
   - Extraer dinámicamente mediante el modelo Gemini y expresiones regulares genéricas:
     - Título de la revista (`journal_title`) y su identificador (`journal_id`).
     - Editorial / Publisher (`publisher_name`).
     - ISSN impreso y electrónico (`issn_ppub`, `issn_epub`, `issn`).
     - Si un dato no está presente en el documento, se omite o se extrae del texto/encabezado sin inyectar datos ficticios de una revista en particular.
2. **Extracción Universal de Volumen, Número y Año:**
   - Generalizar la expresión regular de volumen/número para que reconozca patrones canónicos de cualquier revista científica (ej. `Vol\.?\s*(\d+)`, `Núm\.?\s*(\d+)`, `\b(\d+)\((\d+)\):`, `Año\s*(\d+)`, `(\d{4});\s*(\d+)`).
   - Usar el año detectado en la publicación o el año actual como fallback neutro.
3. **Generalización de Clasificación de Secciones y Limpieza de Tablas:**
   - En `docx_table_parser.py`, sustituir la lista de palabras específicas (`'00421'`, `'diagnóstico'`, `'volumen'`) por una regla genérica basada en la estructura sintáctica (longitud de frase, presencia de saltos de línea deliberados o viñetas).
   - En `format_sections()`, utilizar patrones generales de terminología científica estándar (IMRyD: Introducción, Métodos/Metodología, Resultados, Discusión, Conclusiones, Casos/Casos Clínicos) sin depender de palabras clave de una sola disciplina.
4. **Detección Dinámica del Idioma Principal:**
   - Detectar el idioma del texto principal (`es`, `en`, `pt`, etc.) y asignarlo automáticamente a `<article xml:lang="...">` y a los elementos correspondientes.
5. **Generalización del Sub-artículo en Inglés (`<sub-article>`):**
   - Extraer la categoría traducida o usar la categoría correspondiente en lugar del valor fijo `"Research"`.

---

### Fase 2: Depuración de Scripts Ad-Hoc y Flujo de Procesamiento

1. **Retirar Dependencia de Scripts con Lógicas por Archivo:**
   - Los scripts `fix_all_sanus_expert_rules.py`, `update_all_xmls_header_metadata.py` y similares que usan `if "566" in filename:` no deben formar parte del pipeline de producción.
   - Toda la lógica válida de estructuración (tablas, figuras, citas cruzadas, normalización SciELO) debe quedar consolidada exclusivamente dentro del pipeline general de `main.py` y `docx_table_parser.py`.
2. **Generación Universal del Nombre de Archivo SciELO:**
   - Diseñar una función estándar que construya el nombre de salida a partir de los metadatos reales del artículo:
     `{issn}-{journal_id}-{volume}-{issue}-{elocation_id}.xml`
     sin depender de diccionarios manuales (`scielo_map` o `order_map`).

---

## 3. Plan de Verificación

1. **Prueba con Documentos de Distintas Revistas y Áreas:**
   - Probar la conversión de un documento de área médica/salud (ej. SANUS).
   - Probar la conversión de un documento de área jurídica/social (ej. Biolex).
   - Probar un documento neutro/genérico sin marcas de agua ni nombres conocidos.
2. **Validación SciELO SPS:**
   - Ejecutar la función de validación `validate_sps()` en cada salida generada para certificar que ningún XML pierde conformidad con la norma SPS 1.9 / JATS 1.1 al remover los valores hardcodeados.
3. **Verificación de Ausencia de Strings Específicos:**
   - Realizar búsquedas de patrones en el código (`grep`) para comprobar que no existan nombres de archivos (`.docx`, `566`, `573`, etc.) ni palabras clave exclusivas en los módulos de producción.
