# plugins/__init__.py

# This makes the plugins folder a Python package.
# Optionally, you can auto-import or auto-start plugins here.

# Example: auto-start keep-alive when importing the package
try:
    from .keep_alive import start as _start_keep_alive
    import asyncio
    _start_keep_alive(asyncio.get_event_loop())
except Exception as e:
    import logging
    logging.warning(f"Keep-alive plugin failed to start: {e}")
