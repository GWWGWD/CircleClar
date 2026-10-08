import json

import yaml

from . import ambiginst, qa, sql


def load_task(config, root):
    task = {"qa": qa, "ambiginst": ambiginst, "sql": sql}[config["task"]]
    prompts = yaml.safe_load((root / config["prompt_file"]).read_text(encoding="utf-8"))
    if config["task"] == "ambiginst":
        path = root / config["enumeration"]["demonstrations"]
        prompts["demonstrations"] = json.loads(path.read_text(encoding="utf-8"))
        if len(prompts["demonstrations"]) != 7:
            raise ValueError("AmbigInst enumeration requires seven demonstrations.")
    return task, prompts
