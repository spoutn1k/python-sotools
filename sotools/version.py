PACKAGE = "python-sotools"
VERSION = (0, 1, 0)
RELEASE_CANDIDATE = 0
__version__ = '.'.join(map(
    str, VERSION)) + (f"rc{RELEASE_CANDIDATE}" if RELEASE_CANDIDATE else '')
