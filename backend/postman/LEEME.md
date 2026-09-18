# Batería de Postman

Dos archivos para importar en Postman:

| Archivo | Qué es |
|---|---|
| `AutoPrime.postman_collection.json` | 68 peticiones en 13 carpetas, con 62 comprobaciones |
| `AutoPrime.postman_environment.json` | dos entornos: local y el despliegue |

## Cómo correrla

1. **Import** en Postman → arrastra los dos archivos.
2. Elige el entorno arriba a la derecha (`AutoPrime - local`).
3. **Run collection**, en el orden en que vienen las carpetas.

Por consola, sin abrir Postman:

```bash
npx newman run backend/postman/AutoPrime.postman_collection.json --env-var baseUrl=http://127.0.0.1:8000
```

## Cómo está armada

**Se genera del OpenAPI de la propia API**, con `herramientas/generar_postman.py`.
Escribirla a mano sería mantener dos listas de endpoints, y a la segunda semana
una de las dos estaría desactualizada. Al regenerarla, cualquier endpoint nuevo
aparece solo.

Lo que va a mano son las comprobaciones, porque eso es lo que un esquema no
sabe: que el login guarde el token, que el precio de una venta sea el del
catálogo y no el que mandó el cliente, o que facturar dos veces la misma venta
responda 409.

**El orden de las carpetas es deliberado, no alfabético.** La batería se corre
en secuencia y cada carpeta deja preparado lo que necesita la siguiente: sin
iniciar sesión no hay token, sin catálogo no hay vehículo que vender, sin venta
no hay factura que emitir. En orden alfabético, «Facturas» corría antes que
«Ventas» y se saltaba entera.

**Los borrados están todos al final**, en «Limpieza». Antes cada carpeta
recogía lo suyo, y «Ventas» terminaba borrando la venta que «Facturas»
necesitaba.

## Dos cosas que hay que saber antes de correrla

**Toca datos de verdad.** Crea una venta, una factura, una PQR, una cita y una
cuenta de prueba. La carpeta de limpieza borra casi todo, pero la venta se
queda si se le emitió factura: borrarla dejaría un hueco en el consecutivo y la
API lo impide a propósito. Contra el despliegue, conviene quitarla a mano de
vez en cuando.

**Solo toca lo que ella misma crea.** Esto no era así al principio y costó caro:
la primera versión generaba `DELETE /api/usuarios/{id}` con el id por defecto en
`1`, y al correrla entera **borró el usuario administrador**. La petición era
correcta; el objetivo era real.

Ahora los ids de lo que la colección no crea arrancan vacíos, y un guion previo
salta cualquier petición cuyo objetivo siga sin rellenarse:

```javascript
const pendiente = (url.match(/{{(\w+)}}/g) || [])
    .map(v => v.slice(2, -2))
    .find(v => !pm.collectionVariables.get(v) && v !== 'baseUrl');
if (pendiente) pm.execution.skipRequest();
```

## Qué comprueba

Además del camino feliz, la carpeta **«Casos que deben fallar»** cubre lo que
*no* debe poder hacerse. Una batería que solo prueba lo que funciona no detecta
que se cayó una comprobación de permisos: el endpoint sigue respondiendo 200,
solo que a quien no debía.

- Sin token → 401, y con la cabecera `WWW-Authenticate` que exige la norma.
- Un cuerpo inválido → 422 diciendo **qué campo**, no solo que algo falló.
- Vender dos veces el mismo vehículo → 409 `vehiculo_no_disponible`.
- Facturar dos veces la misma venta → 409 `venta_ya_facturada`.
- Borrar una venta facturada → 409 `venta_con_factura`.
- Pedir más filas de la cuenta → 422.

## Relación con las otras pruebas

Son tres capas y ninguna sustituye a las otras:

| Dónde | Qué cubre |
|---|---|
| `tests/` (pytest, 78 pruebas) | la lógica, contra SQLite en memoria: rápido y sin dejar rastro |
| `pruebas_api.py` (81 pruebas) | la API contra MySQL de verdad, con ENUM y claves ajenas reales |
| esta colección (62 comprobaciones) | lo mismo desde fuera, con la herramienta que usa el instructor |
