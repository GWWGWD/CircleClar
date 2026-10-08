def match_predictions(
    original_input,
    predicted_answers,
    reference_groups,
    task,
    prompts,
    judge_config,
    judge_temperature=0.0,
):
    answers = list(dict.fromkeys(
        answer for answer in predicted_answers
        if answer.strip().casefold() != "unknown"
    ))
    groups = task.group_answers(
        original_input, answers, prompts, judge_config, judge_temperature
    )
    references = [
        {"group_id": group["group_id"], "answers": group["answers"]}
        for group in reference_groups
    ]

    remaining = {group["group_id"]: group["answers"][0] for group in references}
    pairs = []
    for index, group in enumerate(groups):
        prediction = {
            "group_id": f"P{index + 1}",
            "answers": [answers[i] for i in sorted(group["member_indices"])],
        }
        match = task.match_reference(
            original_input,
            prediction,
            references,
            prompts,
            judge_config,
            judge_temperature,
        )
        pairs.append({
            "prediction": prediction["answers"][0],
            "reference": remaining.pop(match["group_id"], None),
        })
    pairs.extend(
        {"prediction": None, "reference": answer}
        for answer in remaining.values()
    )

    return {
        "input": original_input,
        "answers": pairs,
    }
