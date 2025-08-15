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
    OPTIMIZED: Insert inmate or update last_seen only if significantly different.
    Uses MySQL's ON DUPLICATE KEY UPDATE with conditional logic to reduce binlog bloat.
    Works with current unique constraint: name, race, dob, sex, arrest_date, jail_id
    
    OPTIMIZATION: Only updates last_seen if more than 1 hour has passed since last update.
    This dramatically reduces MariaDB binlog writes.
    """
    engine = session.get_bind()
    if engine.dialect.name == "mysql":
        # OPTIMIZED: Use conditional UPDATE to avoid unnecessary writes
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
                -- OPTIMIZATION: Only update last_seen if NULL or more than 1 hour old
                last_seen = CASE 
                    WHEN last_seen IS NULL OR last_seen < DATE_SUB(NOW(), INTERVAL 1 HOUR)
                    THEN VALUES(last_seen)
                    ELSE last_seen
                END,
                -- Always update these fields as they may have legitimately changed
                cell_block = VALUES(cell_block),
                arrest_date = VALUES(arrest_date),
                held_for_agency = VALUES(held_for_agency),
                mugshot = VALUES(mugshot),
                in_custody_date = VALUES(in_custody_date),
                release_date = VALUES(release_date),
                hold_reasons = VALUES(hold_reasons)
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
