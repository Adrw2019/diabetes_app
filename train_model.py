"""
Entrena un modelo de clasificación de diabetes a partir del dataset Pima.
Genera diabetes_app/model.pkl con (model, scaler) para ser usado por la vista predict.
Uso:
    python train_model.py --csv diabetes.csv --out diabetes_app/model.pkl
"""

import argparse
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


FEATURE_ORDER = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
]


def load_and_clean(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df.copy()

    # Reemplaza ceros por NaN en variables que no pueden ser 0 fisiológicamente.
    zero_as_missing = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]
    for col in zero_as_missing:
        df[col] = df[col].replace(0, np.nan)
        df[col] = df[col].fillna(df[col].median())

    return df


def train_model(df: pd.DataFrame):
    X = df[FEATURE_ORDER]
    y = df["Outcome"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    numeric_features = FEATURE_ORDER
    preprocessor = ColumnTransformer(
        transformers=[("num", StandardScaler(), numeric_features)]
    )

    rf = RandomForestClassifier(
        n_estimators=400,
        random_state=42,
        class_weight="balanced",
        n_jobs=1,  # n_jobs>1 puede fallar en entornos con permisos limitados (Windows sandbox)
    )

    pipe = Pipeline(steps=[("scale", preprocessor), ("rf", rf)])
    pipe.fit(X_train, y_train)

    # Métricas de validación.
    proba = pipe.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)
    acc = accuracy_score(y_test, preds)
    roc = roc_auc_score(y_test, proba)

    # Reentrena sobre todo el dataset para exportar el modelo final.
    pipe.fit(X, y)

    # Extrae scaler y modelo para que la vista pueda usarlos.
    scaler = pipe.named_steps["scale"].named_transformers_["num"]
    model = pipe.named_steps["rf"]
    return model, scaler, acc, roc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Ruta al csv de entrenamiento")
    parser.add_argument(
        "--out", default="diabetes_app/model.pkl", help="Ruta de salida del PKL"
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_and_clean(csv_path)
    model, scaler, acc, roc = train_model(df)

    with open(out_path, "wb") as f:
        pickle.dump((model, scaler), f)

    print(f"Modelo guardado en {out_path}")
    print(f"Accuracy val: {acc:.3f}")
    print(f"ROC-AUC val: {roc:.3f}")


if __name__ == "__main__":
    main()
