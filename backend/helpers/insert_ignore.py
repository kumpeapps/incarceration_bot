"""Insert ignore helper for SQLAlchemy."""
from sqlalchemy import insert, text
from sqlalchemy.orm import Session
from datetime import datetime


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


def upsert_inmate(session: Session, inmate_data: dict, auto_commit: bool = False):
    """
    Insert inmate or update last_seen if duplicate exists.
    Uses MySQL's ON DUPLICATE KEY UPDATE for performance.
    Works with current unique constraint: name, race, dob, sex, hold_reasons, in_custody_date, release_date, jail_id
    """
    engine = session.get_bind()
    if engine.dialect.name == "mysql":
        # Use raw SQL for ON DUPLICATE KEY UPDATE
        sql = text("""
            INSERT INTO inmates (
                name, race, sex, cell_block, arrest_date, held_for_agency, 
                mugshot, dob, hold_reasons, is_juvenile, release_date, 
                in_custody_date, jail_id, hide_record, last_seen
            ) VALUES (
                :name, :race, :sex, :cell_block, :arrest_date, :held_for_agency,
                :mugshot, :dob, :hold_reasons, :is_juvenile, :release_date,
                :in_custody_date, :jail_id, :hide_record, :last_seen
            )
            ON DUPLICATE KEY UPDATE
                last_seen = VALUES(last_seen),
                cell_block = VALUES(cell_block),
                arrest_date = VALUES(arrest_date),
                held_for_agency = VALUES(held_for_agency),
                mugshot = VALUES(mugshot)
        """)
        
        # Ensure last_seen is set to current time
        if 'last_seen' not in inmate_data or inmate_data['last_seen'] is None:
            inmate_data['last_seen'] = datetime.now()
            
        session.execute(sql, inmate_data)
    else:
        # Fallback to regular insert_ignore for non-MySQL
        insert_ignore(session, model=None, values=inmate_data, auto_commit=False)
    
    if auto_commit:
        session.commit()
