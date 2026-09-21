"""Notification, email-bridge and placeholder support.

This package is intentionally import-light: importing it must never touch the
database. Placeholder rendering happens lazily at render time.
"""
