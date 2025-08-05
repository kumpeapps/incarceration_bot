"""Insert ignore helper for SQLAlchemy."""
from sqlalchemy import insert
from sqlalchemy.orm import Session


def insert_ignore(
    session: Session, model, values, auto_commit: bool = False
):
    """Insert ignore helper for SQLAlchemy."""
    engine = session.get_bind()
    if engine.dialect.name == "sqlite":
        stmt = insert(model).prefix_with("OR IGNORE")
        session.execute(stmt, values)
    elif engine.dialect.name == "mysql":
        stmt = insert(model).prefix_with("IGNORE")
        session.execute(stmt, values)
    else:
        raise NotImplementedError(
            f"Insert ignore not implemented for dialect {engine.dialect.name}"
        )
    if auto_commit:
        session.commit()
