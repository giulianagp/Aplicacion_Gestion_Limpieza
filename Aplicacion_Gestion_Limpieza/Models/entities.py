
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256

from Utils.permissions import PermissionManager


@dataclass
class Usuario:
    id: int | None
    username: str
    password: str
    rol: str

    def __post_init__(self) -> None:
        self.rol = PermissionManager.normalize_role(self.rol)

    def validar(self) -> None:
        if not self.username.strip():
            raise ValueError("El campo 'usuario' es obligatorio.")
        if not self.password.strip():
            raise ValueError("El campo 'password' es obligatorio.")
        if not self.rol.strip():
            raise ValueError("El campo 'rol' es obligatorio.")

    def password_hash(self) -> str:
        return sha256(self.password.encode("utf-8")).hexdigest()

    def coincide_password(self, plain_password: str) -> bool:
        candidate_hash = sha256(plain_password.encode("utf-8")).hexdigest()
        return self.password in {plain_password, candidate_hash}


@dataclass
class Cuadrilla:
    id: int | None
    nombre: str
    id_jefe: int | None

    def validar(self) -> None:
        if not self.nombre.strip():
            raise ValueError("El campo 'nombre' es obligatorio.")
        if self.id_jefe is not None and int(self.id_jefe) <= 0:
            raise ValueError("El campo 'jefe' debe ser mayor a cero.")


@dataclass
class CuadrillaDetalle(Cuadrilla):
    jefe_nombre: str | None = None

    @property
    def jefe_display(self) -> str:
        return self.jefe_nombre or ""


@dataclass
class Empleado:
    id: int | None
    nombre: str
    tipo: str
    id_cuadrilla: int | None

    def validar(self) -> None:
        if not self.nombre.strip():
            raise ValueError("El campo 'nombre' es obligatorio.")
        if not self.tipo.strip():
            raise ValueError("El campo 'tipo' es obligatorio.")
        if self.id_cuadrilla is not None and int(self.id_cuadrilla) <= 0:
            raise ValueError("El campo 'cuadrilla' debe ser mayor a cero.")


@dataclass
class EmpleadoDetalle(Empleado):
    cuadrilla_nombre: str | None = None

    @property
    def cuadrilla_display(self) -> str:
        return self.cuadrilla_nombre or ""


@dataclass
class Colonia:
    id: int | None
    nombre: str
    codigo_postal: str

    def validar(self) -> None:
        if not self.nombre.strip():
            raise ValueError("El campo 'nombre' es obligatorio.")
        if not self.codigo_postal.strip():
            raise ValueError("El campo 'codigo postal' es obligatorio.")


@dataclass
class Actividad:
    id: int | None
    descripcion: str
    fecha: str
    estado: str
    imagen: str
    id_cuadrilla: int | None
    id_colonia: int | None

    def validar(self) -> None:
        if not self.descripcion.strip():
            raise ValueError("El campo 'descripcion' es obligatorio.")
        if not self.estado.strip():
            raise ValueError("El campo 'estado' es obligatorio.")
        try:
            datetime.strptime(self.fecha, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("El campo 'fecha' debe tener formato YYYY-MM-DD.") from exc
        if self.id_cuadrilla is None or int(self.id_cuadrilla) <= 0:
            raise ValueError("El campo 'cuadrilla' debe ser mayor a cero.")
        if self.id_colonia is None or int(self.id_colonia) <= 0:
            raise ValueError("El campo 'colonia' debe ser mayor a cero.")


@dataclass
class ActividadDetalle(Actividad):
    cuadrilla_nombre: str | None = None
    colonia_nombre: str | None = None

    @property
    def cuadrilla_display(self) -> str:
        return self.cuadrilla_nombre or ""

    @property
    def colonia_display(self) -> str:
        return self.colonia_nombre or ""


@dataclass
class ResumenItem:
    etiqueta: str
    total: int

    @property
    def display_label(self) -> str:
        return self.etiqueta or "Sin asignar"


@dataclass
class DashboardSummary:
    total_actividades: int
    por_cuadrilla: list[ResumenItem]
    por_estado: list[ResumenItem]
