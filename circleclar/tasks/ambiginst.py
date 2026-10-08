import json
import re

from ..llm import generate


def get_input(record, database_root=None):
    return {
        "task_instruction": record["orig_instruction"],
        "instance_input": record["input"],
    }


def get_references(record, original_input):
    if "gt_clarification" in record:
        instructions = record["gt_clarification"]
        indices = record.get("clarification_to_target", list(range(len(instructions))))
        pairs = [(text, record["target"][i]) for text, i in zip(instructions, indices, strict=True)]
    else:
        pairs = [
            (item["resolved_instruction"], item["released_target"])
            for item in record["interpretations"]
        ]
    return (
        [{**original_input, "task_instruction": text} for text, _ in pairs],
        [[answer] for _, answer in pairs],
    )


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


def enumerate_answers(task_input, prompts, model_config, temperature):
    prompt = prompts["enumeration"]
    messages = [{"role": "system", "content": prompt["system"]}]
    for example in prompts["demonstrations"]:
        messages.extend(render_messages(
            {"user": prompt["user"]},
            task_instruction=example["task_instruction"],
            instance_input=example["input"],
        ))
        messages.append({
            "role": "assistant",
            "content": "\n".join(
                f"{i}. {answer}" for i, answer in enumerate(example["answers"], 1)
            ),
        })
    messages.extend(render_messages({"user": prompt["user"]}, **task_input))
    text = generate(messages, model_config, temperature).strip()
    items = list(re.finditer(r"^\d+\.\s+", text, re.MULTILINE))
    if not items or items[0].start() != 0:
        raise ValueError("Expected a numbered answer list.")
    ends = [item.start() for item in items[1:]] + [len(text)]
    answers = [text[item.end():end].strip() for item, end in zip(items, ends)]
    if not all(answers):
        raise ValueError("Expected non-empty candidate outputs.")
    return answers


def clarify(task_input, source_answer, prompts, model_config, temperature):
    messages = render_messages(
        prompts["clarification"], **task_input, target_answer=source_answer
    )
    text = generate(messages, model_config, temperature).strip()
    match = re.fullmatch(r"Clarification:\s*(.+)", text)
    if match is None:
        raise ValueError("Expected one Clarification: line.")
    return {**task_input, "task_instruction": match[1].strip()}


def reanswer(resolved_input, prompts, model_config, temperature):
    messages = render_messages(
        prompts["reanswer"],
        resolved_instruction=resolved_input["task_instruction"],
        instance_input=resolved_input["instance_input"],
    )
    answer = generate(messages, model_config, temperature).strip()
    if not answer:
        raise ValueError("Expected a non-empty answer.")
    return answer


def group_answers(task_input, answers, prompts, model_config, temperature):
    if not answers:
        return []
    unique_answers = list(dict.fromkeys(answers))
    if len(unique_answers) == 1:
        return [{"cluster_id": 0, "member_indices": list(range(len(answers)))}]
    messages = render_messages(
        prompts["grouping"], **task_input,
        numbered_answers="\n".join(
            f"{i}. {answer}" for i, answer in enumerate(unique_answers)
        ),
    )
    clusters = _parse_json(generate(messages, model_config, temperature))["clusters"]
    members = [i for cluster in clusters for i in cluster["member_indices"]]
    if (
        any(type(i) is not int for i in members)
        or sorted(members) != list(range(len(unique_answers)))
        or any(not cluster["member_indices"] for cluster in clusters)
    ):
        raise ValueError("Clusters must partition all answer indices exactly once.")
    for cluster in clusters:
        texts = {unique_answers[i] for i in cluster["member_indices"]}
        cluster["member_indices"] = [i for i, answer in enumerate(answers) if answer in texts]
    return clusters


def judge_consistency(
    task_input, answer_a, answer_b, prompts, model_config, temperature, answer_group=None
):
    messages = render_messages(
        prompts["consistency_judge"], **task_input, answer_a=answer_a, answer_b=answer_b
    )
    result = _parse_json(generate(messages, model_config, temperature))
    if type(result["score"]) is not bool:
        raise ValueError("The consistency score must be a JSON Boolean.")
    return result


def match_reference(
    task_input, prediction_group, reference_groups, prompts, model_config, temperature
):
    if not reference_groups:
        return {"group_id": "NONE", "reason": "Reference support is empty."}
    messages = render_messages(
        prompts["reference_matching"], **task_input,
        canonical_groups_json=json.dumps(reference_groups, ensure_ascii=False),
        target_prediction_json=json.dumps(prediction_group, ensure_ascii=False),
    )
    result = _parse_json(generate(messages, model_config, temperature))
    if result["group_id"] not in {group["group_id"] for group in reference_groups} | {"NONE"}:
        raise ValueError("Expected a reference group ID or NONE.")
    return result
