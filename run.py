import argparse
import json
from pathlib import Path

import yaml

from circleclar.core import run_circleclar
from circleclar.tasks import load_task


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--data", type=Path)
    parser.add_argument("--database-root", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be non-negative.")

    root = Path(__file__).resolve().parent
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    task, prompts = load_task(config, root)
    database_root = args.database_root or root / config.get("database_root", ".")
    models = yaml.safe_load((root / config["models_file"]).read_text(encoding="utf-8"))
    model_config = models["models"][args.model]
    judge_config = models["models"][models["judge"]["model"]]
    judge_temperature = models["judge"]["temperature"]

    data_path = args.data or root / config["data"]
    with data_path.open(encoding="utf-8") as handle:
        if data_path.suffix == ".jsonl":
            records = [json.loads(line) for line in handle if line.strip()]
        else:
            records = json.load(handle)
    if isinstance(records, dict):
        records = records["items"]
    records = records[:args.limit]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        for index, record in enumerate(records):
            original_input = task.get_input(record, database_root)
            result = run_circleclar(
                original_input=original_input,
                task=task,
                prompts=prompts,
                model_config=model_config,
                judge_config=judge_config,
                config=config,
                judge_temperature=judge_temperature,
            )
            result["id"] = record.get("id", record.get("item_id", index))
            result["model"] = args.model
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            handle.flush()
            print(f"{index + 1}/{len(records)}", flush=True)


if __name__ == "__main__":
    main()
