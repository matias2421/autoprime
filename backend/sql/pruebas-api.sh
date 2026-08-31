#!/usr/bin/env bash
# =============================================================================
#  Pruebas de los endpoints de la API AutoPrime
#  Equivalente a la coleccion de Postman (requerimiento 18 del tercer avance).
#
#  Uso:  bash backend/sql/pruebas-api.sh
# =============================================================================
API="http://localhost:3000/api"
ok=0; fallo=0

# probar <descripcion> <codigo-esperado> <metodo> <ruta> [json] [token]
probar() {
  local desc="$1" esperado="$2" metodo="$3" ruta="$4" cuerpo="$5" token="$6"
  local args=(-s -o .resp.json -w "%{http_code}" -X "$metodo" "${API}${ruta}")

  [ -n "$cuerpo" ] && args+=(-H "Content-Type: application/json" -d "$cuerpo")
  [ -n "$token" ]  && args+=(-H "Authorization: Bearer ${token}")

  local codigo
  codigo=$(curl "${args[@]}")

  if [ "$codigo" = "$esperado" ]; then
    printf "  OK   %-3s  %-6s %-38s %s\n" "$codigo" "$metodo" "$ruta" "$desc"
    ok=$((ok+1))
  else
    printf "  FALLA esperaba %s obtuvo %s  %s %s  (%s)\n" "$esperado" "$codigo" "$metodo" "$ruta" "$desc"
    head -c 200 .resp.json; echo
    fallo=$((fallo+1))
  fi
}

token() { node -e "process.stdout.write(JSON.parse(require('fs').readFileSync('.resp.json','utf8')).token||'')"; }
campo() { node -e "process.stdout.write(String(JSON.parse(require('fs').readFileSync('.resp.json','utf8'))$1??''))"; }

echo "============================================================"
echo " AUTENTICACION"
echo "============================================================"

SUFIJO=$(date +%s)
NUEVO="{\"nombre\":\"Laura\",\"apellido\":\"Restrepo\",\"tipoDocumento\":\"CC\",\"numeroDocumento\":\"10${SUFIJO:2:8}\",\"direccion\":\"Carrera 7 22-14\",\"telefono\":\"3205551188\",\"correo\":\"laura${SUFIJO}@correo.com\",\"password\":\"Furia2026#\",\"confirmarPassword\":\"Furia2026#\"}"

probar "registro de cliente"            201 POST /auth/registro "$NUEVO"
TOKEN_NUEVO=$(token)
probar "correo duplicado -> 409"        409 POST /auth/registro "$NUEVO"
probar "datos invalidos -> 400"         400 POST /auth/registro '{"nombre":"A","correo":"malo"}'

probar "login administrador"            200 POST /auth/login '{"correo":"admin@autoprime.com.co","password":"Admin2026!"}'
ADMIN=$(token)
probar "login empleado"                 200 POST /auth/login '{"correo":"empleado@autoprime.com.co","password":"Empleado2026!"}'
EMPLEADO=$(token)
probar "login cliente"                  200 POST /auth/login '{"correo":"cliente@autoprime.com.co","password":"Cliente2026!"}'
CLIENTE=$(token)
probar "contrasena erronea -> 401"      401 POST /auth/login '{"correo":"admin@autoprime.com.co","password":"NoEsLaClave1!"}'
probar "perfil con token"               200 GET  /auth/perfil "" "$ADMIN"
probar "perfil sin token -> 401"        401 GET  /auth/perfil
probar "token invalido -> 401"          401 GET  /auth/perfil "" "abc.def.ghi"

echo
echo "============================================================"
echo " USUARIOS (CRUD protegido por rol)"
echo "============================================================"

probar "listar como admin"              200 GET  /usuarios "" "$ADMIN"
probar "listar como empleado"           200 GET  /usuarios "" "$EMPLEADO"
probar "cliente NO puede listar -> 403" 403 GET  /usuarios "" "$CLIENTE"
probar "sin token -> 401"               401 GET  /usuarios

probar "crear usuario (admin)"          201 POST /usuarios "{\"nombre\":\"Pedro\",\"apellido\":\"Gomez\",\"tipoDocumento\":\"CC\",\"numeroDocumento\":\"20${SUFIJO:2:8}\",\"direccion\":\"Calle 10 20-30\",\"telefono\":\"3109998877\",\"correo\":\"pedro${SUFIJO}@correo.com\",\"password\":\"Pedro2026#\",\"rol\":\"empleado\"}" "$ADMIN"
NUEVO_ID=$(campo ".usuario.id")

probar "obtener por id"                 200 GET  "/usuarios/${NUEVO_ID}" "" "$ADMIN"
probar "actualizar (PUT)"               200 PUT  "/usuarios/${NUEVO_ID}" '{"nombre":"Pedro Andres","telefono":"3112223344"}' "$ADMIN"
probar "actualizar invalido -> 400"     400 PUT  "/usuarios/${NUEVO_ID}" '{"telefono":"123"}' "$ADMIN"
probar "cambiar estado (PATCH)"         200 PATCH "/usuarios/${NUEVO_ID}/estado" '{"estado":"inactivo"}' "$ADMIN"
probar "estado invalido -> 400"         400 PATCH "/usuarios/${NUEVO_ID}/estado" '{"estado":"dormido"}' "$ADMIN"
probar "empleado NO edita -> 403"       403 PUT  "/usuarios/${NUEVO_ID}" '{"nombre":"Otro"}' "$EMPLEADO"
probar "usuario inexistente -> 404"     404 GET  /usuarios/999999 "" "$ADMIN"
probar "eliminar (DELETE)"              200 DELETE "/usuarios/${NUEVO_ID}" "" "$ADMIN"

echo
echo "============================================================"
echo " PRODUCTOS"
echo "============================================================"

probar "listar (publico)"               200 GET  /productos
probar "filtrar por familia"            200 GET  "/productos?familia=edicion"
probar "obtener por slug"               200 GET  /productos/pugnator-tricolore
probar "slug inexistente -> 404"        404 GET  /productos/no-existe

probar "crear (admin)"                  201 POST /productos "{\"slug\":\"prueba-${SUFIJO}\",\"marca\":\"Prueba\",\"modelo\":\"Test\",\"familia\":\"gama\",\"base\":\"Prueba Base\",\"lema\":\"Solo una prueba\",\"descripcion\":\"Vehiculo creado por el script de pruebas.\",\"imagen\":\"mansory-pugnator-perfil.webp\",\"anio\":2025,\"kilometraje\":0,\"precio\":100000000,\"motor\":\"V6\",\"potencia\":\"300 hp\",\"aceleracion\":\"5,0 s\",\"velocidad\":\"250 km/h\",\"transmision\":\"Automatica\",\"traccion\":\"Trasera\"}" "$ADMIN"
PROD_ID=$(campo ".producto.id")

probar "actualizar (PUT)"               200 PUT  "/productos/${PROD_ID}" '{"precio":95000000}' "$ADMIN"
probar "cliente NO crea -> 403"         403 POST /productos '{"slug":"x"}' "$CLIENTE"
probar "empleado NO elimina -> 403"     403 DELETE "/productos/${PROD_ID}" "" "$EMPLEADO"
probar "eliminar (admin)"               200 DELETE "/productos/${PROD_ID}" "" "$ADMIN"

echo
echo "============================================================"
echo " SERVICIOS"
echo "============================================================"

probar "listar (publico)"               200 GET  /servicios
probar "obtener por id"                 200 GET  /servicios/1
probar "crear (empleado)"               201 POST /servicios '{"nombre":"Lavado premium","descripcion":"Lavado y detallado completo.","duracionMin":90,"precio":120000}' "$EMPLEADO"
SERV_ID=$(campo ".servicio.id")
probar "actualizar"                     200 PUT  "/servicios/${SERV_ID}" '{"precio":150000}' "$ADMIN"
probar "eliminar (admin)"               200 DELETE "/servicios/${SERV_ID}" "" "$ADMIN"

echo
echo "============================================================"
echo " CITAS (agendamiento)"
echo "============================================================"

FECHA=$(node -e "const d=new Date();d.setDate(d.getDate()+7);while(d.getDay()===0)d.setDate(d.getDate()+1);process.stdout.write(d.toISOString().slice(0,10))")
echo "  (fecha de prueba: $FECHA)"

probar "disponibilidad (publico)"       200 GET  "/citas/disponibilidad?fecha=${FECHA}"
probar "fecha mal formada -> 400"       400 GET  "/citas/disponibilidad?fecha=31-12-2026"

probar "agendar como cliente"           201 POST /citas "{\"fecha\":\"${FECHA}\",\"hora\":\"10:00\",\"servicioId\":1,\"productoId\":1,\"notas\":\"Prueba automatica\"}" "$CLIENTE"
CITA_ID=$(campo ".cita.id")
probar "misma franja -> 409"            409 POST /citas "{\"fecha\":\"${FECHA}\",\"hora\":\"10:00\",\"servicioId\":1,\"productoId\":1}" "$CLIENTE"
probar "fecha pasada -> 400"            400 POST /citas '{"fecha":"2020-01-15","hora":"10:00","servicioId":1}' "$CLIENTE"
probar "hora fuera de horario -> 400"   400 POST /citas "{\"fecha\":\"${FECHA}\",\"hora\":\"23:00\",\"servicioId\":1}" "$CLIENTE"
probar "sin token -> 401"               401 POST /citas "{\"fecha\":\"${FECHA}\",\"hora\":\"11:00\",\"servicioId\":1}"

probar "cliente ve sus citas"           200 GET  /citas "" "$CLIENTE"
probar "admin ve todas"                 200 GET  /citas "" "$ADMIN"
probar "resumen"                        200 GET  /citas/resumen "" "$ADMIN"
probar "empleado confirma"              200 PATCH "/citas/${CITA_ID}/estado" '{"estado":"confirmada"}' "$EMPLEADO"
probar "cliente cancela la suya"        200 PATCH "/citas/${CITA_ID}/estado" '{"estado":"cancelada"}' "$CLIENTE"
probar "cliente NO confirma -> 403"     403 PATCH "/citas/${CITA_ID}/estado" '{"estado":"confirmada"}' "$CLIENTE"
probar "eliminar (admin)"               200 DELETE "/citas/${CITA_ID}" "" "$ADMIN"

echo
echo "============================================================"
printf " RESULTADO:  %d pruebas OK, %d fallidas\n" "$ok" "$fallo"
echo "============================================================"
[ "$fallo" -eq 0 ] || exit 1
