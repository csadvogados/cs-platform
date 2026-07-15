import logging

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger("cs_platform.database")


def initialize_database() -> None:
    """
    Inicializa o schema do banco de forma segura e idempotente.
    Cria apenas tabelas inexistentes e preserva os dados já existentes.
    """
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")

        existing_before = set(inspect(engine).get_table_names())
        logger.info(
            "Banco conectado. Tabelas existentes antes da inicialização: %s",
            sorted(existing_before),
        )

        Base.metadata.create_all(bind=engine, checkfirst=True)

        existing_after = set(inspect(engine).get_table_names())
        created_tables = sorted(existing_after - existing_before)

        if created_tables:
            logger.info("Tabelas criadas: %s", created_tables)
        else:
            logger.info("Nenhuma tabela nova precisou ser criada.")

        if "organizations" not in existing_after:
            raise RuntimeError(
                "A tabela 'organizations' não foi criada. "
                "Verifique se todos os modelos são importados por app.models."
            )

    except SQLAlchemyError as exc:
        logger.exception("Falha SQLAlchemy durante a inicialização do banco.")
        raise RuntimeError("Não foi possível inicializar o banco de dados.") from exc
