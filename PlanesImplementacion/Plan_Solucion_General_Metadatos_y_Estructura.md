# Plan de Solución General: Metadatos Editoriales, Estructuras JATS y Limpieza Estricta

Este plan aborda de manera **general y automatizada** los 8 problemas críticos reportados sobre el pipeline de procesamiento XML JATS SciELO SPS.

---

## Problemas Identificados y Soluciones Propuestas

### 1. Números de Fascículo en Bibliografía Convertidos en `<xref ref-type="bibr">`
- **Problema:** En expresiones como `2023;2(82):1-13` o `29(21):1248-1251` dentro de la bibliografía, el detector de citas convierte el número de fascículo `(82)` o `(21)` en `<xref ref-type="bibr" rid="B82">`, generando referencias rotas o semánticamente incorrectas.
- **Solución:**
  - Excluir explícitamente los contenedores `<ref-list>`, `<ref>`, `<mixed-citation>`, `<element-citation>` y `<back>` en la función `auto_link_cross_references`.
  - Crear una rutina de limpieza post-procesamiento que remueva cualquier `<xref ref-type="bibr">` que haya quedado anidado dentro de `<ref-list>`, des-envolviéndolo para conservar únicamente su texto plano.

### 2. Elemento `<trans-abstract xml:lang="pt"/>` Vacío
- **Problema:** Se emite una etiqueta autoconclusiva `<trans-abstract xml:lang="pt"/>` cuando no existe un resumen en portugués, lo que es rechazado por validadores SPS.
- **Solución:**
  - Modificar la construcción de metadatos en `main.py` para no crear ni adjuntar la etiqueta `<trans-abstract xml:lang="pt">` si el texto del resumen en portugués está vacío o no fue extraído.
  - Añadir una regla de limpieza final que elimine (`decompose()`) cualquier nodo `<trans-abstract>` o `<abstract>` que no contenga elementos `<p>` ni `<sec>` con texto.

### 3. Sección "Inteligencia Artificial" Anidada Dentro de Financiamiento
- **Problema:** El párrafo y declaración de uso de Inteligencia Artificial quedan incluidos dentro de la sección `<sec sec-type="financial-disclosure">`, dejando el cuerpo con 8 secciones en lugar de 9 independientes.
- **Solución:**
  - Modificar `restructure_body_to_sections` y `fix_all_sanus_expert_rules.py` para detectar encabezados o párrafos con la frase "Inteligencia artificial" / "Artificial intelligence" / "Uso de inteligencia artificial".
  - Extraerlos hacia su propia sección independiente `<sec id="secX">` con su `<title>Inteligencia artificial</title>` colocada inmediatamente después de Financiamiento, garantizando paridad entre el cuerpo principal y el `sub-article` en inglés.

### 4. Tablas Anidadas Dentro de Elementos `<p>` (`<p><table-wrap>...</table-wrap></p>`)
- **Problema:** `<table-wrap>` es un elemento de bloque JATS y no puede ser hijo directo de `<p>`, violando el DTD.
- **Solución:**
  - En `format_tables` y en el paso de sanitización final, verificar si algún `<table-wrap>` tiene como padre directo a un nodo `<p>`.
  - Des-envolver la tabla moviéndola antes o después del `<p>` padre, y eliminar el `<p>` si queda vacío tras la extracción.

### 5. Fuentes de Tablas Duplicadas e Inconsistentes
- **Problema:** `<table-wrap-foot>` presenta duplicaciones como `"Fuente: Elaboración propia Fuente: Elaboración propia"` o la presencia simultánea de `<attrib>` y `<fn fn-type="other">`.
- **Solución:**
  - Normalizar todos los `<table-wrap-foot>` para que utilicen una única convención SciELO SPS: `<fn fn-type="other" id="TFNx"><p>Fuente: ...</p></fn>`.
  - Aplicar deduplicación por expresión regular (`re.sub`) sobre el texto de las notas de pie de tabla para eliminar frases repetidas exactamente.

### 6. Metadatos Editoriales Incorrectos (`<article-id>`, DOI duplicado, `<volume>`)
- **Problema:** 
  - `<article-id pub-id-type="doi">` incluye la URL completa `https://doi.org/10.36789/...` en lugar de solo la cadena DOI `10.36789/...`.
  - En la cita "Cómo citar" se genera `https://doi.org/https://doi.org/...` por duplicación de prefijo.
  - Aparece `<article-id pub-id-type="other">00000</article-id>` dummy y `<volume>21</volume>` (confundiendo el número de fascículo/edición con el volumen).
- **Solución:**
  - Limpiar el prefijo `https://doi.org/` de todos los nodos `<article-id pub-id-type="doi">`.
  - Prevenir la duplicación de prefijo `https://doi.org/` en la función de formateo de citas.
  - Eliminar o reemplazar los identificadores dummy `00000` y corregir la asignación de `<volume>` a `10`.

### 7. Etiquetado Circular en `<label>` (`<label><xref rid="en-t3">Table 3</xref></label>`)
- **Problema:** La etiqueta interna `<label>` de una tabla contiene un `<xref>` apuntando a la propia tabla.
- **Solución:**
  - Excluir nodos `<label>` y `<caption/title>` de la transformación de referencias cruzadas.
  - Añadir una regla de limpieza que des-envuelva (`unwrap()`) cualquier nodo `<xref>` encontrado dentro de un `<label>`, dejando solo el texto plano (ej. `<label>Table 3</label>`).

### 8. Filas Vacías en Tablas (`<tr><td/><td/></tr>`)
- **Problema:** Tablas con filas sobrantes sin contenido textual en sus celdas.
- **Solución:**
  - En `format_tables` y `build_jats_table_from_docx`, iterar sobre todas las filas `<tr>` y eliminar (`decompose()`) aquellas donde la suma del texto de sus celdas `<td>`/`<th>` sea totalmente vacía.

---

## Proposed Changes

### Core Engine & Pipeline

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **`auto_link_cross_references(soup)`**: Agregar restricción estricta para omitir elementos dentro de `<back>`, `<ref-list>`, `<ref>`, `<mixed-citation>`, `<element-citation>`, `<label>` y `<caption>`.
- **`build_scielo_front` / `clean_body_duplicate_metadata`**: Asegurar que los nodos `<article-id pub-id-type="doi">` contengan únicamente la cadena DOI sin prefijo HTTP. Eliminar generación de `<trans-abstract>` si no hay contenido en portugués.
- **`format_tables(soup)`**: 
  - Des-envolver `<table-wrap>` de dentro de `<p>`.
  - Eliminar `<tr>` vacíos sin texto en sus celdas.
  - Remover `<xref>` anidados dentro de `<label>`.
  - Consolidar `<table-wrap-foot>` a un único `<fn fn-type="other">` deduplicado.

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Reforzar la extracción de la sección de Inteligencia Artificial para colocarla como `<sec id="secX">` independiente después de Financiamiento en español e inglés.
- Limpiar `<trans-abstract xml:lang="pt"/>` vacíos.
- Normalizar metadatos editoriales (DOI sin URL prefix, `<volume>10</volume>`, remover dummy `00000`).

#### [MODIFY] [apply_10_out_of_10_expert_fixes.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/apply_10_out_of_10_expert_fixes.py)
- Agregar un paso de verificación/limpieza estricto para asegurar que todos los XMLs procesados cumplan al 100% con los 8 puntos.

---

## Verification Plan

### Automated Tests
1. Ejecutar el pipeline completo de procesamiento para SANUS:
   - `python process_sanus_batch.py`
   - `python clean_sanus_bodies.py`
   - `python fix_how_to_cite_and_subarticle.py`
   - `python fix_all_sanus_expert_rules.py`
   - `python apply_10_out_of_10_expert_fixes.py`

2. Ejecutar script de prueba para validar automáticamente los 8 puntos en los 18 archivos XMLs:
   - Verificar que no exista ningún `<xref ref-type="bibr">` dentro de `<ref-list>`.
   - Verificar que no exista `<trans-abstract>` vacío.
   - Verificar que "Inteligencia artificial" sea una `<sec>` independiente.
   - Verificar que ningún `<table-wrap>` sea hijo de `<p>`.
   - Verificar que los pies de tabla no tengan texto duplicado.
   - Verificar que el DOI en `<article-id>` no contenga `https://doi.org/`.
   - Verificar que no existan URLs duplicadas `https://doi.org/https://doi.org/`.
   - Verificar que `<label>` de tablas no contenga `<xref>`.
   - Verificar que no existan `<tr>` vacíos en tablas.

### Manual Verification
- Inspeccionar visualmente la estructura generada en `566_ESP.xml` y `573_ESP.xml`.
