import logging

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger("cs_platform.database")


def initialize_database() -> None:
    """
    Verifica a conexão e garante uma inicialização segura.

    Em produção, o schema deve ser criado pelas migrations do Alembic
    executadas no pre-deploy. Em desenvolvimento e teste, create_all
    continua disponível como fallback.
    """
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")

        existing_tables = set(inspect(engine).get_table_names())
        logger.info("Banco conectado. Tabelas existentes: %s", sorted(existing_tables))

        if not existing_tables:
            logger.warning(
                "Nenhuma tabela encontrada. O Alembic deveria ter sido executado "
                "no pre-deploy."
            )

        if "organizations" not in existing_tables:
            logger.warning(
                "Tabela organizations ausente após o pre-deploy."
            )

    except SQLAlchemyError as exc:
        logger.exception("Falha durante a verificação do banco.")
        raise RuntimeError("Não foi possível validar o banco de dados.") from exc
