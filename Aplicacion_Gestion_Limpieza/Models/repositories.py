"""Repositorios para acceso a datos."""

from __future__ import annotations

from typing import Any

from Database.connection import DatabaseConnection
from Models.entities import (
    Actividad,
    ActividadDetalle,
    Colonia,
    Cuadrilla,
    CuadrillaDetalle,
    DashboardSummary,
    Empleado,
    EmpleadoDetalle,
    ResumenItem,
    Usuario,
)


class BaseRepository:
    entity_class = None

    def __init__(self, table_name: str, fields: list[str]):
        self.db = DatabaseConnection()
        self.table_name = table_name
        self.fields = fields

    def _build_entity(self, row: dict[str, Any]):
        if self.entity_class is None:
            raise ValueError("entity_class no configurada en el repositorio.")
        return self.entity_class(**row)

    def _build_entities(self, rows: list[dict[str, Any]]) -> list:
        return [self._build_entity(row) for row in rows]

    def _entity_values(self, entity) -> tuple[Any, ...]:
        return tuple(getattr(entity, field) for field in self.fields)

    def get_all(self) -> list:
        rows = self.db.execute(
            f"SELECT * FROM {self.table_name} ORDER BY id DESC",
            fetchall=True,
        )
        return self._build_entities(rows)

    def get_by_id(self, item_id: int):
        row = self.db.execute(
            f"SELECT * FROM {self.table_name} WHERE id = %s",
            (item_id,),
            fetchone=True,
        )
        return self._build_entity(row) if row else None

    def create(self, entity) -> int:
        columns = ", ".join(self.fields)
        placeholders = ", ".join(["%s"] * len(self.fields))
        entity_id = self.db.execute(
            f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})",
            self._entity_values(entity),
            commit=True,
        )
        entity.id = entity_id
        return entity_id

    def update(self, entity) -> None:
        if entity.id is None:
            raise ValueError("La entidad debe tener id para actualizarse.")
        assignments = ", ".join([f"{field} = %s" for field in self.fields])
        values = self._entity_values(entity) + (entity.id,)
        self.db.execute(
            f"UPDATE {self.table_name} SET {assignments} WHERE id = %s",
            values,
            commit=True,
        )

    def delete(self, item_id: int) -> None:
        self.db.execute(
            f"DELETE FROM {self.table_name} WHERE id = %s",
            (item_id,),
            commit=True,
        )


class UsuarioRepository(BaseRepository):
    entity_class = Usuario

    def __init__(self):
        super().__init__("usuarios", ["username", "password", "rol"])

    def authenticate(self, username: str, password: str) -> Usuario | None:
        user = self.db.execute(
            "SELECT * FROM usuarios WHERE username = %s",
            (username,),
            fetchone=True,
        )
        if not user:
            return None

        entity = self._build_entity(user)
        if entity.coincide_password(password):
            return entity
        return None


class CuadrillaRepository(BaseRepository):
    entity_class = Cuadrilla

    def __init__(self):
        super().__init__("cuadrillas", ["nombre", "id_jefe"])

    def get_all_detailed(self) -> list[CuadrillaDetalle]:
        query = """
        SELECT c.id, c.nombre, c.id_jefe, e.nombre AS jefe_nombre
        FROM cuadrillas c
        LEFT JOIN empleados e ON c.id_jefe = e.id
        ORDER BY c.id DESC
        """
        rows = self.db.execute(query, fetchall=True)
        return [CuadrillaDetalle(**row) for row in rows]


class EmpleadoRepository(BaseRepository):
    entity_class = Empleado

    def __init__(self):
        super().__init__("empleados", ["nombre", "tipo", "id_cuadrilla"])

    def get_all_detailed(self) -> list[EmpleadoDetalle]:
        query = """
        SELECT e.id, e.nombre, e.tipo, e.id_cuadrilla, c.nombre AS cuadrilla_nombre
        FROM empleados e
        LEFT JOIN cuadrillas c ON e.id_cuadrilla = c.id
        ORDER BY e.id DESC
        """
        rows = self.db.execute(query, fetchall=True)
        return [EmpleadoDetalle(**row) for row in rows]

    def get_jefes(self) -> list[Empleado]:
        rows = self.db.execute(
            "SELECT id, nombre, tipo, id_cuadrilla FROM empleados WHERE tipo = 'Jefe' ORDER BY nombre",
            fetchall=True,
        )
        return [Empleado(**row) for row in rows]


class ColoniaRepository(BaseRepository):
    entity_class = Colonia

    def __init__(self):
        super().__init__("colonias", ["nombre", "codigo_postal"])


class ActividadRepository(BaseRepository):
    entity_class = Actividad

    def __init__(self):
        super().__init__(
            "actividades",
            ["descripcion", "fecha", "estado", "imagen", "id_cuadrilla", "id_colonia"],
        )

    def get_all_detailed(self) -> list[ActividadDetalle]:
        query = """
        SELECT a.id, a.descripcion, a.fecha, a.estado, a.imagen,
               a.id_cuadrilla, a.id_colonia,
               c.nombre AS cuadrilla_nombre,
               col.nombre AS colonia_nombre
        FROM actividades a
        LEFT JOIN cuadrillas c ON a.id_cuadrilla = c.id
        LEFT JOIN colonias col ON a.id_colonia = col.id
        ORDER BY a.fecha DESC, a.id DESC
        """
        rows = self.db.execute(query, fetchall=True)
        return [ActividadDetalle(**row) for row in rows]

    def get_dashboard_summary(self) -> DashboardSummary:
        total_row = self.db.execute(
            "SELECT COUNT(*) AS total FROM actividades",
            fetchone=True,
        )
        by_cuadrilla_rows = self.db.execute(
            """
            SELECT c.nombre AS etiqueta, COUNT(a.id) AS total
            FROM cuadrillas c
            LEFT JOIN actividades a ON c.id = a.id_cuadrilla
            GROUP BY c.id, c.nombre
            ORDER BY total DESC, c.nombre
            """,
            fetchall=True,
        )
        by_estado_rows = self.db.execute(
            """
            SELECT estado AS etiqueta, COUNT(*) AS total
            FROM actividades
            GROUP BY estado
            ORDER BY total DESC
            """,
            fetchall=True,
        )
        return DashboardSummary(
            total_actividades=total_row["total"] if total_row else 0,
            por_cuadrilla=[ResumenItem(**row) for row in by_cuadrilla_rows],
            por_estado=[ResumenItem(**row) for row in by_estado_rows],
        )
