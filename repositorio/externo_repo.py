from dominio.datos_externos import Clima, TipoCambio, ahora_utc
from repositorio.conexion import consultar, ejecutar


class ClimaRepositorio:

    def guardar(self, clave: str, ciudad_consulta: str, pais_consulta: str, clima: Clima) -> str:
        """Inserta o actualiza (según clave_busqueda). Devuelve el instante de obtención."""
        obtenido_en = ahora_utc()
        ejecutar(
            "INSERT INTO clima (clave_busqueda, ciudad_consulta, pais_consulta, ciudad, pais, latitud, "
            "longitud, temperatura, humedad, codigo_tiempo, fecha_api, obtenido_en) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(clave_busqueda) DO UPDATE SET "
            "ciudad = excluded.ciudad, pais = excluded.pais, latitud = excluded.latitud, "
            "longitud = excluded.longitud, temperatura = excluded.temperatura, humedad = excluded.humedad, "
            "codigo_tiempo = excluded.codigo_tiempo, fecha_api = excluded.fecha_api, "
            "obtenido_en = excluded.obtenido_en",
            (clave, ciudad_consulta, pais_consulta, clima.ciudad, clima.pais, clima.latitud,
             clima.longitud, clima.temperatura, clima.humedad, clima.codigo_tiempo, clima.fecha_api,
             obtenido_en),
        )
        clima.obtenido_en = obtenido_en
        return obtenido_en

    def obtener(self, clave: str):
        filas = consultar("SELECT * FROM clima WHERE clave_busqueda = ?", (clave,))
        if not filas:
            return None
        f = filas[0]
        return Clima(
            ciudad=f["ciudad"], pais=f["pais"], latitud=f["latitud"], longitud=f["longitud"],
            temperatura=f["temperatura"], humedad=f["humedad"], codigo_tiempo=f["codigo_tiempo"],
            fecha_api=f["fecha_api"], obtenido_en=f["obtenido_en"],
        )

    def contar(self) -> int:
        return consultar("SELECT COUNT(*) AS total FROM clima")[0]["total"]


class TipoCambioRepositorio:

    def guardar(self, cambio: TipoCambio) -> str:
        obtenido_en = ahora_utc()
        ejecutar(
            "INSERT INTO tipo_cambio (codigo, nombre, valor, fecha_valor, obtenido_en) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(codigo, fecha_valor) DO UPDATE SET "
            "nombre = excluded.nombre, valor = excluded.valor, obtenido_en = excluded.obtenido_en",
            (cambio.codigo, cambio.nombre, cambio.valor, cambio.fecha_valor, obtenido_en),
        )
        cambio.obtenido_en = obtenido_en
        return obtenido_en

    def obtener_ultimo(self, codigo: str):
        """El valor más reciente guardado para esa moneda (por fecha del valor)."""
        filas = consultar(
            "SELECT codigo, nombre, valor, fecha_valor, obtenido_en FROM tipo_cambio "
            "WHERE codigo = ? ORDER BY fecha_valor DESC LIMIT 1",
            (codigo,),
        )
        if not filas:
            return None
        f = filas[0]
        return TipoCambio(f["codigo"], f["nombre"], f["valor"], f["fecha_valor"], f["obtenido_en"])

    def contar(self) -> int:
        return consultar("SELECT COUNT(*) AS total FROM tipo_cambio")[0]["total"]
