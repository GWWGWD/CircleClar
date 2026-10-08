from ..recovery import recover


def build_reference(
    original_input,
    resolved_inputs,
    reference_answers,
    task,
    prompts,
    model_config,
    judge_config,
    config,
    judge_temperature=0.0,
):
    pairs = list(zip(resolved_inputs, reference_answers, strict=True))
    source_answers = [answers[0] for _, answers in pairs]
    groups = task.group_answers(
        original_input, source_answers, prompts, judge_config, judge_temperature
    )

    rewrites = []
    for resolved_input, answers in pairs:
        recovery = recover(
            resolved_input=resolved_input,
            source_answer=answers[0],
            task=task,
            prompts=prompts,
            model_config=model_config,
            judge_config=judge_config,
            config=config["reference"],
            judge_temperature=judge_temperature,
        )
        rewrites.append({
            "resolved_input": resolved_input,
            "answers": answers,
            "recovery": recovery,
        })

    reference_groups = []
    for index, group in enumerate(groups):
        indices = sorted(group["member_indices"])
        if any(rewrites[i]["recovery"]["accepted"] for i in indices):
            answers = list(dict.fromkeys(
                answer for i in indices for answer in reference_answers[i]
            ))
            reference_groups.append({
                "group_id": f"G{index + 1}",
                "answers": answers,
                "rewrite_indices": indices,
            })

    return {
        "input": original_input,
        "rewrites": rewrites,
        "reference_groups": reference_groups,
        "support": [group["answers"][0] for group in reference_groups],
    }
