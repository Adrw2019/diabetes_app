import logging
import math
import os
import pickle
from functools import lru_cache

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.html import strip_tags

APP_DIR = os.path.join(settings.BASE_DIR, "diabetes_app")
MODEL_PATH = os.path.join(APP_DIR, "model.pkl")
SCALER_PATH = os.path.join(APP_DIR, "scaler.pkl")

DPF_MIN = 0.078
DPF_MAX = 2.42


def safe_load(path):
    try:
        if not os.path.exists(path):
            logging.error("Archivo no encontrado: %s", path)
            return None
        if os.path.getsize(path) == 0:
            logging.error("Archivo vacio: %s", path)
            return None
        with open(path, "rb") as file_obj:
            return pickle.load(file_obj)
    except Exception:
        logging.exception("Error cargando pickle: %s", path)
        return None


def manual_probability(pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, dpf, age):
    score = (
        -9.70
        + 0.040 * glucose
        + 0.070 * bmi
        + 0.030 * age
        + 0.010 * pregnancies
        + 0.005 * skinthickness
        + 0.001 * insulin
        + 0.005 * bloodpressure
        + 0.350 * dpf
    )
    probability = 1.0 / (1.0 + math.exp(-score))
    return max(0.0, min(1.0, probability))


@lru_cache(maxsize=1)
def load_model_and_scaler():
    """
    Carga y normaliza artefactos (model.pkl, scaler.pkl).
    Usa cache en memoria para no leer disco en cada request.
    Permite que model.pkl sea un tuple (model, scaler) como a veces guarda sklearn.
    """
    model = safe_load(MODEL_PATH)
    scaler = safe_load(SCALER_PATH)

    if isinstance(model, tuple):
        possible_model = model[0] if len(model) > 0 else None
        possible_scaler = model[1] if len(model) > 1 else None
        if possible_model is not None:
            model = possible_model
        if scaler is None and possible_scaler is not None:
            scaler = possible_scaler

    return model, scaler


def normalize_unit(value, min_value, max_value):
    if max_value <= min_value:
        return 0.0
    clamped = max(min(value, max_value), min_value)
    return (clamped - min_value) / (max_value - min_value)


def derive_dpf(pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, age):
    weights = [
        (glucose, 44, 199, 0.30),
        (bmi, 18.2, 67.1, 0.25),
        (age, 18, 90, 0.20),
        (insulin, 14, 846, 0.10),
        (skinthickness, 7, 99, 0.05),
        (bloodpressure, 24, 122, 0.05),
        (pregnancies, 0, 17, 0.05),
    ]
    score = sum(weight * normalize_unit(value, min_value, max_value) for value, min_value, max_value, weight in weights)
    return DPF_MIN + score * (DPF_MAX - DPF_MIN)


def parse_input(request):
    pregnancies = float(request.POST.get("pregnancies", 0))
    glucose = float(request.POST.get("glucose", 0))
    bloodpressure = float(request.POST.get("bloodpressure", 0))
    skinthickness = float(request.POST.get("skinthickness", 0))
    insulin = float(request.POST.get("insulin", 0))
    bmi = float(request.POST.get("bmi", 0))
    age = float(request.POST.get("age", 0))
    source_confirmed = request.POST.get("source_confirmed") == "on"
    dpf = derive_dpf(pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, age)
    return pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, dpf, age, source_confirmed


def validate_ranges(pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, dpf, age):
    return (
        0 <= pregnancies <= 17  # máximo observado en el dataset Pima
        and 44 <= glucose <= 199
        and 24 <= bloodpressure <= 122
        and 7 <= skinthickness <= 99
        and 14 <= insulin <= 846
        and 18.2 <= bmi <= 67.1
        and 0.078 <= dpf <= 2.42
        and 18 <= age <= 90
    )


def consistency_issues(glucose, skinthickness, insulin, bmi, dpf):
    issues = []
    if bmi > 50 and skinthickness < 10:
        issues.append("BMI muy alto con grosor de piel muy bajo.")
    if glucose > 180 and insulin < 30:
        issues.append("Glucosa muy alta con insulina muy baja.")
    if insulin > 500 and glucose < 70:
        issues.append("Insulina muy alta con glucosa muy baja.")
    if dpf > 2.0:
        issues.append("DPF demasiado alto, valida el dato.")
    return issues


def root(request):
    return redirect("diabetes_app:login")


class CustomPasswordResetView(PasswordResetView):
    """Permite fijar dominio/protocolo en los enlaces por red local o staging."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        fixed_domain = getattr(settings, "PASSWORD_RESET_DOMAIN_OVERRIDE", "")
        if fixed_domain:
            kwargs["domain_override"] = fixed_domain
        fixed_protocol = getattr(settings, "PASSWORD_RESET_PROTOCOL_OVERRIDE", "")
        if fixed_protocol in {"http", "https"}:
            kwargs["use_https"] = fixed_protocol == "https"
        return kwargs


def send_welcome_email(user):
    """Envía un correo de bienvenida; no interrumpe el registro si falla."""
    try:
        context = {"username": user.username}
        html_message = render_to_string("diabetes_app/emails/welcome_email.html", context)
        plain_message = strip_tags(html_message)
        send_mail(
            subject="Bienvenido a Diabetes App",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception:
        logging.exception("No se pudo enviar el correo de bienvenida")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, "Usuario o contrasena incorrectos.")
        else:
            login(request, user)
            return redirect("diabetes_app:predict")

    return render(request, "diabetes_app/login.html")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username or not email or not password:
            messages.error(request, "Completa todos los campos.")
        elif password != confirm_password:
            messages.error(request, "Las contrasenas no coinciden.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "El usuario ya existe.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Ese correo ya esta registrado.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            send_welcome_email(user)
            login(request, user)
            return redirect("diabetes_app:predict")

    return render(request, "diabetes_app/register.html")


def logout_view(request):
    logout(request)
    return redirect("diabetes_app:login")


@login_required(login_url="diabetes_app:login")
def predict(request):
    context = {
        "values": {
            "pregnancies": "",
            "glucose": "",
            "bloodpressure": "",
            "skinthickness": "",
            "insulin": "",
            "bmi": "",
            "age": "",
            "dpf": "",
        },
        "show_result": False,
    }

    if request.method == "POST":
        try:
            pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, dpf, age, source_confirmed = parse_input(request)
        except Exception:
            logging.exception("Error leyendo variables del formulario")
            return HttpResponse("Datos invalidos en el formulario", status=400)

        current_values = {
            "pregnancies": f"{pregnancies:.1f}",
            "glucose": f"{glucose:.1f}",
            "bloodpressure": f"{bloodpressure:.1f}",
            "skinthickness": f"{skinthickness:.1f}",
            "insulin": f"{insulin:.1f}",
            "bmi": f"{bmi:.1f}",
            "age": f"{age:.1f}",
            "dpf": f"{dpf:.5f}",
            "source_confirmed": source_confirmed,
        }

        if not source_confirmed:
            messages.error(request, "Debes confirmar que los datos vienen de una fuente real (laboratorio/medicion).")
            context["values"] = current_values
            return render(request, "diabetes_app/predict_form.html", context)

        if not validate_ranges(pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, dpf, age):
            messages.error(
                request,
                "Verifica rangos reales (segun dataset Pima y criterio clinico): Embarazos 0-17, Glucosa 44-199, Presion 24-122, "
                "Skin 7-99, Insulina 14-846, BMI 18.2-67.1, DPF 0.078-2.42, Edad 18-90.",
            )
            context["values"] = current_values
            return render(request, "diabetes_app/predict_form.html", context)

        issues = consistency_issues(glucose, skinthickness, insulin, bmi, dpf)
        if issues:
            messages.error(request, "Datos sospechosos: " + " | ".join(issues))
            context["values"] = current_values
            return render(request, "diabetes_app/predict_form.html", context)

        features = [pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, dpf, age]

        probability = None
        model_source = "manual_formula"
        model, scaler = load_model_and_scaler()

        try:
            if model is not None:
                model_source = getattr(model, "__class__", type("obj", (), {})).__name__ or "model.pkl"
                x_data = [features]
                if scaler is not None:
                    try:
                        x_data = scaler.transform(x_data)
                    except Exception:
                        logging.exception("Error aplicando scaler; se usara X sin transformar")

                if hasattr(model, "predict_proba"):
                    probability = float(model.predict_proba(x_data)[0][1])
                else:
                    prediction = int(model.predict(x_data)[0])
                    probability = 0.75 if prediction == 1 else 0.05
            else:
                logging.warning("model.pkl/scaler.pkl no encontrados; usando formula manual.")
        except Exception:
            logging.exception("Error con modelo; se usa metodo manual")
            probability = None

        if probability is None:
            probability = manual_probability(*features)
            model_source = "manual_formula"

        probability_percent = round(probability * 100, 1)
        has_risk = probability_percent >= 50.0

        context.update(
            {
                "show_result": True,
                "dpf": f"{dpf:.5f}",
                "probability": f"{probability_percent:.1f}",
                "has_risk": has_risk,
                "model_source": model_source,
                "values": {
                    "pregnancies": f"{pregnancies:.1f}",
                    "glucose": f"{glucose:.1f}",
                    "bloodpressure": f"{bloodpressure:.1f}",
                    "skinthickness": f"{skinthickness:.1f}",
                    "insulin": f"{insulin:.1f}",
                    "bmi": f"{bmi:.1f}",
                    "age": f"{age:.1f}",
                    "dpf": f"{dpf:.5f}",
                    "source_confirmed": source_confirmed,
                },
            }
        )

    return render(request, "diabetes_app/predict_form.html", context)
