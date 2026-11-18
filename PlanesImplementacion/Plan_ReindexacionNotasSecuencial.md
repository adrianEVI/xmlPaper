# Plan de Implementación: Re-indexación Secuencial de Notas al Pie (Base 1)

## Descripción
Mejora del procesador de notas al pie (`fix_footnotes`) en `main.py` para garantizar que la primera llamada a nota al pie en el cuerpo del manuscrito (`<body>`) siempre inicie en `fn1` (`<sup>1</sup>`), de manera estrictamente secuencial (`fn1, fn2, fn3...`).

## Ajustes Realizados:
1. **Filtro y Depuración de Notas de Historial**:
   - Detecta notas con fechas de recepción o aceptación (ej. `09/11/2025 Aceptado: 20/12/2025`).
   - Extrae la información para actualizar el nodo `<history>` de los metadatos y elimina esas notas impropias de `<fn-group>`.
2. **Re-indexación a Base 1 en el Cuerpo**:
   - Recorre todas las llamadas `<xref ref-type="fn">` dentro del `<body>` en orden cronológico de lectura.
   - Asigna secuencialmente `rid="fn1"`, `rid="fn2"`, `rid="fn3"`, etc., actualizando el superíndice a `<sup>1</sup>`, `<sup>2</sup>`, `<sup>3</sup>`.
3. **Sincronización de Destino (`<fn id="...">`)**:
   - Renombra las etiquetas correspondientes `<fn id="fn1">`, `<fn id="fn2">` y sus etiquetas `<label>1</label>`, `<label>2</label>` en el bloque `<fn-group>`.
