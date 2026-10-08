from statistics import mean


def response_action(count):
    if count == 0:
        return "abstain"
    if count == 1:
        return "answer"
    return "clarify"


def set_metrics(matching):
    pairs = matching["answers"]
    prediction_count = sum(pair["prediction"] is not None for pair in pairs)
    reference_count = sum(pair["reference"] is not None for pair in pairs)
    matched_count = sum(
        pair["prediction"] is not None and pair["reference"] is not None
        for pair in pairs
    )
    total = prediction_count + reference_count

    return {
        "precision": (
            matched_count / prediction_count
            if prediction_count else float(reference_count == 0)
        ),
        "recall": matched_count / reference_count if reference_count else 1.0,
        "f1": 2 * matched_count / total if total else 1.0,
        "em": int(matched_count == prediction_count == reference_count),
        "ambiguity_score": prediction_count,
    }


def policy_actions(matching):
    return {
        side: response_action(sum(pair[side] is not None for pair in matching["answers"]))
        for side in ("prediction", "reference")
    }


def ambiguity_auroc(results):
    positive = [
        row["metrics"]["ambiguity_score"]
        for row in results if row["action"]["reference"] == "clarify"
    ]
    negative = [
        row["metrics"]["ambiguity_score"]
        for row in results if row["action"]["reference"] != "clarify"
    ]
    if not positive or not negative:
        return None
    wins = sum(
        (a > b) + 0.5 * (a == b)
        for a in positive for b in negative
    )
    return wins / (len(positive) * len(negative))


def policy_balanced_accuracy(results):
    recalls = []
    for action in ("abstain", "answer", "clarify"):
        correct = [
            row["action"]["prediction"] == action
            for row in results if row["action"]["reference"] == action
        ]
        if not correct:
            return None
        recalls.append(mean(correct))
    return float(mean(recalls))


def summarize(results):
    if not results:
        raise ValueError("Evaluation requires at least one question.")
    metrics = [row["metrics"] for row in results]
    return {
        "questions": len(metrics),
        **{
            name: float(mean(row[name] for row in metrics))
            for name in ("precision", "recall", "f1", "em")
        },
        "ambiguity_auroc": ambiguity_auroc(results),
        "balanced_accuracy": policy_balanced_accuracy(results),
    }
