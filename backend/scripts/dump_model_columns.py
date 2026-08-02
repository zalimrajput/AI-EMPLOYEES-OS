"""Dump all SQLAlchemy model tables, columns, and nullability."""
import importlib
import os
import sys

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ".")

import app.models as models_mod  # noqa: E402

for name in sorted(models_mod.__all__):
    cls = getattr(models_mod, name)
    if not hasattr(cls, "__table__"):
        continue
    cols = []
    for c in cls.__table__.columns:
        nullable = "NULL" if c.nullable else "NOT NULL"
        default = " default" if c.default is not None or c.server_default is not None else ""
        fk = f" FK={list(c.foreign_keys)[0].target_fullname}" if c.foreign_keys else ""
        cols.append(f"{c.name}:{nullable}{default}{fk}")
    print(f"{cls.__tablename__} ({name}):")
    for col in cols:
        print(f"    {col}")
