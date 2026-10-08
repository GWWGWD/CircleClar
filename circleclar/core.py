from .recovery import recover


def run_circleclar(
    original_input,
    task,
    prompts,
    model_config,
    judge_config,
    config,
    judge_temperature=0.0,
):
    samples = config["enumeration"]["samples"]
    if samples < 1:
        raise ValueError("Candidate discovery requires at least one enumeration.")

    enumerations = [
        task.enumerate_answers(
            original_input, prompts, model_config, config["enumeration"]["temperature"]
        )
        for _ in range(samples)
    ]
    answer_pool = list(dict.fromkeys(
        answer for answers in enumerations for answer in answers
    ))
    groups = task.group_answers(
        original_input, answer_pool, prompts, judge_config, judge_temperature
    )

    candidates = []
    support = []
    for group in groups:
        answers = [answer_pool[index] for index in sorted(group["member_indices"])]
        source_answer = answers[0]
        clarification = task.clarify(
            original_input,
            source_answer,
            prompts,
            model_config,
            config["clarification"]["temperature"],
        )
        recovery = recover(
            resolved_input=clarification,
            source_answer=source_answer,
            task=task,
            prompts=prompts,
            model_config=model_config,
            judge_config=judge_config,
            config=config["recovery"],
            judge_temperature=judge_temperature,
        )
        candidates.append({
            "answers": answers,
            "source_answer": source_answer,
            "clarification": clarification,
            "recovery": recovery,
        })
        if recovery["accepted"]:
            support.append(source_answer)

    return {
        "input": original_input,
        "enumerations": enumerations,
        "candidates": candidates,
        "support": support,
    }
