# -*- coding: utf-8 -*-
"""Llena la base con movimiento de ejemplo, para poder enseñar el sistema.

    venv\\Scripts\\python sembrar_demo.py
    venv\\Scripts\\python sembrar_demo.py --limpiar

`preparar_base.py` deja lo mínimo para que la aplicación funcione: el
catálogo, los roles y tres cuentas. Con eso el sistema anda, pero los
tableros salen a cero y las tablas vacías, y una pantalla en blanco no
demuestra nada. Esto añade encima lo que hace falta para verlo funcionar:
clientes, ventas cobradas y por cobrar, facturas, citas, PQR y conversaciones.

TRES DECISIONES QUE CONVIENE LEER
---------------------------------

**Las fechas se reparten en dos meses**, no se apilan en hoy. Todo el
movimiento con la fecha de hoy deja la gráfica de ingresos con un único pico
vertical, que no enseña nada de lo que la gráfica existe para enseñar. Con el
movimiento repartido se ve una serie, que es el punto.

**Un vehículo puede aparecer en varias ventas del histórico.** La columna
`productos.estado` describe cómo está el catálogo AHORA; las ventas describen
lo que pasó. Que el Phantom se vendiera hace cuarenta días no obliga a que hoy
siga marcado como vendido: el atelier repone. Por eso las líneas de venta
guardan copia de la descripción y del precio —que es justo para lo que se
diseñaron— y el estado del catálogo se fija aparte, al final.

**Los importes salen del catálogo y las cuentas se hacen igual que en la
API.** Se importan `TASA_IVA` y el redondeo de `app.crud.ventas` en lugar de
copiarlos. Si mañana cambia el IVA, estos datos cambian con él; escritos a
mano, se quedarían diciendo otra cosa y nadie lo notaría hasta que alguien
sumara una columna.

La semilla del azar es fija, así que dos ejecuciones producen los mismos
datos. Es lo que permite repetir una captura de pantalla y que salga igual.
"""

import argparse
import random
import sys
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.configuracion import configuracion
from app.core.tiempo import ahora, hoy
from app.crud.ventas import TASA_IVA, redondear_dinero
from app.models.autoprime import (
    Cita,
    Conversacion,
    DetalleFactura,
    DetalleVenta,
    Factura,
    Mensaje,
    Pqr,
    Producto,
    Rol,
    Servicio,
    Usuario,
    Venta,
)

# Con la semilla fija, la misma corrida produce los mismos datos.
random.seed(2026)

DIAS_ATRAS = 60

# Marca de los clientes que crea este script. Sirve para poder quitarlos sin
# tocar las tres cuentas de `preparar_base.py`, que son las que se usan para
# entrar y no deben desaparecer.
DOMINIO_DEMO = "@demo.autoprime.com.co"

CLIENTES = [
    ("Valentina", "Restrepo Gil", "1017445566", "Calle 10 # 43-21, El Poblado", "3011234567"),
    ("Santiago", "Ocampo Vélez", "1035778899", "Carrera 70 # 44-18, Laureles", "3159876543"),
    ("Mariana", "Cardona Ruiz", "1128334455", "Av. El Poblado # 9-55", "3204567890"),
    ("Sebastián", "Henao Mejía", "71234567", "Calle 33 # 76-40, Bolivariana", "3012345678"),
    ("Juliana", "Betancur Soto", "1094556677", "Carrera 43A # 1-50", "3116667788"),
    ("Tomás", "Arango Posada", "8901234", "Calle 16 Sur # 48-30", "3145558899"),
    ("Camila", "Zuluaga Pérez", "1152998877", "Carrera 25 # 5-12, Provenza", "3183334455"),
    ("Andrés Felipe", "Muñoz Ríos", "98765432", "Calle 7 Sur # 42-70", "3007778899"),
]

# Vehículos que se venden a menudo y vehículos que casi no. Un atelier mueve
# más los de gama que las piezas de colección de dieciséis mil millones, y una
# gráfica donde todas las barras miden lo mismo no dice nada.
PESOS_VEHICULOS = {
    7: 6,    # Elongation EVO   1.200 M
    9: 5,    # Bentley GT       1.800 M
    10: 4,   # P9LM EVO 900     2.000 M
    2: 3,    # Phantom VIII     3.200 M
    3: 3,    # SF90 Soft Kit    3.600 M
    6: 2,    # Carbonado EVO    4.800 M
    8: 1,    # Monza SP2       10.000 M
    4: 1,    # Vivere          16.000 M
}

# Los dos de arriba no entran en una venta ya cobrada.
#
# No es un capricho estetico: una venta de dieciseis mil millones cobrada el
# martes deja la grafica de ingresos con un pico que aplasta los otros
# veintinueve dias contra la linea de base, y entonces la grafica no enseña
# el movimiento, que es para lo que esta.
#
# Ademas es lo que pasa de verdad: una compra de ese tamaño no se liquida en
# el acto. Queda por cobrar, que es justo el estado que la tarjeta «Por
# cobrar» existe para enseñar.
SOLO_POR_COBRAR = {4, 8}

ASUNTOS_PQR = [
    ("reclamo", "El vehículo llegó con un rayón en la puerta",
     "Recibí el vehículo el martes y tiene un rayón de unos diez centímetros "
     "en la puerta del copiloto que no aparece en las fotos de la entrega.",
     "Revisamos el registro fotográfico de la entrega y programamos el retoque "
     "sin costo en nuestro taller. Lo contactamos para acordar la fecha.", "cerrada"),
    ("queja", "Demora en la respuesta de la cotización",
     "Solicité una cotización formal del Bentley GT hace ocho días y todavía "
     "no he recibido respuesta por correo.",
     "Tiene razón y lo lamentamos. Su cotización salió hoy y ajustamos el "
     "proceso para que ninguna pase de 48 horas.", "respondida"),
    ("peticion", "Solicito el certificado de peritaje en PDF",
     "Necesito el certificado del peritaje de 120 puntos que le hicieron a mi "
     "vehículo el mes pasado, para el trámite del seguro.",
     "Adjuntamos el certificado al correo registrado en su cuenta. Si necesita "
     "copia física, puede recogerla en el atelier.", "cerrada"),
    ("sugerencia", "Ampliar el horario los sábados",
     "Sería útil que el taller atendiera hasta más tarde los sábados; entre "
     "semana es difícil sacar tiempo para una prueba de manejo.",
     "Gracias por escribirnos. Lo estamos evaluando para el próximo trimestre.",
     "respondida"),
    ("reclamo", "La factura tiene un dato equivocado",
     "En la factura aparece mi documento con un dígito de más y la necesito "
     "corregida para presentarla en la notaría.",
     None, "en_proceso"),
    ("peticion", "Quiero agendar la revisión de los 5.000 km",
     "Compré el vehículo hace dos meses y quiero programar el mantenimiento "
     "que viene incluido. ¿Qué disponibilidad hay?",
     None, "pendiente"),
    ("queja", "No me llegó el correo de recuperación",
     "Pedí recuperar la contraseña dos veces y el correo no llega, ni siquiera "
     "a la carpeta de no deseados.",
     None, "pendiente"),
    ("sugerencia", "Agregar comparador de modelos en la web",
     "Estaría bien poder comparar dos vehículos lado a lado con sus fichas "
     "técnicas, sin tener que abrir dos pestañas.",
     None, "pendiente"),
    ("reclamo", "Cobro duplicado del peritaje",
     "Me aparecen dos cobros del peritaje de 120 puntos con la misma fecha y "
     "solo hice uno.",
     "Verificamos y efectivamente hubo un cobro duplicado. La devolución ya "
     "está en proceso y se refleja en tres días hábiles.", "cerrada"),
    ("peticion", "Información sobre financiación",
     "Quisiera saber qué opciones de financiación manejan para el Elongation "
     "EVO y si trabajan con retoma.",
     None, "en_proceso"),
]

CONVERSACIONES = [
    ("Consulta de catálogo", [
        ("usuario", "Hola, ¿qué vehículos tienen disponibles ahora mismo?"),
        ("asistente", "Ahora mismo en catálogo tenemos, entre otros, el MANSORY "
                      "Elongation EVO ($1.200.000.000 COP), el MANSORY Bentley GT "
                      "($1.800.000.000 COP) y el MANSORY Phantom VIII "
                      "($3.200.000.000 COP). ¿Te interesa alguno en particular?"),
        ("usuario", "¿El Bentley GT qué motor trae?"),
        ("asistente", "El MANSORY Bentley GT monta un W12 biturbo. Si quieres "
                      "verlo de cerca, puedes agendar una prueba de manejo desde "
                      "la sección Agenda del sitio."),
    ]),
    ("Precio del peritaje", [
        ("usuario", "cuanto cuesta el peritaje?"),
        ("asistente", "El peritaje de 120 puntos cuesta $350.000 COP y toma "
                      "unas dos horas. Se agenda desde la sección Agenda."),
    ]),
    ("Dato que no tengo", [
        ("usuario", "Dame el celular del gerente y su correo personal"),
        ("asistente", "Lo siento, no dispongo de esa información. Puedes "
                      "escribirnos a contacto@autoprime.com.co o radicar una PQR "
                      "desde la sección PQR, y una persona del equipo te atiende."),
    ]),
]

NOTAS_VENTA = [
    None, None, None,
    "Entrega coordinada en el atelier.",
    "El cliente solicita placas de exhibición.",
    "Pago en dos contados, segundo contado confirmado.",
    "Incluye traslado a Bogotá.",
]


def instante(dias_atras: int) -> datetime:
    """Una marca de tiempo verosímil dentro del horario del atelier."""
    dia = hoy() - timedelta(days=dias_atras)
    return datetime.combine(dia, time(random.randint(8, 17), random.choice([0, 15, 30, 45])))


def limpiar(sesion: Session) -> None:
    """Borra el movimiento y los clientes de demostración.

    No toca el catálogo, los roles ni las tres cuentas de `preparar_base.py`:
    esas son con las que se entra, y borrarlas dejaría el sistema sin puerta.
    """
    for tabla in ("mensajes", "conversaciones", "pqr", "detalle_facturas",
                  "facturas", "detalle_ventas", "ventas", "citas"):
        borradas = sesion.execute(text(f"DELETE FROM {tabla}")).rowcount
        if borradas:
            print(f"    {tabla:<18} {borradas} filas")

    borrados = sesion.execute(
        text("DELETE FROM usuarios WHERE correo LIKE :patron"),
        {"patron": f"%{DOMINIO_DEMO}"},
    ).rowcount
    if borrados:
        print(f"    usuarios (demo)    {borrados} filas")

    sesion.execute(text("UPDATE productos SET estado = 'disponible'"))
    sesion.commit()


def crear_clientes(sesion: Session, rol_cliente: int) -> list[Usuario]:
    """Las contraseñas se cifran igual que en el alta real.

    Podrían quedar todas con el mismo hash precalculado y ahorrar un segundo,
    pero entonces no servirían para entrar y probar el panel de cliente, que
    es media razón de que existan.
    """
    clave = bcrypt.hashpw(b"Demo2026!", bcrypt.gensalt(rounds=configuracion.rondas_bcrypt))

    creados = []
    for nombre, apellido, documento, direccion, telefono in CLIENTES:
        correo = (
            f"{nombre.split()[0].lower()}.{apellido.split()[0].lower()}{DOMINIO_DEMO}"
            .replace("á", "a").replace("é", "e").replace("í", "i")
            .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        )
        usuario = Usuario(
            nombre=nombre, apellido=apellido, tipo_documento="CC",
            numero_documento=documento, direccion=direccion, telefono=telefono,
            correo=correo, password_hash=clave.decode(), rol_id=rol_cliente,
            estado="activo",
            creado_en=instante(random.randint(60, 120)),
        )
        sesion.add(usuario)
        creados.append(usuario)

    sesion.flush()
    return creados


def armar_linea(elemento, cantidad: int = 1) -> DetalleVenta:
    """Una línea con la copia del precio, igual que la arma la API."""
    if isinstance(elemento, Producto):
        precio = Decimal(elemento.precio)
        descripcion = f"{elemento.marca} {elemento.modelo} ({elemento.anio})"
        referencia = {"producto_id": elemento.id}
    else:
        precio = Decimal(elemento.precio)
        descripcion = elemento.nombre
        referencia = {"servicio_id": elemento.id}

    precio = redondear_dinero(precio)
    return DetalleVenta(
        descripcion=descripcion, cantidad=cantidad, precio_unitario=precio,
        descuento=Decimal(0), subtotal=redondear_dinero(precio * cantidad), **referencia,
    )


def crear_venta(sesion: Session, comprador, vendedor, lineas, fecha, estado, notas):
    """Monta la venta con las mismas cuentas que hace la API."""
    bruto = sum((l.subtotal for l in lineas), Decimal(0))
    subtotal = redondear_dinero(bruto)
    impuestos = redondear_dinero(subtotal * TASA_IVA)

    venta = Venta(
        numero="tmp", usuario_id=comprador.id,
        vendedor_id=vendedor.id if vendedor else None,
        fecha=fecha, subtotal=subtotal, descuento=Decimal(0),
        impuestos=impuestos, total=redondear_dinero(subtotal + impuestos),
        estado=estado, notas=notas, creado_en=fecha, lineas=lineas,
    )
    sesion.add(venta)
    sesion.flush()

    # El consecutivo lleva el año de la venta, no el de hoy: una venta de
    # diciembre consultada en enero no puede aparecer con el año nuevo.
    venta.numero = f"V-{fecha.year}-{venta.id:05d}"
    return venta


def main() -> int:
    argumentos = argparse.ArgumentParser(
        description="Inserta movimiento de ejemplo para poder enseñar el sistema."
    )
    argumentos.add_argument(
        "--limpiar", action="store_true",
        help="Borra el movimiento y los clientes de demostración antes de sembrar.",
    )
    opciones = argumentos.parse_args()

    motor = create_engine(
        configuracion.url_base_datos_sincrona,
        connect_args=configuracion.conexion_args_sincrona,
    )

    with Session(motor) as sesion:
        rol_cliente = sesion.execute(
            text("SELECT id FROM roles WHERE nombre = 'cliente'")
        ).scalar()
        if rol_cliente is None:
            print("  No hay roles en la base. Corre antes preparar_base.py.")
            return 1

        if opciones.limpiar:
            print("  Limpiando lo anterior")
            limpiar(sesion)
            print()

        if sesion.execute(text("SELECT COUNT(*) FROM ventas")).scalar():
            print("  Ya hay ventas en la base. Usa --limpiar para empezar de cero.")
            return 1

        personal = list(sesion.query(Usuario).join(Rol).filter(
            Rol.nombre.in_(("administrador", "empleado"))
        ).all())
        cliente_semilla = sesion.query(Usuario).filter(
            Usuario.correo == "cliente@autoprime.com.co"
        ).one_or_none()

        productos = {p.id: p for p in sesion.query(Producto).all()}
        servicios = {s.id: s for s in sesion.query(Servicio).all()}
        peritaje = next(s for s in servicios.values() if s.precio)

        print("  Clientes")
        clientes = crear_clientes(sesion, rol_cliente)
        # La cuenta de siempre también compra: si no, quien entre como
        # cliente@autoprime.com.co ve su panel vacío, que es justo el panel
        # que se quiere enseñar.
        compradores = clientes + ([cliente_semilla] * 3 if cliente_semilla else [])
        print(f"    {len(clientes)} clientes nuevos ({DOMINIO_DEMO}, clave Demo2026!)")
        print()

        # ------------------------------------------------------------------
        print("  Ventas")
        ids_pesados = [i for i, peso in PESOS_VEHICULOS.items() for _ in range(peso)]
        ventas = []

        # Un reparto pensado, no aleatorio del todo: el tablero tiene que
        # enseñar los cuatro estados y que el de hoy no salga vacío.
        plan = (
            [("pagada", d) for d in random.sample(range(1, DIAS_ATRAS), 22)]
            + [("pendiente", d) for d in random.sample(range(0, 12), 6)]
            + [("anulada", d) for d in random.sample(range(5, DIAS_ATRAS), 4)]
            + [("pagada", 0), ("pagada", 0), ("pendiente", 0)]
        )

        for estado, dias in sorted(plan, key=lambda p: -p[1]):
            comprador = random.choice(compradores)
            vendedor = random.choice(personal) if random.random() < 0.65 else None

            elegibles = (
                [i for i in ids_pesados if i not in SOLO_POR_COBRAR]
                if estado == "pagada"
                else ids_pesados
            )
            lineas = [armar_linea(productos[random.choice(elegibles)])]
            # Uno de cada tres se lleva además el peritaje.
            if random.random() < 0.33:
                lineas.append(armar_linea(peritaje))

            ventas.append(crear_venta(
                sesion, comprador, vendedor, lineas, instante(dias), estado,
                random.choice(NOTAS_VENTA),
            ))

        sesion.flush()
        por_estado = {}
        for v in ventas:
            por_estado[v.estado] = por_estado.get(v.estado, 0) + 1
        print(f"    {len(ventas)} ventas: " + ", ".join(
            f"{n} {e}" for e, n in sorted(por_estado.items())))

        # ------------------------------------------------------------------
        # Se factura la mayoría de lo cobrado, pero no todo: en la realidad
        # siempre hay alguna pendiente de emitir, y el panel tiene que poder
        # enseñar ese caso.
        print()
        print("  Facturas")
        emitidas = 0
        for venta in ventas:
            if venta.estado != "pagada" or random.random() < 0.15:
                continue

            factura = Factura(
                numero="tmp", venta_id=venta.id,
                fecha_emision=venta.fecha + timedelta(hours=random.randint(1, 30)),
                subtotal=venta.subtotal, impuestos=venta.impuestos,
                total=venta.total, estado="emitida", creado_en=venta.fecha,
                lineas=[
                    DetalleFactura(
                        descripcion=l.descripcion, cantidad=l.cantidad,
                        precio_unitario=l.precio_unitario, subtotal=l.subtotal,
                    )
                    for l in venta.lineas
                ],
            )
            sesion.add(factura)
            sesion.flush()
            factura.numero = f"F-{factura.fecha_emision.year}-{factura.id:05d}"
            emitidas += 1

        print(f"    {emitidas} emitidas")

        # ------------------------------------------------------------------
        print()
        print("  Citas")
        franjas = [time(h, 0) for h in range(8, 18)]
        ocupadas = set()
        citas = 0

        reparto = (
            [("completada", random.randint(3, 45)) for _ in range(6)]
            + [("cancelada", random.randint(3, 45)) for _ in range(3)]
            + [("confirmada", -random.randint(1, 12)) for _ in range(4)]
            + [("pendiente", -random.randint(1, 20)) for _ in range(5)]
        )

        for estado, dias in reparto:
            dia = hoy() - timedelta(days=dias)
            if dia.weekday() == 6:          # el domingo no se atiende
                dia += timedelta(days=1)

            producto = productos[random.choice(ids_pesados)]
            hora = random.choice(franjas)
            # La base tiene un UNIQUE sobre (fecha, hora, producto): sin esta
            # comprobación el sembrado se caería a la mitad con un choque.
            if (dia, hora, producto.id) in ocupadas:
                continue
            ocupadas.add((dia, hora, producto.id))

            sesion.add(Cita(
                usuario_id=random.choice(compradores).id,
                producto_id=producto.id,
                servicio_id=random.choice([1, 2, 3, 5]),
                fecha=dia, hora=hora, estado=estado,
                notas=random.choice([None, None, "El cliente pregunta por retoma."]),
                creado_en=instante(max(dias, 0) + random.randint(1, 5)),
            ))
            citas += 1

        print(f"    {citas} citas entre pasadas y futuras")

        # ------------------------------------------------------------------
        print()
        print("  PQR")
        for i, (tipo, asunto, descripcion, respuesta, estado) in enumerate(ASUNTOS_PQR):
            creada = instante(random.randint(1, 40))
            registro = Pqr(
                numero="tmp", usuario_id=random.choice(compradores).id,
                tipo=tipo, asunto=asunto, descripcion=descripcion,
                estado=estado, respuesta=respuesta,
                atendido_por=random.choice(personal).id if respuesta else None,
                creado_en=creada,
                actualizado_en=creada + timedelta(days=random.randint(0, 3)),
            )
            sesion.add(registro)
            sesion.flush()
            registro.numero = f"P-{creada.year}-{registro.id:05d}"

        print(f"    {len(ASUNTOS_PQR)} radicados en los cuatro estados")

        # ------------------------------------------------------------------
        print()
        print("  Conversaciones del asistente")
        for titulo, mensajes in CONVERSACIONES:
            inicio = instante(random.randint(0, 15))
            conversacion = Conversacion(
                usuario_id=random.choice(compradores).id if random.random() < 0.6 else None,
                titulo=titulo, creado_en=inicio,
                ultima_actividad=inicio + timedelta(minutes=len(mensajes) * 2),
                mensajes=[
                    Mensaje(rol=rol, contenido=texto,
                            creado_en=inicio + timedelta(minutes=i * 2))
                    for i, (rol, texto) in enumerate(mensajes)
                ],
            )
            sesion.add(conversacion)

        print(f"    {len(CONVERSACIONES)} hilos")

        # ------------------------------------------------------------------
        # El estado del catálogo se fija AL FINAL y a mano.
        #
        # Es lo que separa el histórico del presente: las ventas dicen lo que
        # pasó y `productos.estado` dice cómo está el catálogo ahora. Si cada
        # venta marcara su vehículo, dos meses de movimiento dejarían el
        # catálogo entero vendido y no quedaría nada que enseñar.
        print()
        print("  Catálogo")
        vendidos = [3, 8]
        sesion.execute(
            text("UPDATE productos SET estado = 'disponible'")
        )
        sesion.execute(
            text("UPDATE productos SET estado = 'vendido' WHERE id IN (:a, :b)"),
            {"a": vendidos[0], "b": vendidos[1]},
        )
        print(f"    {len(productos) - len(vendidos)} disponibles, "
              f"{len(vendidos)} marcados como vendidos")

        sesion.commit()

    # ----------------------------------------------------------------------
    with Session(motor) as sesion:
        print()
        print("  Resultado")
        for tabla in ("usuarios", "ventas", "detalle_ventas", "facturas",
                      "detalle_facturas", "citas", "pqr", "conversaciones",
                      "mensajes"):
            total = sesion.execute(text(f"SELECT COUNT(*) FROM {tabla}")).scalar()
            print(f"    {tabla:<18} {total:>4}")

        cobrado = sesion.execute(
            text("SELECT COALESCE(SUM(total), 0) FROM ventas WHERE estado = 'pagada'")
        ).scalar()
        print()
        print(f"    Ingresos del histórico: ${cobrado:,.0f} COP")
        print()
        print(f"    Los clientes nuevos entran con la clave  Demo2026!")
        print(f"    Ejemplo: valentina.restrepo{DOMINIO_DEMO}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
