import csv
import os
from datetime import date

from dominio.excepciones import DatoInvalidoError

FORMATOS = ("csv", "txt")


class Informe:

    def __init__(self, tipo: str, formato: str, fecha_generacion: date, filas: list):
        formato = formato.strip().lower()
        if formato not in FORMATOS:
            raise DatoInvalidoError("Formato no soportado. Use csv o txt.")
        self._tipo = tipo
        self._formato = formato
        self._fecha_generacion = fecha_generacion
        self._filas = filas

    @property
    def tipo(self):
        return self._tipo

    @property
    def formato(self):
        return self._formato

    def exportar(self, carpeta: str = "informes") -> str:
        os.makedirs(carpeta, exist_ok=True)
        nombre = f"informe_{self._tipo}_{self._fecha_generacion}.{self._formato}"
        ruta = os.path.join(carpeta, nombre)
        if self._formato == "csv":
            with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
                escritor = csv.writer(archivo, delimiter=";")
                escritor.writerow(["Proyecto", "Empleado", "Total horas"])
                escritor.writerows(self._filas)
        else:
            with open(ruta, "w", encoding="utf-8") as archivo:
                archivo.write(f"Informe de {self._tipo} - EcoTech Solutions ({self._fecha_generacion})\n\n")
                for proyecto, empleado, horas in self._filas:
                    archivo.write(f"{proyecto:<25} {empleado:<20} {horas:>6} h\n")
        return ruta
