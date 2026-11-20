import logging
import os

CARPETA = os.path.dirname(os.path.abspath(__file__))


def configurar_logging():
    """Los detalles técnicos van a logs/ecotech.log; al usuario solo se le muestran mensajes seguros."""
    carpeta_logs = os.path.join(CARPETA, "logs")
    os.makedirs(carpeta_logs, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(carpeta_logs, "ecotech.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )
