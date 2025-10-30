"""Command modules for tfkit CLI."""

# Lazy imports to avoid circular dependencies
__all__ = ["scan", "validate", "export", "examples"]


def __getattr__(name):
    """Lazy load commands to avoid circular imports."""
    if name == "scan":
        from .scan import scan

        return scan
    elif name == "validate":
        from .validate import validate

        return validate
    elif name == "export":
        from .export import export

        return export
    elif name == "examples":
        from .examples import examples

        return examples
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
