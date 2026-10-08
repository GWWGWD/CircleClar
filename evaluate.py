import argparse
import json
from pathlib import Path

import yaml

from circleclar.evaluation.matching import match_predictions
from circleclar.evaluation.metrics import policy_actions, set_metrics, summarize
from circleclar.tasks import load_task


def load_records(path):
    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    indexed = {record["id"]: record for record in records}
    if len(indexed) != len(records):
        raise ValueError(f"Duplicate sample IDs in {path}.")
    return indexed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    task, prompts = load_task(config, root)
    models = yaml.safe_load((root / config["models_file"]).read_text(encoding="utf-8"))
    judge_config = models["models"][models["judge"]["model"]]
    judge_temperature = models["judge"]["temperature"]

    predictions = load_records(args.predictions)
    references = load_records(args.reference)
    if not predictions:
        parser.error("Predictions must contain at least one question.")
    if len({row["model"] for row in predictions.values()}) != 1:
        parser.error("Predictions must use the same model.")
    for sample_id, prediction in predictions.items():
        if sample_id not in references:
            parser.error(f"Missing reference for sample {sample_id}.")
        reference = references[sample_id]
        if any(prediction[key] != reference[key] for key in ("input", "model")):
            parser.error(f"Input or model differs for sample {sample_id}.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        results = []
        for index, (sample_id, prediction) in enumerate(predictions.items()):
            result = match_predictions(
                original_input=prediction["input"],
                predicted_answers=prediction["support"],
                reference_groups=references[sample_id]["reference_groups"],
                task=task,
                prompts=prompts,
                judge_config=judge_config,
                judge_temperature=judge_temperature,
            )
            result["metrics"] = set_metrics(result)
            result["action"] = policy_actions(result)
            results.append(result)
            print(f"{index + 1}/{len(predictions)}", flush=True)

        report = {
            "summary": summarize(results),
            "per_question": results,
        }
        json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
