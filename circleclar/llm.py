import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def generate(messages, model_config, temperature) -> str:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    params = {
        "model": model_config["model"],
        "messages": messages,
        "temperature": temperature,
    }
    if "reasoning_effort" in model_config:
        params["reasoning_effort"] = model_config["reasoning_effort"]

    with OpenAI(
        base_url=os.environ[model_config["base_url_env"]],
        api_key=os.environ[model_config["api_key_env"]],
    ) as client:
        response = client.chat.completions.create(**params)

    return response.choices[0].message.content or ""
