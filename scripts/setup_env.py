#!/usr/bin/env python
"""Genera un .env real a partir de .env.example pidiéndote los valores sensibles."""

import getpass
import pathlib
import secrets


def prompt(prompt_text, default=None, hide_input=False):
    suffix = f" [{default}]" if default else ""
    prompt_full = f"{prompt_text}{suffix}: "
    if hide_input:
        value = getpass.getpass(prompt_full)
    else:
        value = input(prompt_full)
    return value.strip() or default or ""


def main():
    example_path = pathlib.Path(".env.example")
    if not example_path.exists():
        raise SystemExit(".env.example no existe. Crea primero con los valores base.")

    print("Generar archivo .env (los valores sensibles no se guardan en Git). Pulsa ENTER para usar el valor entre corchetes.")

    secret_key = prompt(
        "SECRET_KEY (deja vacío para generar una clave segura auto)", None, hide_input=True
    )
    if not secret_key:
        secret_key = secrets.token_urlsafe(50)
        print(f"Se generó SECRET_KEY automática: {secret_key}")

    allowed_hosts = prompt(
        "ALLOWED_HOSTS (coma separado)", "diabetes-app-eby0.onrender.com,localhost,127.0.0.1"
    )
    database_url = prompt(
        "DATABASE_URL (postgres://usuario:clave@host:puerto/bd)", "postgres://usuario:clave@localhost:5432/diabetes_app"
    )

    print("\nConfigura el correo SMTP (usa Gmail si no sabes qué poner).")
    email_host = prompt("EMAIL_HOST", "smtp.gmail.com")
    email_port = prompt("EMAIL_PORT", "587")
    email_use_tls = prompt("EMAIL_USE_TLS [True/False]", "True")
    email_use_ssl = prompt("EMAIL_USE_SSL [True/False]", "False")
    email_host_user = prompt("EMAIL_HOST_USER (tu correo)", "tu_cuenta@gmail.com")
    email_host_password = prompt("EMAIL_HOST_PASSWORD (app password)", hide_input=True)
    default_from_email = prompt("DEFAULT_FROM_EMAIL", email_host_user)

    password_reset_domain = prompt("PASSWORD_RESET_DOMAIN_OVERRIDE", "diabetes-app-eby0.onrender.com")
    password_reset_protocol = prompt("PASSWORD_RESET_PROTOCOL_OVERRIDE", "https")

    content = [
        "# Django",
        f"SECRET_KEY={secret_key}",
        "DEBUG=False",
        f"ALLOWED_HOSTS={allowed_hosts}",
        "",
        "# Base de datos persistente (Postgres)",
        f"DATABASE_URL={database_url}",
        "",
        "# SMTP (elige un proveedor y rellena)",
        "EMAIL_HOST=" + email_host,
        "EMAIL_PORT=" + email_port,
        "EMAIL_USE_TLS=" + email_use_tls,
        "EMAIL_USE_SSL=" + email_use_ssl,
        "EMAIL_HOST_USER=" + email_host_user,
        "EMAIL_HOST_PASSWORD=" + email_host_password,
        "DEFAULT_FROM_EMAIL=" + default_from_email,
        "",
        "# Password reset links",
        f"PASSWORD_RESET_DOMAIN_OVERRIDE={password_reset_domain}",
        f"PASSWORD_RESET_PROTOCOL_OVERRIDE={password_reset_protocol}",
    ]

    target_path = pathlib.Path(".env")
    target_path.write_text("\n".join(content) + "\n")
    print(f"\nArchivo {target_path} generado. No lo subas al repositorio.")


if __name__ == "__main__":
    main()
