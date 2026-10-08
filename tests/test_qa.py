import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from circleclar.core import run_circleclar
from circleclar.evaluation.matching import match_predictions
from circleclar.evaluation.metrics import policy_actions, set_metrics
from circleclar.evaluation.reference import build_reference
from circleclar.tasks import load_task


def main(default_config="ambigqa_hq", default_data="examples/qa.jsonl", default_database_root=None, default_id="1"):
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=root / f"configs/{default_config}.yaml")
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--data", type=Path, default=root / default_data)
    parser.add_argument("--id", default=default_id)
    parser.add_argument("--database-root", type=Path, default=(
        root / default_database_root if default_database_root else None
    ))
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    with args.data.open(encoding="utf-8") as handle:
        if args.data.suffix == ".jsonl":
            records = [json.loads(line) for line in handle if line.strip()]
        else:
            records = json.load(handle)
    if isinstance(records, dict):
        records = records["items"]
    selected = [
        record
        for index, record in enumerate(records)
        if str(record.get("id", record.get("item_id", index))) == args.id
    ]
    if len(selected) != 1:
        parser.error(f"Expected one question with ID {args.id}.")

    record = selected[0]
    task, prompts = load_task(config, root)
    database_root = args.database_root or root / config.get("database_root", ".")
    original_input = task.get_input(record, database_root)
    resolved_inputs, reference_answers = task.get_references(record, original_input)
    models = yaml.safe_load((root / config["models_file"]).read_text(encoding="utf-8"))
    judge_config = models["models"][models["judge"]["model"]]
    judge_temperature = models["judge"]["temperature"]
    arguments = {
        "original_input": original_input,
        "task": task,
        "prompts": prompts,
        "model_config": models["models"][args.model],
        "judge_config": judge_config,
        "config": config,
        "judge_temperature": judge_temperature,
    }

    print(f"Input: {original_input}", flush=True)
    reference = build_reference(
        resolved_inputs=resolved_inputs,
        reference_answers=reference_answers,
        **arguments,
    )
    print(f"\nReference support: {json.dumps(reference['support'], ensure_ascii=False)}", flush=True)

    print("\nCircleClar prediction", flush=True)
    prediction = run_circleclar(**arguments)
    print("\nEnumeration groups:")
    for candidate in prediction["candidates"]:
        print(f"  {json.dumps(candidate['answers'], ensure_ascii=False)}")
    for candidate in prediction["candidates"]:
        print(f"\nGroup: {json.dumps(candidate['answers'], ensure_ascii=False)}")
        clarification = candidate["clarification"]
        if isinstance(clarification, dict):
            clarification = clarification.get("task_instruction", clarification.get("request"))
        print(f"Clarification: {clarification}")
        recovery = candidate["recovery"]
        reanswer = None
        if recovery["accepted"]:
            top_group = max(recovery["groups"], key=lambda group: group["count"])
            reanswer = list(dict.fromkeys(
                recovery["reanswers"][i] for i in top_group["member_indices"]
            ))
        print(f"Re-answer: {json.dumps(reanswer, ensure_ascii=False)}", flush=True)
    print(f"\nPredicted support: {json.dumps(prediction['support'], ensure_ascii=False)}", flush=True)

    print("\nEvaluation", flush=True)
    result = match_predictions(
        original_input=original_input,
        predicted_answers=prediction["support"],
        reference_groups=reference["reference_groups"],
        task=task,
        prompts=prompts,
        judge_config=judge_config,
        judge_temperature=judge_temperature,
    )
    metrics = set_metrics(result)
    action = policy_actions(result)
    print("\nAnswer matches (prediction -> reference):")
    for pair in result["answers"]:
        left = json.dumps(pair["prediction"], ensure_ascii=False)
        right = json.dumps(pair["reference"], ensure_ascii=False)
        print(f"  {left} -> {right}")
    print(f"\nMetrics: {json.dumps(metrics, ensure_ascii=False)}")
    print(
        f"Action: prediction={action['prediction']}, reference={action['reference']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
