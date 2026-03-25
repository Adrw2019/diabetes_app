#!/usr/bin/env python
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[0].parent
sys.path.append(str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth.models import User  # noqa: E402

TEST_USERS = [
    {"username": "usuario1", "email": "usuario1@example.com", "password": "Pass1234!"},
    {"username": "usuario2", "email": "usuario2@example.com", "password": "Pass1234!"},
    {"username": "usuario3", "email": "usuario3@example.com", "password": "Pass1234!"},
]

for data in TEST_USERS:
    obj, created = User.objects.get_or_create(username=data["username"], defaults=data)
    if created:
        print(f"Creado {obj.username} ({obj.email})")
    else:
        print(f"Ya existe {obj.username}")
