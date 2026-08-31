#!/usr/bin/env bash
# =============================================================================
#  Convierte un escaneo 3D en un GLB ligero para la web.
#
#  Los modelos llegan como OBJ de ~125 MB: un millon de caras y las texturas
#  PBR sueltas, sin .mtl que las enlace. Este script los deja en torno a 1,5 MB
#  sin que se note la diferencia en pantalla.
#
#  USO
#      bash herramientas/convertir-modelo-3d.sh <carpeta-origen> <salida.glb>
#
#  REQUISITOS (se instalan en cualquier carpeta temporal, no en el proyecto)
#      npm install obj2gltf @gltf-transform/cli
#      Python con Pillow  (ya viene con el entorno)
#
#  DESPUES DE CONVERTIR
#      1. Copiar el .glb a  frontend/public/modelos3d/
#      2. Anadir al vehiculo en  frontend/src/data/vehiculos.js:
#             modelo3d: { archivo: "/modelos3d/<nombre>.glb", peso: "1,4 MB" }
#         La ficha muestra el apartado "En 3D" y su entrada en el submenu solo
#         si ese campo existe; no hay que tocar ninguna pagina.
#
#  QUE HACE Y POR QUE
#      - Escribe el .mtl que el exportador no genera y enlaza las texturas.
#      - Usa `texture_pbr` como mapa ORM combinado (oclusion en R, rugosidad en
#        G, metalicidad en B). Eso deja fuera los mapas sueltos de rugosidad y
#        metalicidad, que son redundantes.
#      - Simplifica la malla al 12 % (1.000.000 -> ~187.000 triangulos).
#      - Comprime con Draco y NO con meshopt: `model-viewer` no incluye el
#        decodificador de meshopt y fallaria al cargar.
# =============================================================================

set -e
ORIGEN="$1"; SALIDA="$2"; BASE="$(dirname "$0")"
GT="node $BASE/node_modules/@gltf-transform/cli/bin/cli.js"
OBJ2="node $BASE/node_modules/obj2gltf/bin/obj2gltf.js"
TMP="$BASE/tmp"; rm -rf "$TMP"; mkdir -p "$TMP"

cp "$ORIGEN"/texture_diffuse.png "$ORIGEN"/texture_normal.png "$ORIGEN"/texture_pbr.png "$TMP/"

# Difuso a 2048 (es lo que se mira); normal y ORM a 1024, que basta.
python -c "
from PIL import Image
for n,l in [('texture_diffuse',2048),('texture_normal',1024),('texture_pbr',1024)]:
    im=Image.open(r'$TMP/'+n+'.png').convert('RGB')
    if im.size[0]!=l: im=im.resize((l,l),Image.LANCZOS)
    im.save(r'$TMP/'+n+'.jpg','JPEG',quality=88,optimize=True,progressive=True)
"

cat > "$TMP/base.mtl" <<'MTL'
# El OBJ exportado no trae .mtl: se escribe aqui para enlazar las texturas.
newmtl vehiculo
Kd 1.000 1.000 1.000
d 1.0
illum 2
map_Kd texture_diffuse.jpg
norm texture_normal.jpg
MTL

# Inserta la referencia al material, que el exportador no puso.
ORIGEN_OBJ="$ORIGEN/base.obj" DESTINO_OBJ="$TMP/base.obj" python -c "
import io,os
with io.open(os.environ['ORIGEN_OBJ'],encoding='utf-8',errors='replace') as e, \
     io.open(os.environ['DESTINO_OBJ'],'w',encoding='utf-8') as s:
    puesto=False
    for l in e:
        if not puesto and l.startswith('o '):
            s.write('mtllib base.mtl\n'); s.write(l); s.write('usemtl vehiculo\n'); puesto=True; continue
        s.write(l)
"

cd "$TMP"
$OBJ2 -i base.obj -o crudo.glb --binary --metallicRoughnessOcclusionTexture texture_pbr.jpg >/dev/null
$GT weld crudo.glb w.glb >/dev/null 2>&1
$GT simplify w.glb s.glb --ratio 0.12 --error 0.0012 >/dev/null 2>&1
# Draco y no meshopt: `model-viewer` no incluye el decodificador de meshopt.
$GT draco s.glb "$SALIDA" >/dev/null 2>&1
printf "  %s -> %.2f MB\n" "$(basename "$SALIDA")" "$(wc -c < "$SALIDA" | awk '{print $1/1048576}')"
