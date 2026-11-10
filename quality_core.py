"""Small, independently testable helpers for the submission audit."""
from collections import Counter

LABELS = ("Accelerating", "Steady", "Slowing")


def market_consensus(labels):
    """Preserve the team's rule, including its conservative split convention."""
    counts = Counter(x for x in labels if x in LABELS)
    if not counts:
        return "Insufficient", ""
    top = [x for x, n in counts.items() if n == max(counts.values())]
    split = counts.get("Accelerating", 0) == counts.get("Slowing", 0) > 0
    label = "Steady" if len(top) > 1 or split else top[0]
    confidence = "high" if max(counts.values()) / sum(counts.values()) >= .75 and len(top) == 1 else "low"
    return label, confidence


def classification_metrics(actual, predicted):
    """Score only valid pairs; absent classes have undefined recall, not zero."""
    actual, predicted = list(actual), list(predicted)
    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted labels must have equal lengths")
    pairs = [(a, p) for a, p in zip(actual, predicted) if a in LABELS and p in LABELS]
    recalls, details = [], []
    for label in LABELS:
        support = sum(a == label for a, _ in pairs)
        called = sum(p == label for _, p in pairs)
        correct = sum(a == p == label for a, p in pairs)
        recall = correct / support if support else None
        if recall is not None:
            recalls.append(recall)
        details.append(dict(label=label, actual_count=support, predicted_count=called,
                            true_positive=correct, precision=correct / called if called else None,
                            recall=recall))
    n = len(pairs)
    return dict(n=n, correct=sum(a == p for a, p in pairs),
                accuracy=sum(a == p for a, p in pairs) / n if n else None,
                balanced_accuracy=sum(recalls) / len(recalls) if recalls else None,
                classes_present=len(recalls), details=details)
