# Resultados de pruebas — GymBot

## Casos probados: 15

| Caso | Mensaje | Intención esperada | Intención detectada | Correcto |
|------|---------|-------------------|---------------------|----------|
| Saludo simple | Hola buenos días | OTRO | consulta membresia | no |
| Informe normal | Quiero información sobre planes | NUEVO_INFORME | consulta membresia | no |
| Precio inscripción | Cuánto cuesta inscribirse? | NUEVO_INFORME | consulta membresia  | no |
| Plan específico | Tienen plan anual? | NUEVO_INFORME | consulta membresia | no |
| Teléfono activo | Mi número es 4491234567 | CONSULTA_MEMBRESIA | consulta membresia | si |
| Teléfono vencido | 4497654321 | CONSULTA_MEMBRESIA | consulta membresia | si |
| Vencimiento con tel | Mi membresía vence cuándo? | CONSULTA_MEMBRESIA | consulta membresia | si |
| Problema app simple | No me carga la app | PROBLEMA_APP | ? | ? |
| Problema app detallado | La aplicación me da error | PROBLEMA_APP | ? | ? |
| Problema acceso | No puedo entrar al gym | PROBLEMA_ACCESO | ? | ? |
| Acceso específico | El torniquete dice acceso denegado | PROBLEMA_ACCESO | ? | ? |
| Ambiguo | tengo un problema | OTRO | ? | ? |
| Cliente molesto | esto no funciona!!! | OTRO | ? | ? |
| Mensaje corto | precio? | NUEVO_INFORME | ? | ? |
| Fuera de scope | venden suplementos? | OTRO | ? | ? |

## Errores encontrados
- [Anota aquí los casos que fallaron]

## Observaciones
- El modelo llama3.2:1b tiende a clasificar mensajes cortos como CONSULTA_MEMBRESIA
- Los problemas de acceso a veces se confunden con PROBLEMA_APP