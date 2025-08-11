"""
Shared Alembic utilities for both maintenance and initialization
"""
import subprocess
import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

def _run_alembic(cmd_args: List[str], *, info_msg: Optional[str] = None, err_prefix: Optional[str] = None) -> Optional[str]:
    """
    Run "alembic <cmd_args…>" and return stdout on success, or None on failure.
    
    Args:
        cmd_args: List of command arguments to pass to alembic
        info_msg: Optional info message to log before running
        err_prefix: Optional prefix for error messages
        
    Returns:
        stdout on success, None on failure
    """
    try:
        if info_msg:
            logger.info(info_msg)
        res = subprocess.run(
            ['alembic'] + cmd_args,
            capture_output=True, text=True, cwd=os.getcwd(),
            check=False
        )
        if res.returncode != 0:
            logger.error("%s %s failed: %s", err_prefix or 'alembic', cmd_args[0], res.stderr.strip())
            return None
        return res.stdout.strip()
    except (subprocess.SubprocessError, OSError) as e:
        logger.error("%s %s exception: %s", err_prefix or 'alembic', cmd_args[0], e)
        return None

def check_multiple_heads() -> tuple[bool, List[str]]:
    """
    Check if there are multiple Alembic heads.
    
    Returns:
        (has_multiple_heads, list_of_heads)
    """
    heads_out = _run_alembic(['heads'], err_prefix="check heads")
    if heads_out is None:
        return False, []
    
    heads = [line.strip() for line in heads_out.splitlines() if line.strip()]
    return len(heads) > 1, heads

def merge_heads_safely(allow_auto_merge: bool = False) -> bool:
    """
    Merge multiple Alembic heads if they exist.
    
    Args:
        allow_auto_merge: If True, automatically merge heads. If False, just log warning.
        
    Returns:
        True if merge was successful or no merge needed, False if failed
    """
    has_multiple, heads = check_multiple_heads()
    
    if not has_multiple:
        logger.info("Only one head found – no merge needed")
        return True
    
    if not allow_auto_merge:
        logger.warning("Multiple heads detected (%d heads) but auto-merge is disabled", len(heads))
        logger.warning("Please resolve manually:")
        logger.warning("  docker-compose exec backend_api alembic merge -m 'merge heads' heads")
        logger.warning("  docker-compose exec backend_api alembic upgrade head")
        return False
    
    logger.info("Merging %d heads automatically...", len(heads))
    
    merge_out = _run_alembic(
        ['merge', '-m', 'auto merge conflicting heads during startup', 'heads'],
        info_msg="Merging %d heads..." % len(heads),
        err_prefix="merge heads"
    )
    if merge_out is None:
        return False
    
    logger.info("Merge migration created: %s", merge_out)
    
    # Upgrade to the merged head
    upgrade_out = _run_alembic(['upgrade', 'head'],
                              info_msg="Upgrading to merged head...",
                              err_prefix="upgrade after merge")
    return upgrade_out is not None

def get_current_revision() -> Optional[str]:
    """Get the current database revision."""
    current_out = _run_alembic(['current'], err_prefix="get current revision")
    if current_out is None:
        return None
    
    # Extract revision hash from output
    lines = [line.strip() for line in current_out.splitlines() if line.strip()]
    if lines:
        # Usually format is "revision_hash (head)" or just "revision_hash"
        return lines[0].split()[0] if lines[0] else None
    return None

def show_migration_history() -> bool:
    """Show migration history."""
    hist = _run_alembic(['history'],
                       info_msg="Showing migration history...",
                       err_prefix="show history")
    if hist is None:
        return False
    
    print("Migration history:\n", hist)
    return True
