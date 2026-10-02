import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.classify.data import generate_dataset, CATEGORIES
from core.classify.train import train_classifier, evaluate, predict


def test_generate_dataset_has_correct_category_balance():
    rows = generate_dataset(per_category=10, seed=1)
    assert len(rows) == 10 * len(CATEGORIES)

    from collections import Counter
    counts = Counter(cat for _, cat in rows)
    for category in CATEGORIES:
        assert counts[category] == 10


def test_generate_dataset_is_reproducible_with_same_seed():
    rows_a = generate_dataset(per_category=10, seed=7)
    rows_b = generate_dataset(per_category=10, seed=7)
    assert rows_a == rows_b


def test_train_classifier_produces_a_working_model():
    rows = generate_dataset(per_category=25, seed=42)
    texts = [t for t, _ in rows]
    labels = [c for _, c in rows]

    trained = train_classifier(texts, labels)
    result = evaluate(trained, split="test")

    assert 0.0 <= result["macro_f1"] <= 1.0


def test_predict_returns_a_known_category_with_plain_types():
    rows = generate_dataset(per_category=25, seed=42)
    texts = [t for t, _ in rows]
    labels = [c for _, c in rows]
    trained = train_classifier(texts, labels)

    result = predict(trained, "The api-gateway keeps returning connection timeouts.")

    assert result["category"] in CATEGORIES
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["category"], str)
    assert isinstance(result["confidence"], float)


if __name__ == "__main__":
    print("run with: pytest tests/test_classify.py -v")
