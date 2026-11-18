"""Runtime Tailwind CSS compilation for ``wagtail-daisIE``."""

from .compiler import (
    TailwindCompilationError,
    build_input_stylesheet,
    compile_classnames,
    compile_input_stylesheet,
    extract_class_names,
)
from .placeholder import (
    JIT_CONFIG_ID,
    JIT_PLACEHOLDER_ID,
    inject_config,
    placeholder_html,
)


__all__ = [
    "JIT_CONFIG_ID",
    "JIT_PLACEHOLDER_ID",
    "TailwindCompilationError",
    "build_input_stylesheet",
    "compile_classnames",
    "compile_input_stylesheet",
    "extract_class_names",
    "inject_config",
    "placeholder_html",
]
