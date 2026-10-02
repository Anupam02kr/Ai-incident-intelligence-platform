import csv
import pickle

import numpy as np
import xgboost as xgb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


def load_dataset(path):
    texts, labels = [], []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"])
            labels.append(row["category"])
    return texts, labels


def train_classifier(texts, labels, test_size=0.15, val_size=0.15, random_state=42):
    """Splits the data 70/15/15 (train/val/test, matching the SRS), fits
    a TF-IDF vectorizer + XGBoost classifier, and returns everything
    needed to evaluate and reuse it. val isn't used for hyperparameter
    tuning here since the dataset's small - it's there so future tuning
    has a set to check against without touching test.
    """
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(labels)

    X_temp, X_test, y_temp, y_test = train_test_split(
        texts, y, test_size=test_size, random_state=random_state, stratify=y
    )
    val_fraction_of_remaining = val_size / (1 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_fraction_of_remaining,
        random_state=random_state, stratify=y_temp
    )

    vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2), stop_words="english")
    X_train_vec = vectorizer.fit_transform(X_train)
    X_val_vec = vectorizer.transform(X_val)
    X_test_vec = vectorizer.transform(X_test)

    model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=len(label_encoder.classes_),
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        eval_metric="mlogloss",
        random_state=random_state,
    )
    model.fit(X_train_vec, y_train)

    return {
        "model": model,
        "vectorizer": vectorizer,
        "label_encoder": label_encoder,
        "splits": {
            "X_train": X_train, "y_train": y_train,
            "X_val": X_val, "y_val": y_val,
            "X_test": X_test, "y_test": y_test,
        },
    }


def evaluate(trained, split="test"):
    """Runs the model against a given split and returns macro F1 plus a
    full per-class report. Defaults to test since that's what NFR-3
    actually measures against, but val is handy for a quick sanity check
    during development.
    """
    model = trained["model"]
    vectorizer = trained["vectorizer"]
    label_encoder = trained["label_encoder"]
    splits = trained["splits"]

    X = splits[f"X_{split}"]
    y_true = splits[f"y_{split}"]

    X_vec = vectorizer.transform(X)
    y_pred = model.predict(X_vec)

    macro_f1 = f1_score(y_true, y_pred, average="macro")
    report = classification_report(
        y_true, y_pred, target_names=label_encoder.classes_, zero_division=0
    )

    return {"macro_f1": macro_f1, "report": report}


def predict(trained, text):
    """Classifies a single piece of text, returns the predicted category
    plus a confidence score - this is what FR-19 wants (category +
    confidence).
    """
    vectorizer = trained["vectorizer"]
    model = trained["model"]
    label_encoder = trained["label_encoder"]

    X_vec = vectorizer.transform([text])
    probs = model.predict_proba(X_vec)[0]
    predicted_idx = int(np.argmax(probs))

    return {
        "category": str(label_encoder.classes_[predicted_idx]),
        "confidence": round(float(probs[predicted_idx]), 3),
    }


def save_trained(trained, path):
    """Saves the model + vectorizer + label encoder together so they can
    be loaded later without retraining. Doesn't save the train/val/test
    splits since those are only needed during evaluation, not inference.
    """
    to_save = {
        "model": trained["model"],
        "vectorizer": trained["vectorizer"],
        "label_encoder": trained["label_encoder"],
    }
    with open(path, "wb") as f:
        pickle.dump(to_save, f)


def load_trained(path):
    with open(path, "rb") as f:
        return pickle.load(f)


if __name__ == "__main__":
    texts, labels = load_dataset("eval/incident_dataset.csv")
    print(f"loaded {len(texts)} incidents")

    trained = train_classifier(texts, labels)

    val_result = evaluate(trained, split="val")
    print(f"\nvalidation macro F1: {val_result['macro_f1']:.3f}")

    test_result = evaluate(trained, split="test")
    print(f"\ntest macro F1: {test_result['macro_f1']:.3f}")
    print(f"\n{test_result['report']}")

    save_trained(trained, "eval/classifier.pkl")
    print("saved model to eval/classifier.pkl")

    sample = "The payment-service is returning 500 errors after last night's deploy."
    result = predict(trained, sample)
    print(f"\nsample prediction: '{sample}'")
    print(f"  -> {result}")
