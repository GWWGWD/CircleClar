def recover(
    resolved_input,
    source_answer,
    task,
    prompts,
    model_config,
    judge_config,
    config,
    judge_temperature=0.0,
):
    samples = config["samples"]
    if samples < 1:
        raise ValueError("Recovery requires at least one sample.")

    reanswers = [
        task.reanswer(resolved_input, prompts, model_config, config["temperature"])
        for _ in range(samples)
    ]
    groups = task.group_answers(
        resolved_input, reanswers, prompts, judge_config, judge_temperature
    )
    for group in groups:
        group["count"] = len(group["member_indices"])
        group["frequency"] = group["count"] / samples

    top_count = max((group["count"] for group in groups), default=0)
    top_groups = [group for group in groups if group["count"] == top_count]
    top_frequency = top_count / samples
    if len(top_groups) != 1:
        return {
            "resolved_input": resolved_input,
            "source_answer": source_answer,
            "reanswers": reanswers,
            "groups": groups,
            "top_answer": None,
            "top_frequency": top_frequency,
            "source_agreement": {
                "score": False,
                "reason": "Top re-answer groups are tied." if groups else "No valid re-answer group.",
            },
            "accepted": False,
        }

    top_group = top_groups[0]
    top_answer = reanswers[top_group["member_indices"][0]]
    source_agreement = task.judge_consistency(
        resolved_input,
        source_answer,
        top_answer,
        prompts,
        judge_config,
        judge_temperature,
        answer_group=[reanswers[i] for i in top_group["member_indices"]],
    )

    accepted = (
        source_agreement["score"]
        and top_frequency >= config["threshold"]
    )
    return {
        "resolved_input": resolved_input,
        "source_answer": source_answer,
        "reanswers": reanswers,
        "groups": groups,
        "top_answer": top_answer,
        "top_frequency": top_frequency,
        "source_agreement": source_agreement,
        "accepted": accepted,
    }
