import json
import re

from ..llm import generate


def get_input(record, database_root=None):
    return record["question"]


def get_references(record, original_input):
    return record["gt_rewrite"], record["answer"]


def render_messages(prompt, **values):
    return [
        {
            "role": role,
            "content": re.sub(
                r"\{([a-z_]+)\}", lambda match: str(values[match[1]]), text
            ),
        }
        for role, text in prompt.items()
    ]


def _parse_json(text):
    text = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    return json.loads(fenced[1] if fenced else text)


def enumerate_answers(question, prompts, model_config, temperature):
    messages = render_messages(prompts["enumeration"], question=question)
    text = generate(messages, model_config, temperature)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    answers = [re.fullmatch(r"\d+\.\s+(.+)", line) for line in lines]
    if not answers or any(answer is None for answer in answers):
        raise ValueError("Expected a numbered answer list.")
    return [answer[1].strip() for answer in answers]


def clarify(question, source_answer, prompts, model_config, temperature):
    messages = render_messages(
        prompts["clarification"], question=question, source_answer=source_answer
    )
    text = generate(messages, model_config, temperature).strip()
    match = re.fullmatch(r"Clarification:\s*(.+)", text)
    if match is None:
        raise ValueError("Expected one Clarification: line.")
    return match[1].strip()


def reanswer(resolved_question, prompts, model_config, temperature):
    messages = render_messages(
        prompts["reanswer"], resolved_question=resolved_question
    )
    answer = generate(messages, model_config, temperature).strip()
    if not answer:
        raise ValueError("Expected a non-empty answer.")
    return answer


def group_answers(question, answers, prompts, model_config, temperature):
    if not answers:
        return []
    unique_answers = list(dict.fromkeys(answers))
    if len(unique_answers) == 1:
        return [{"cluster_id": 0, "member_indices": list(range(len(answers)))}]

    messages = render_messages(
        prompts["grouping"],
        question=question,
        numbered_answers="\n".join(
            f"{index}. {answer}" for index, answer in enumerate(unique_answers)
        ),
    )
    result = _parse_json(generate(messages, model_config, temperature))
    clusters = result["clusters"]
    members = [index for cluster in clusters for index in cluster["member_indices"]]
    if (
        any(type(index) is not int for index in members)
        or sorted(members) != list(range(len(unique_answers)))
        or any(not cluster["member_indices"] for cluster in clusters)
    ):
        raise ValueError("Clusters must partition all answer indices exactly once.")

    for cluster in clusters:
        texts = {unique_answers[index] for index in cluster["member_indices"]}
        cluster["member_indices"] = [
            index for index, answer in enumerate(answers) if answer in texts
        ]
    return clusters


def judge_consistency(
    question, answer_a, answer_b, prompts, model_config, temperature, answer_group=None
):
    messages = render_messages(
        prompts["consistency_judge"],
        question=question,
        ref_text=answer_a,
        candidate=answer_b,
    )
    result = _parse_json(generate(messages, model_config, temperature))
    if type(result["score"]) is not bool:
        raise ValueError("The consistency score must be a JSON Boolean.")
    return result


def match_reference(
    question, prediction_group, reference_groups, prompts, model_config, temperature
):
    if not reference_groups:
        return {"group_id": "NONE", "reason": "Reference support is empty."}

    messages = render_messages(
        prompts["reference_matching"],
        question=question,
        canonical_groups_json=json.dumps(reference_groups, ensure_ascii=False),
        target_prediction_json=json.dumps(prediction_group, ensure_ascii=False),
    )
    result = _parse_json(generate(messages, model_config, temperature))
    group_ids = {group["group_id"] for group in reference_groups}
    if result["group_id"] not in group_ids | {"NONE"}:
        raise ValueError("Expected a reference group ID or NONE.")
    return result
