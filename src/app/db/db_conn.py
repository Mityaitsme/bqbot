from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# TODO: insert a real URL here
engine = create_engine(
  DATABASE_URL,
  pool_pre_ping=True,
)

SessionFactory = sessionmaker(bind=engine)


class DB:
  """
  Low-level DB access layer.
  Provides atomic operations via context-managed sessions.
  """

  @staticmethod
  @contextmanager
  def session() -> Generator[Session, None, None]:
    session = SessionFactory()
    try:
      yield session
      session.commit()
    except Exception:
      session.rollback()
      raise
    finally:
      session.close()

  @staticmethod
  def select(*, table: str, where: Dict[str, Any] | None = None,
             columns: str = "*") -> List[Dict[str, Any]]:
    """
    Makes a SELECT query to the database via SQLAlchemy
    """
    with DB.session() as session:
      sql = f"SELECT {columns} FROM {table}"
      params: Dict[str, Any] = {}

      if where:
        conditions = []
        for key, value in where.items():
          conditions.append(f"{key} = :{key}")
          params[key] = value
        sql += " WHERE " + " AND ".join(conditions)

      logger.debug(f"SQL SELECT: {sql} | params={params}")

      result = session.execute(text(sql), params)
      return [dict(row._mapping) for row in result]

  @staticmethod
  def insert(*, table: str, values: Dict[str, Any]) -> int:
    """
    Makes an INSERT query to the database via SQLAlchemy
    """
    with DB.session() as session:
      columns = ", ".join(values.keys())
      placeholders = ", ".join(f":{k}" for k in values.keys())
      sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"

      logger.debug(f"SQL INSERT: {sql} | values={values}")
      result = session.execute(text(sql), values)
      return result.scalar_one()

  @staticmethod
  def update(*, table: str, id: int, values: Dict[str, Any]) -> None:
    """
    Makes an UPDATE query to the database via SQLAlchemy
    """
    with DB.session() as session:
      assignments = ", ".join(f"{k} = :{k}" for k in values.keys())
      params = dict(values)
      params["id"] = id
      sql = f"UPDATE {table} SET {assignments} WHERE id = :id"

      logger.debug(f"SQL UPDATE: {sql} | values={params}")
      session.execute(text(sql), params)
