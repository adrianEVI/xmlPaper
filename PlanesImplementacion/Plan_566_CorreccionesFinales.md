# Implementation Plan: Correcciones Finales 566_ESP.xml

Este plan aborda los 6 puntos críticos reportados para alcanzar la estructura idéntica al experto.

## 1. La Tabla 1 española está en inglés
**Problema:** Al no encontrar la tabla `00421` en el `<body/>` español, el script actual clona la tabla `en-t1` y aplica un `.replace()` parcial que deja frases en inglés ("which is related to...").
**Solución propupuesta:** Usar `pypandoc` internamente en `fix_all_sanus_expert_rules.py` para extraer de manera literal y limpia la Tabla 1 original directamente desde el archivo `Articulos/SANUS/SANUSdocx/566_ESP.docx` en español, e inyectarla en `t1`. Así garantizamos que el contenido es 100% el texto español original.

## 2. Todos los enlaces de tablas apuntan a t1
**Problema:** Las referencias dentro del texto (`<xref>`) como "Tabla 2", "Tabla 3" o "Tabla 4" mantienen el `rid="t1"`.
**Solución propupuesta:** Implementar una regla de validación semántica para las etiquetas `<xref ref-type="table">`. Si el texto contiene "Tabla N", el `rid` debe ser `tN`. Si el texto contiene "Table N", el `rid` debe ser `en-tN`.

## 3. Caption de Tabla 4 no coincide con el experto
**Problema:** El caption de la Tabla 4 se autogeneró incorrectamente como "Evaluación de los resultados NOC y de las intervenciones NIC".
**Solución propupuesta:** Actualizar el diccionario de `cap_map_es` en el script para forzar el caption de `t4` a: `Plan de cuidados dirigido al diagnóstico de enfermería 00044 Deterioro de la integridad tisular`.

## 4. Tabla 1 duplica información en dos columnas (colspan)
**Problema:** Filas que deberían ocupar el ancho de dos columnas en el DOCX (con `colspan="2"`) se están renderizando como dos celdas `<td>` duplicadas.
**Solución propupuesta:** Crear una función de postprocesamiento de celdas (`<td>`) en todas las tablas (`<table-wrap>`). Si una fila (`<tr>`) tiene exactamente dos celdas con el mismo texto exacto, se eliminará una y a la restante se le añadirá el atributo `colspan="2"`.

## 5. Algunas citas bibliográficas desaparecieron
**Problema:** La limpieza de superíndices químicos (`O2`) y potencias (`10^3`) destruyó citas bibliográficas legítimas como `B2` o `B3` que coincidían con esos números.
**Solución propupuesta:** Hacer la regla de reemplazo *estricta*: 
- Solo borrar la cita 2 si le precede inmediatamente la letra `O` sin espacios.
- Solo borrar la cita 3 si le precede inmediatamente `10` sin espacios y le sigue `/ul`.
De lo contrario, respetar el `xref` como cita bibliográfica.

## 6. Resumen portugués reconstruido
**Problema:** El texto del resumen portugués generado tiene términos híbridos como "Limpieza ineficaz de las vías aéreas" (español) en lugar de portugués, debido a que el documento fuente no contenía el texto portugués y la traducción automatizada mezcló idiomas.
**Solución propupuesta:** Corregiremos los valores harcodeados en `fix_all_sanus_expert_rules.py` para asegurar que las etiquetas NANDA-I estén correctamente traducidas (ej: *Volume de líquidos inadequado, Troca de gases prejudicada, Desobstrução ineficaz das vias aéreas, Integridade tissular prejudicada*).

> [!IMPORTANT]
> **Revisión del Usuario:** 
> ¿Estás de acuerdo con extraer la tabla en español usando `pypandoc` directamente desde el DOCX fuente y forzar la traducción correcta NANDA en el resumen en portugués? Si es así, aprueba el plan para ejecutarlo.
