# Plan de Implementación: Corrección de Pérdida de Secciones y Metadatos en DOCX

Este plan aborda la resolución integral de la pérdida de contenido en el cuerpo del documento XML (como la Sección `I. INTRODUCCIÓN`, `II. DIAGNÓSTICO`, `III. FUNDAMENTOS`, `IV. ANÁLISIS`), el truncamiento de títulos largos y la correcta extracción de resúmenes y palabras clave hacia el cabezal `<front>`.

## Problemas Identificados y Causa Raíz

1. **Desaparición de Secciones (I. INTRODUCCIÓN a IV. ANÁLISIS)**:
   - **Causa Raíz A**: El módulo `restructure_body_to_sections` solo reconocía un párrafo como título de sección si contenía explícitamente una etiqueta `<bold>`. En manuscritos Word donde los títulos de sección (`I. INTRODUCCIÓN`, etc.) usan estilos de título de Word sin la etiqueta `<bold>` explícita en el XML de Pandoc, los párrafos no se detectaban como nueva sección.
   - **Causa Raíz B**: Al no detectarse como nueva sección, todos los párrafos de las Secciones I, II, III y IV se acumularon dentro de la sección anterior (`Abstract`).
   - **Causa Raíz C**: Posteriormente, la función `extract_structured_abstracts_from_body` localizó el nodo `<sec>` del Abstract para extraerlo y ejecutó `p.decompose()`, eliminando el nodo del Abstract junto con todos los párrafos de las Secciones I a IV tragados dentro de él.

2. **Truncamiento del Título del Artículo**:
   - En `extract_metadata_from_text`, el filtro determinista de títulos detenía la concatenación de líneas al encontrar palabras cortas no incluidas en la lista de conectores. Al terminar una línea con `"un"`, el algoritmo cortaba el título de forma prematura en *"Violencia estructural y respuesta penal ineficaz: Hacia un"*.

3. **Resumen y Palabras Clave "No disponible" en `<front>`**:
   - Cuando el Resumen en español es continuo y no contiene las 3 sub-secciones estructuradas (*Objetivo, Metodología, Resultados*), la función de extracción secundaria no lo asignaba a `metadata.abstract_es`, dejando en `<front>` el valor por defecto *"Resumen no disponible"*.

---

## Cambios Propuestos

### 1. Servidor Principal ([`main.py`](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py))

#### A. Ampliar la detección de Secciones en `restructure_body_to_sections`
- Extender el criterio de detección de títulos de sección para reconocer:
  1. Párrafos con negrita `<bold>` (criterio actual).
  2. Párrafos cuyo texto inicie con patrones de numeración de secciones: romanos (`I.`, `II.`, `III.`, `IV.`, etc.), arábigos (`1.`, `2.`, `1.1`), o palabras clave canónicas (`SUMARIO`, `RESUMEN`, `ABSTRACT`, `INTRODUCCIÓN`, `CONCLUSIONES`, `REFERENCIAS BIBLIOGRÁFICAS`, etc.), independientemente de si Pandoc incluyó o no la etiqueta `<bold>`.

#### B. Aisleamiento seguro en `extract_structured_abstracts_from_body`
- Prevenir la destrucción destructiva (`.decompose()`) de nodos `<sec>` contenedores.
- Extraer únicamente el texto o párrafo específico del Abstract sin eliminar párrafos subsecuentes del cuerpo del artículo.

#### C. Corrección del truncamiento de Títulos en `extract_metadata_from_text`
- Expandir la lista de conectores de continuación de título en `extract_metadata_from_text` para incluir: `"un"`, `"una"`, `"del"`, `"los"`, `"las"`, `"con"`, `"por"`, `"para"`, `"en"`, `"al"`, `"o"`, `"a"`, evitando cortes prematuros al final de línea.

#### D. Extracción de Resúmenes No Estructurados y Palabras Clave
- Asegurar que si el Resumen en español existe en el cuerpo (incluso si es un único párrafo no estructurado), se asigne correctamente a `metadata.abstract_es` para actualizar la cabecera `<front>`.

---

## Plan de Verificación

### Pruebas Automatizadas y de Scripts
1. Ejecutar la conversión del archivo problemático `441-XML_jats(1).xml` / DOCX de prueba y verificar:
   - Que la Sección `I. INTRODUCCIÓN` y todo su texto aparezcan completos en el XML generado.
   - Que el título en `<front>` aparezca completo sin truncar.
   - Que el `<abstract>` y `<kwd-group>` en `<front>` contengan los valores extraídos del manuscrito.

### Verificación Manual
- Validar la estructura del árbol XML generado asegurando que cumpla la DTD de SciELO SPS 1.9 mediante `verify_sps_xml_structure.py` si aplica.
