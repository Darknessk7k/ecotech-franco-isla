"""Pruebas automáticas del cliente de API, el Plan B y la seguridad.

Usa un servidor local falso (no gasta la API real y permite simular errores):
    python -m pruebas.prueba_api_cliente
"""
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# --- se configura el entorno ANTES de importar el proyecto, para no tocar la base real ---
CARPETA_TEMPORAL = tempfile.mkdtemp()
os.environ["ECOTECH_DB_PATH"] = os.path.join(CARPETA_TEMPORAL, "prueba.db")
os.environ["CIUDADES_SINCRONIZAR"] = "Concepción:CL,Santiago:CL"

from api_cliente import ClienteAPI                                    # noqa: E402
from dominio.administrador import Administrador                       # noqa: E402
from dominio.empleado import Empleado                                 # noqa: E402
from dominio.excepciones import (AccesoDenegadoError, ApiClienteError, ApiNoDisponibleError,  # noqa: E402
                                 DatoInvalidoError, NoEncontradoError, RespuestaInvalidaError, SinDatosError)
from dominio.seguridad import generar_hash                            # noqa: E402
from datetime import date                                             # noqa: E402
from repositorio.conexion import inicializar_bd, consultar            # noqa: E402
from servicio_externo import ServicioExterno                          # noqa: E402

ESTADO = {"modo": "ok", "peticiones": 0}


class ApiFalsa(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _responder(self, codigo, cuerpo=b"", cabeceras=None):
        self.send_response(codigo)
        for k, v in (cabeceras or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        try:
            self.wfile.write(cuerpo)
        except (BrokenPipeError, ConnectionResetError):
            pass   # el cliente se desconectó (pasa en la prueba de timeout)

    def do_GET(self):
        ESTADO["peticiones"] += 1
        modo = ESTADO["modo"]
        if modo == "500":
            return self._responder(500)
        if modo == "404":
            return self._responder(404)
        if modo == "429":
            return self._responder(429, cabeceras={"Retry-After": "3"})
        if modo == "json_roto":
            return self._responder(200, b"esto no es json")
        if modo == "lento":
            import time
            time.sleep(3)
        ruta = urlparse(self.path)
        consulta = parse_qs(ruta.query)
        if ruta.path == "/geo":
            if consulta.get("name", [""])[0] == "Noexiste":
                return self._responder(200, b'{"generationtime_ms": 0.2}')
            cuerpo = {"results": [{"name": "Concepción", "country": "Chile", "country_code": "CL",
                                   "latitude": -36.82, "longitude": -73.05}]}
        elif ruta.path == "/forecast":
            cuerpo = {"current": {"time": "2026-11-20T10:00", "temperature_2m": 17.4,
                                  "relative_humidity_2m": 63, "weather_code": 2}}
        elif ruta.path == "/api/dolar":
            cuerpo = {"codigo": "dolar", "nombre": "Dólar observado", "unidad_medida": "Pesos",
                      "serie": [{"fecha": "2026-11-19T03:00:00.000Z", "valor": 950.0},
                                {"fecha": "2026-11-18T03:00:00.000Z", "valor": 948.0}]}
        elif ruta.path == "/api/euro":
            cuerpo = {"codigo": "euro", "nombre": "Euro", "unidad_medida": "Pesos",
                      "serie": [{"fecha": "2026-11-19T03:00:00.000Z", "valor": 1100.0}]}
        else:
            return self._responder(404)
        self._responder(200, json.dumps(cuerpo).encode("utf-8"))


def crear_cliente(**kwargs):
    cliente = ClienteAPI(**kwargs)
    cliente.esperas = []
    cliente._dormir = cliente.esperas.append   # no se espera de verdad
    return cliente


class PruebasBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = HTTPServer(("127.0.0.1", 0), ApiFalsa)
        cls.base = f"http://127.0.0.1:{cls.servidor.server_port}"
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def setUp(self):
        ESTADO["modo"] = "ok"
        ESTADO["peticiones"] = 0


class PruebasCliente(PruebasBase):

    def test_respuesta_200(self):
        datos = crear_cliente().obtener_json(f"{self.base}/api/dolar")
        self.assertEqual(datos["codigo"], "dolar")

    def test_4xx_no_se_reintenta(self):
        ESTADO["modo"] = "404"
        with self.assertRaises(ApiClienteError):
            crear_cliente().obtener_json(f"{self.base}/api/dolar")
        self.assertEqual(ESTADO["peticiones"], 1)

    def test_5xx_se_reintenta_con_backoff_y_termina(self):
        ESTADO["modo"] = "500"
        cliente = crear_cliente(max_intentos=4, espera_base=1)
        with self.assertRaises(ApiNoDisponibleError):
            cliente.obtener_json(f"{self.base}/api/dolar")
        self.assertEqual(ESTADO["peticiones"], 4)
        self.assertEqual(cliente.esperas, [1, 2, 4])      # espera creciente

    def test_429_respeta_retry_after(self):
        ESTADO["modo"] = "429"
        cliente = crear_cliente(max_intentos=2, espera_base=1)
        with self.assertRaises(ApiNoDisponibleError):
            cliente.obtener_json(f"{self.base}/api/dolar")
        self.assertEqual(cliente.esperas, [3])            # usó el Retry-After: 3

    def test_sin_red_se_reintenta(self):
        cliente = crear_cliente(max_intentos=3, espera_base=1)
        with self.assertRaises(ApiNoDisponibleError):
            cliente.obtener_json("http://127.0.0.1:9/nada")   # puerto cerrado
        self.assertEqual(cliente.esperas, [1, 2])

    def test_timeout(self):
        ESTADO["modo"] = "lento"
        cliente = crear_cliente(timeout=1, max_intentos=1)
        with self.assertRaises(ApiNoDisponibleError):
            cliente.obtener_json(f"{self.base}/api/dolar")

    def test_url_mal_formada_no_se_reintenta(self):
        cliente = crear_cliente()
        with self.assertRaises(ApiClienteError):
            cliente.obtener_json("htp://esto-no-es-una-url")
        self.assertEqual(cliente.esperas, [])

    def test_json_invalido(self):
        ESTADO["modo"] = "json_roto"
        with self.assertRaises(RespuestaInvalidaError):
            crear_cliente().obtener_json(f"{self.base}/api/dolar")


class PruebasServicio(PruebasBase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ["API_CLIMA_GEO_URL"] = f"{cls.base}/geo"
        os.environ["API_CLIMA_URL"] = f"{cls.base}/forecast"
        os.environ["API_CAMBIO_URL"] = f"{cls.base}/api"
        inicializar_bd()
        cls.admin = Administrador("admin", generar_hash("ClaveAdmin1"), "Recursos Humanos")
        assert cls.admin.autenticar("ClaveAdmin1")
        cls.empleado = Empleado("ana.perez", generar_hash("Clave1234"), "Ana Pérez", "Calle 1",
                                "+56911112222", "ana@ecotech.cl", date(2024, 3, 1), 950000)
        assert cls.empleado.autenticar("Clave1234")

    def setUp(self):
        super().setUp()
        self.servicio = ServicioExterno(cliente=crear_cliente(max_intentos=2, espera_base=0))

    def test_sin_sesion_no_consulta(self):
        sin_login = Administrador("otro.admin", generar_hash("Clave12345"), "RRHH")
        with self.assertRaises(AccesoDenegadoError):
            self.servicio.consultar_clima(sin_login, "Concepción", "CL")
        self.assertEqual(ESTADO["peticiones"], 0)          # ni siquiera llamó a la API

    def test_empleado_no_ve_tipo_de_cambio(self):
        with self.assertRaises(AccesoDenegadoError):
            self.servicio.consultar_cambio(self.empleado, "USD")

    def test_entradas_invalidas(self):
        for ciudad in ["", "  ", "Santiago'; DROP TABLE clima;--", "<script>", "A", "x" * 100]:
            with self.assertRaises(DatoInvalidoError):
                self.servicio.consultar_clima(self.admin, ciudad, "")
        with self.assertRaises(DatoInvalidoError):
            self.servicio.consultar_clima(self.admin, "Santiago", "CHILE")
        with self.assertRaises(DatoInvalidoError):
            self.servicio.consultar_cambio(self.admin, "BTC")

    def test_ciudad_inexistente(self):
        with self.assertRaises(NoEncontradoError):
            self.servicio.consultar_clima(self.admin, "Noexiste", "")

    def test_clima_en_vivo_e_idempotente(self):
        for _ in range(2):
            r = self.servicio.consultar_clima(self.admin, "Concepción", "CL")
            self.assertTrue(r.en_vivo)
            self.assertEqual(r.datos.temperatura, 17.4)
        filas = consultar("SELECT COUNT(*) AS n FROM clima WHERE clave_busqueda = ?", ("concepcion|CL",))
        self.assertEqual(filas[0]["n"], 1)

    def test_plan_b_cuando_la_api_cae(self):
        self.servicio.consultar_clima(self.admin, "Concepción", "CL")     # deja datos guardados
        ESTADO["modo"] = "500"
        r = self.servicio.consultar_clima(self.admin, "Concepción", "CL")
        self.assertFalse(r.en_vivo)
        self.assertEqual(r.datos.temperatura, 17.4)
        self.assertTrue(r.obtenido_en)

    def test_plan_b_con_url_invalida_404(self):
        self.servicio.consultar_clima(self.admin, "Concepción", "CL")
        os.environ["API_CLIMA_GEO_URL"] = f"{self.base}/ruta-que-no-existe"
        try:
            r = self.servicio.consultar_clima(self.admin, "Concepción", "CL")
        finally:
            os.environ["API_CLIMA_GEO_URL"] = f"{self.base}/geo"
        self.assertFalse(r.en_vivo)

    def test_sin_datos_guardados_y_api_caida(self):
        ESTADO["modo"] = "500"
        with self.assertRaises(SinDatosError):
            self.servicio.consultar_clima(self.admin, "Ciudad Nueva", "CL")

    def test_pago_internacional(self):
        pago = self.servicio.calcular_pago(self.admin, self.empleado, "USD")
        self.assertEqual(str(pago.monto), "1000.00")       # 950000 / 950
        self.assertEqual(pago.moneda, "USD")

    def test_sincronizar_dos_veces_no_duplica(self):
        self.servicio.sincronizar(self.admin)
        primero = self.servicio.sincronizar(self.admin)
        segundo = self.servicio.sincronizar(self.admin)
        self.assertEqual(primero["total_clima"], segundo["total_clima"])
        self.assertEqual(primero["total_cambio"], segundo["total_cambio"])
        self.assertEqual(segundo["errores"], [])

    def test_contrasenas_con_bcrypt_y_salt(self):
        h1, h2 = generar_hash("MismaClave1"), generar_hash("MismaClave1")
        self.assertTrue(h1.startswith("$2b$"))
        self.assertNotEqual(h1, h2)                         # distinto salt => distinto hash
        self.assertNotIn("MismaClave1", h1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
