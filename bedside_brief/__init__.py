"""Bedside Brief — deterministic half of the pipeline (store, retrieve, render, validate, bayes).

No module in this package makes an LLM call. The package logger writes to stdout only.
"""
from __future__ import annotations

import logging
import sys

__version__ = "0.1.0"

_log = logging.getLogger("bedside_brief")
if not _log.handlers:  # stdout only; never a file
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    _log.addHandler(_handler)
    _log.setLevel(logging.INFO)
