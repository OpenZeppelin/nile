try:
    from importlib import metadata as importlib_metadata
except ImportError:
    import importlib_metadata  # python < 3.8


def version_command():
    nile_version = importlib_metadata.version("cairo-nile")
    print(nile_version)
