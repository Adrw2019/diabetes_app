import logging
import math
import os
import pickle

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect, render

APP_DIR = os.path.join(settings.BASE_DIR, "diabetes_app")
MODEL_PATH = os.path.join(APP_DIR, "model.pkl")
SCALER_PATH = os.path.join(APP_DIR, "scaler.pkl")


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


def calculate_dpf(pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, age):
    raw = (
        0.30
        + 0.0008 * glucose
        + 0.0020 * bmi
        + 0.0007 * age
        - 0.0005 * bloodpressure
        + 0.0003 * pregnancies
        + 0.0002 * skinthickness
        + 0.0004 * insulin
    )
    return max(0.01, min(0.99, raw))


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


def parse_input(request):
    pregnancies = float(request.POST.get("pregnancies", 0))
    glucose = float(request.POST.get("glucose", 0))
    bloodpressure = float(request.POST.get("bloodpressure", 0))
    skinthickness = float(request.POST.get("skinthickness", 0))
    insulin = float(request.POST.get("insulin", 0))
    bmi = float(request.POST.get("bmi", 0))
    age = float(request.POST.get("age", 0))
    return pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, age


def root(request):
    if request.user.is_authenticated:
        return redirect("diabetes_app:predict")
    return redirect("diabetes_app:login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("diabetes_app:predict")

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
    if request.user.is_authenticated:
        return redirect("diabetes_app:predict")

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
            pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, age = parse_input(request)
        except Exception:
            logging.exception("Error leyendo variables del formulario")
            return HttpResponse("Datos invalidos en el formulario", status=400)

        dpf = calculate_dpf(pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, age)
        features = [pregnancies, glucose, bloodpressure, skinthickness, insulin, bmi, dpf, age]

        probability = None
        model = safe_load(MODEL_PATH)
        scaler = safe_load(SCALER_PATH)

        try:
            if isinstance(model, tuple):
                possible_model = model[0] if len(model) > 0 else None
                possible_scaler = model[1] if len(model) > 1 else None
                if possible_model is not None:
                    model = possible_model
                if scaler is None and possible_scaler is not None:
                    scaler = possible_scaler

            if model is not None:
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
        except Exception:
            logging.exception("Error con modelo; se usa metodo manual")
            probability = None

        if probability is None:
            probability = manual_probability(*features)

        probability_percent = round(probability * 100, 1)
        has_risk = probability_percent >= 50.0

        context.update(
            {
                "show_result": True,
                "dpf": f"{dpf:.5f}",
                "probability": f"{probability_percent:.1f}",
                "has_risk": has_risk,
                "values": {
                    "pregnancies": f"{pregnancies:.1f}",
                    "glucose": f"{glucose:.1f}",
                    "bloodpressure": f"{bloodpressure:.1f}",
                    "skinthickness": f"{skinthickness:.1f}",
                    "insulin": f"{insulin:.1f}",
                    "bmi": f"{bmi:.1f}",
                    "age": f"{age:.1f}",
                    "dpf": f"{dpf:.5f}",
                },
            }
        )

    return render(request, "diabetes_app/predict_form.html", context)
