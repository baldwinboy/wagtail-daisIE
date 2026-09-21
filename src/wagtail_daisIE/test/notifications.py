"""Importable callables used by the notification bridge tests."""


def fixed_recipients(source):
    return ["bridge@example.com"]


def title_context(source):
    if isinstance(source, dict) and source.get("name"):
        return {"name": source["name"]}
    return {"name": "World"}
