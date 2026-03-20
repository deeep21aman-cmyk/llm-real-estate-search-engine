"""Expose the existing top-level `app` package as `RealtorDR.app`."""

from pathlib import Path


__path__ = [str(Path(__file__).resolve().parents[2] / "app")]
