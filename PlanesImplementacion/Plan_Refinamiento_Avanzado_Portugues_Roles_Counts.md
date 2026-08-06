# Plan de Implementación: Ajustes Multilingües (Portugués), Roles de Autor y Conteo Compuesto

Se estructuran los cambios para incorporar los **metadatos en Portugués (`xml:lang="pt"`) en el `<front>`**, actualizar el contador total de tablas a `count="8"`, incluir los elementos `<role>` poblados con la titulación académica de cada autor y enriquecer las afiliaciones con `content-type="normalized"`.

---

## User Review Required

> [!IMPORTANT]
> **Puntos Principales de Acción:**
> 1. **Inclusión de Metadatos en Portugués en `<front>`:**
>    - Se agregarán los bloques `<trans-title-group xml:lang="pt">`, `<trans-abstract xml:lang="pt">` y `<kwd-group xml:lang="pt">` en la cabecera principal del XML.
> 2. **Roles Académicos Integrados (`<role>`):**
>    - Cada nodo `<contrib contrib-type="author">` conservará su correspondiente etiqueta `<role>` con el texto exacto de la titulación (ej. `<role>Maestra en Enfermería</role>`, `<role>Doctor en Educación</role>`, etc.).
> 3. **Conteo Total Compuesto de Tablas (`count="8"`):**
>    - El elemento `<table-count>` contabilizará el total compuesto de tablas del documento (4 del cuerpo principal en español + 4 del sub-artículo en inglés = `count="8"`).
> 4. **Enriquecimiento de Afiliaciones (`content-type="normalized"`):**
>    - `<institution content-type="original">` incluirá el grado académico al inicio de la firma institucional y se añadirá el atributo `content-type="normalized"` en la institución principal.
> 5. **Normalización de Estilo Editorial:**
>    - Ajuste de capitalización en `<journal-title>Sanus</journal-title>` e `<subject>Investigación</subject>`.

---

## Proposed Changes

### 1. Inyección de Metadatos en Portugués (`fix_all_sanus_expert_rules.py` y `main.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)
- **Construcción de nodos `<trans-title-group xml:lang="pt">`, `<trans-abstract xml:lang="pt">` y `<kwd-group xml:lang="pt">`:**
  - Extraer o asignar el título en portugués, el resumen estructurado en portugués y las palavras-chave.
  - Insertar estos nodos en el `<article-meta>` del `<front>` principal.

---

### 2. Estructuración de Roles de Autor y Afiliaciones Normalizadas (`fix_all_sanus_expert_rules.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- **Extracción e Inserción de `<role>`:**
  - Garantizar que los 6 autores posean el nodo `<role>` con su titulación correspondiente.
- **Formateo de `<institution>` en `<aff>`:**
  - Incluir el grado académico dentro de `<institution content-type="original">`.
  - Añadir `<institution content-type="normalized">` en la entrada de la institución.

---

### 3. Conteo Total Compuesto de Tablas (`table-count`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Sumar todas las tablas (`table-wrap`) del documento principal y del `<sub-article>`, asignando `<table-count count="8"/>` cuando existan 4 tablas en español y 4 en inglés.

---

### 4. Ajustes Editoriales Menores

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Aplicar Sentence Case en `<journal-title>` ("Sanus") y en `<subject>` ("Investigación").

---

## Verification Plan

### Automated Tests & Verification
1. **Verificación de Metadatos en Portugués:**
   - Comprobar la presencia de `xml:lang="pt"` en `<trans-title-group>`, `<trans-abstract>` y `<kwd-group>`.
2. **Verificación de `<role>` en Autores:**
   - Validar que los 6 nodos de autor contengan su respectivo `<role>Doctor/a...</role>`.
3. **Verificación de `<table-count>`:**
   - Confirmar `<table-count count="8"/>` en el nodo `<counts>`.
