-- Orden estable del listado de reservas, incluido el desempate entre salas.
CREATE INDEX IF NOT EXISTS reservas_orden_inicio_id ON reservas(inicio DESC,id DESC);
