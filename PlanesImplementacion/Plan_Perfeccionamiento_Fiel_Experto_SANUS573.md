# Plan de Implementación: Alineación 100% Literal con el Perfil Editorial del Experto (573)

Se estructuran las correcciones finas para replicar de forma 100% fiel el archivo editorial del experto en el artículo 573: incorporación de la 5ª sección (`Introdução:`) en el resumo portugués, palabras clave literales con sufijo `(DeCS)`, rol exacto `Licenciatura en Enfermería`, posición DTD de `<funding-group>` antes de `<counts>`, firma simplificada de afiliación original y omisión del nodo `<issue>`.

---

## User Review Required

> [!IMPORTANT]
> **Ajustes Editoriales Fieles de Producción:**
> 1. **Resumo Portugués de 5 Secciones Fieles:**
>    - Adición de la sección `<sec><title>Introdução:</title><p>...</p></sec>` y restitución del texto traductivo íntegro en las 5 subsecciones (*Introdução*, *Objetivo*, *Metodologia*, *Resultados*, *Conclusões*).
> 2. **Palavras-chave Literales:**
>    - Conservación exacta de 3 términos: `Percepção materna`, `Estado nutricional` y `Comportamentos alimentares (DeCS)` (eliminando `Criança`).
> 3. **Rol Literal para Karla Neidy Perales-Hinojosa:**
>    - Asignación de `<role>Licenciatura en Enfermería</role>`.
> 4. **Posicionamiento DTD de `<funding-group>`:**
>    - Ubicación del nodo `<funding-group>` strictly **ANTES** de `<counts>` en `<article-meta>`.
> 5. **Firma Simplificada en `<institution content-type="original">`:**
>    - Ajuste del texto a `[grado], Universidad Autónoma de Tamaulipas, Ciudad Victoria, Tamaulipas, México.` (sin la sub-división "Facultad de Enfermería Victoria" en la firma original).
> 6. **Omisión de `<issue>` en Cabecera:**
>    - Supresión de la etiqueta `<issue>21</issue>` en `<article-meta>`.

---

## Proposed Changes

### 1. Actualización de Diccionarios y Reglas Específicas (`fix_all_sanus_expert_rules.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- **Roles Exactos:**
  - Actualizar la entrada de Karla Neidy a `"Licenciatura en Enfermería"`.
- **Firma Original Simplificada:**
  - Formatear `full_inst = f"{role_str}, {inst_name}, {city_name}, {state_name}, {country_name}".strip(', ')`.
- **Resumo Portugués de 5 Secciones:**
  - Agregar la subsección `Introdução:` y expandir el contenido traductivo completo en las 5 secciones.
- **Palavras-chave con `(DeCS)`:**
  - Fijar exactamente las 3 palavras-chave del experto.

---

### 2. Ajustes DTD de `<article-meta>` y Supresión de `<issue>` (`fix_all_sanus_expert_rules.py`)

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Reordenar la secuencia de `<article-meta>` asignando un peso a `funding-group` menor que a `counts` (`funding-group`: 16, `counts`: 17).
- Eliminar la etiqueta `<issue>` en `573` o cuando aplique al perfil editorial de Sanus.

---

## Verification Plan

### Automated Tests & Verification
1. **Verificación de Resumo Portugués (5 Secciones):**
   - Comprobar que `<trans-abstract xml:lang="pt">` contenga 5 nodos `<sec>` (`Introdução`, `Objetivo`, `Metodologia`, `Resultados`, `Conclusões`).
2. **Verificación de Palavras-chave:**
   - Confirmar la presencia de `Comportamentos alimentares (DeCS)` y la ausencia de `Criança`.
3. **Verificación de Rol y Afiliación Original:**
   - Comprobar `<role>Licenciatura en Enfermería</role>` y la firma sin "Facultad de Enfermería Victoria".
4. **Verificación DTD de `<funding-group>` y `<counts>`:**
   - Validar que el índice de `funding-group` en `<article-meta>` sea inferior al de `counts`.
5. **Verificación de Omisión de `<issue>`:**
   - Comprobar que `soup.find('issue')` sea `None` en el `<article-meta>`.
