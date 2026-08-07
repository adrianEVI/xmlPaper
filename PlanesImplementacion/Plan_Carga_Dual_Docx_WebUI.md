# Plan de Implementación: Carga Dual de Documentos (Principal + Traducción Inglés) en la Web UI

Habilitar la opción de adjuntar de manera manual y simultánea dos archivos (`.docx` principal y `.docx` opcional en inglés) desde la interfaz web, procesándolos en el backend FastAPI para generar un único XML JATS estricto con la estructura SciELO SPS (`<sub-article article-type="translation" xml:lang="en">`).

## User Review Required

> [!IMPORTANT]
> - El segundo archivo (Traducción en Inglés `_ENG.docx`) será totalmente **opcional**. Si no se adjunta, la conversión operará como hasta ahora procesando solo el documento principal.
> - Se corregirá un detalle en la función `process_eng_docx_to_subarticle` en `main.py` para asegurar que devuelva explícitamente la etiqueta `<sub-article>`.

## Proposed Changes

### Backend FastAPI

#### [MODIFY] [main.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/main.py)

- **Corregir `process_eng_docx_to_subarticle`**:
  - Añadir `return sub_article` al final de la función para retornar la estructura construida.
- **Actualizar Endpoint `/convert`**:
  - Modificar la firma del endpoint a `async def convert_docx(file: UploadFile = File(...), eng_file: Optional[UploadFile] = File(None))`.
  - Guardar `eng_file` (si se proporciona) en el directorio temporal como `eng_input_path`.
  - Cuando se adjunte `eng_file`, ejecutar `process_eng_docx_to_subarticle(soup, eng_input_path, metadata)` para insertar el nodo `<sub-article>` e integrar títulos, resúmenes y palabras clave en inglés actualizados en la sección `<front>` principal.

---

### Frontend Web UI

#### [MODIFY] [index.html](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/static/index.html)

- **Añadir zona de carga para la traducción**:
  - Crear una segunda área de carga de diseño moderno/glassmorphism identificada como "Traducción al Inglés (Opcional - `.docx`)".
  - Permitir seleccionar o arrastrar el archivo `_ENG.docx`.
- **Actualizar lógica en JavaScript**:
  - En la función del formulario `uploadForm`, adjuntar `eng_file` a `FormData` si el usuario ha seleccionado una traducción.
  - Ajustar los mensajes de estado del progreso para indicar la carga y procesamiento de ambos documentos cuando corresponda.

---

## Verification Plan

### Manual Verification
1. **Prueba con 1 archivo único**:
   - Subir un solo archivo Word (`.docx`) a través de la web UI y verificar que se genera y descarga el XML de manera correcta.
2. **Prueba con 2 archivos (Principal + `_ENG.docx`)**:
   - Subir el archivo principal (ej. español) y el archivo de traducción en inglés en el nuevo campo secundario.
   - Ejecutar la conversión.
   - Inspeccionar el XML devuelto y verificar que contiene:
     - La sección `<front>` con títulos y resúmenes multilingües.
     - La sección `<sub-article article-type="translation" id="s1" xml:lang="en">` con el cuerpo estructurado del artículo en inglés.
