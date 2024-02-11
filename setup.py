"""Install missing modules"""

import pip


def import_or_install(module, package=None):
    """install module if unable to import"""
    if package is None:
        package = module
    try:
        __import__(module)
    except ImportError:
        pip.main(["install", package])


import_or_install("infisical_api")
import_or_install("kumpeapi")
