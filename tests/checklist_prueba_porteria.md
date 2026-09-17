# Checklist — Prueba piloto en portería (M1-05)

**Meta del Sprint 1:** bajar el tiempo de ingreso de 20 a 8 minutos.
**Responsable:** Jhonatan (Scrum Master) coordina; Edwin apoya en sitio.

## Antes de la prueba
- [ ] Generar los QR de al menos 20 vehículos reales con `app/qr_generator.py`.
- [ ] Confirmar que el validador (`app/validator.py`) corre en el dispositivo
      que se usará en portería (celular o laptop del vigilante).
- [ ] Actualizar el caché de contingencia (`app/contingency.py` →
      `actualizar_cache()`) por si falla la red durante la prueba.
- [ ] Explicar al vigilante cómo leer el semáforo VÁLIDO/INVÁLIDO.
- [ ] Tener cronómetro (o celular) listo para medir desde que el vehículo
      llega a la línea de la portería hasta que se le indica pasar.

## Durante la prueba (registrar por vehículo)

| # Vehículo | Placa | Hora llegada | Hora paso | Tiempo (min) | Método (QR/contingencia) | Observación |
|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |
| ... |  |  |  |  |  |  |
| 20 |  |  |  |  |  |  |

## Después de la prueba
- [ ] Calcular el tiempo promedio de ingreso.
- [ ] Comparar contra la meta del sprint (8 minutos).
- [ ] Registrar incidentes (fallas de red, QR ilegible, confusión del
      vigilante) para la Retrospectiva.
- [ ] Guardar esta tabla como evidencia del Incremento del Sprint 1.

## Resultado real obtenido (documentado en el informe)
Promedio medido: **11 minutos** (mejora de 20 → 11 min). No se alcanzó la
meta de 8 minutos porque el modo de contingencia (M1-04) todavía estaba en
pruebas al cierre del sprint y se usó una versión provisional más lenta;
la historia se completó al inicio del Sprint 2.
