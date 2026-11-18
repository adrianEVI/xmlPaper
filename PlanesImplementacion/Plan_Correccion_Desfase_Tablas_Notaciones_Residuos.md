# Plan de Implementación: Re-alineación de Tablas por Objeto, Corrección de Notaciones Científicas/Químicas y Limpieza de Residuos

Se diseña la solución definitiva para resolver la asociación de contenidos de tablas por objeto, corregir falsas citas en notaciones ($10^3/\mu l$, $O_2$), eliminar párrafos duplicados y remover secciones residuales.

---

## User Review Required

> [!IMPORTANT]
> **Puntos Clave de Corrección:**
> 1. **Re-alineación Fiel de Tablas (Contenido + Caption por Objeto 1:1):**
>    - **Tabla 1 (`t1`):** Caption de 00421 + Tabla con contenido de 00421 (Volumen de líquidos).
>    - **Tabla 2 (`t2`):** Caption de 00030 + Tabla con contenido de 00030 (Intercambio gaseoso).
>    - **Tabla 3 (`t3`):** Caption de 00031 + Tabla con contenido de 00031 (Vías aéreas).
>    - **Tabla 4 (`t4`):** Caption de Evaluación NOC/NIC + Tabla completa con contenido de 00044 (Integridad tisular y NOC/NIC de 32 filas, **no vacía**).
> 2. **Eliminación Total de Párrafos Duplicados de Título:**
>    - Descomponer de `body` cualquier párrafo `<p>` residual con el título de la Tabla 1.
> 3. **Corrección de Notaciones Científicas y Químicas (Prevención de Falsos `bibr`):**
>    - `10^3/ul`: Transformar `10<xref ref-type="bibr" rid="B3"><sup>3</sup></xref>/ul` en `10<sup>3</sup>/µl`.
>    - `O2`: Transformar `O<xref ref-type="bibr" rid="B2"><sup>2</sup></xref>` en `O<sub>2</sub>`.
> 4. **Eliminación de la Sección Residual `Section` en el Sub-artículo:**
>    - Remover la sección extra `Section` al final de `<sub-article>`, dejando exactamente las 9 secciones editoriales.
> 5. **Normalización del Resumen Portugués Fiel:**
>    - Asegurar que los términos clínicos en portugués no contengan mezclas en español (p. ej., `Deterioração da troca gasosa` en lugar de `Deterioro do intercambio gaseoso`).

---

## Proposed Changes

### 1. Actualización en `fix_all_sanus_expert_rules.py` y `main.py`

#### [MODIFY] [fix_all_sanus_expert_rules.py](file:///c:/Users/avazq/OneDrive/Escritorio/AntiProjects/xmlPaper/fix_all_sanus_expert_rules.py)
- Reconstruir el mapeo de tablas `t1`, `t2`, `t3`, `t4` para 566 vinculando cada tabla física con su caption correspondiente y garantizando que `t4` no quede vacía.
- Eliminar párrafos duplicados del texto que contengan la etiqueta/título de la Tabla 1.
- Deshacer la conversión a `xref` en notaciones clínicas:
  - Cambiar `10<sup>3</sup>/ul` a etiqueta superíndice pura `10<sup>3</sup>/µl`.
  - Cambiar `O<sup>2</sup>` a subíndice químico `O<sub>2</sub>`.
- Eliminar cualquier sección `<sec>` con título `Section` en `<sub-article>`.
- Limpiar y normalizar los términos en portugués en `<trans-abstract xml:lang="pt">`.

---

## Verification Plan

### Automated Tests & Verification
1. **Verificación de Contenidos de Tablas:**
   - Comprobar que el primer `<td>` o `<tr>` de `t1` contenga 00421, `t2` contenga 00030, `t3` contenga 00031 y `t4` contenga 00044/NOC/NIC.
2. **Verificación de Notaciones:**
   - Comprobar que no exista `rid="B3"` en $10^3/\mu l$ ni `rid="B2"` en $O_2$.
3. **Verificación de Conteo de Secciones en Sub-artículo:**
   - Comprobar que en `<sub-article>` existan exactamente 9 secciones y ninguna llamada `Section`.
4. **Verificación SciELO SPS (0 Errores):**
   - Ejecutar `verify_sps_xml_structure.py` y validar la estructura.
