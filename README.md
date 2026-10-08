# CircleClar

CircleClar estimates model-realizable answer support through an answer–clarification–answer cycle. It supports AmbigQA, AmbigQA-HQ, AmbigInst, and AMBROSIA.

## Setup

```bash
cd CircleClar
pip install -r requirements.txt
cp .env.example .env
```

Fill in `OPENAI_API_KEY` in `.env`. The program loads this file automatically; `OPENAI_BASE_URL` defaults to the OpenAI address provided in the template.

Set the model in `configs/models.yaml` and sampling parameters in the dataset configuration. The default model is GPT-5.4-mini.

## Smoke test

```bash
python tests/test_qa.py --id 1
python tests/test_ambiginst.py --id 18
python tests/test_sql.py --id ambrosia-2298
```

Each script runs reference construction, prediction, and evaluation for one example. Results are printed to the terminal only.

## Run the pipeline

Build the model-specific reference, run CircleClar, then evaluate. For QA:

```bash
python build_reference.py \
  --config configs/ambigqa_hq.yaml \
  --data examples/qa.jsonl \
  --output outputs/qa/demo/reference.jsonl

python run.py \
  --config configs/ambigqa_hq.yaml \
  --data examples/qa.jsonl \
  --output outputs/qa/demo/predictions.jsonl

python evaluate.py \
  --config configs/ambigqa_hq.yaml \
  --predictions outputs/qa/demo/predictions.jsonl \
  --reference outputs/qa/demo/reference.jsonl \
  --output outputs/qa/demo/evaluation.json
```

Use a new output directory for each run. `evaluation.json` contains answer matches, per-question metrics, and aggregate metrics.

Select the task with `--config` and `--data`:

| Task | Configuration | Example data |
|---|---|---|
| QA | `configs/ambigqa_hq.yaml` | `examples/qa.jsonl` |
| AmbigInst | `configs/ambiginst.yaml` | `examples/ambiginst.jsonl` |
| SQL | `configs/ambrosia.yaml` | `examples/sql/request.jsonl` |

For the SQL examples, also add `--database-root examples/sql` to the reference and prediction commands. Both SQLite databases are included. Use `outputs/ambiginst/` or `outputs/sql/` for the corresponding results.
