import base64
import json
import math
import re
import sqlite3
import time
from collections import Counter
from contextlib import closing
from itertools import permutations
from pathlib import Path

from ..llm import generate


def get_input(record, database_root):
    database = (Path(database_root) / record["database"]).resolve()
    if not database.is_file():
        raise FileNotFoundError(database)
    return {
        "request": record["effective_unresolved_question"],
        "database": str(database),
    }


def get_references(record, original_input):
    return (
        [{**original_input, "request": item["effective_text"]} for item in record["interpretations"]],
        [[item["gold_sql"]] for item in record["interpretations"]],
    )


def database_context(database):
    with closing(sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        schema = "\n".join(row[0] for row in connection.execute(
            "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
        ))
        dump = "\n".join(connection.iterdump())
    return {"DATABASE_SCHEMA": schema, "DATABASE_DUMP": dump}


def render_messages(prompt, **values):
    pattern = re.compile(r"\{\{([A-Z_]+)\}\}|\b(DATABASE_DUMP|UNRESOLVED_REQUEST|RESOLVED_REQUEST|REPRESENTATIVE_SQL)\b")
    return [
        {
            "role": role,
            "content": pattern.sub(lambda match: str(values[match[1] or match[2]]), text),
        }
        for role, text in prompt.items()
    ]


def _parse_json(text):
    text = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    return json.loads(fenced[1] if fenced else text)


def _strip_fence(text):
    text = text.strip()
    fenced = re.fullmatch(r"```(?:sql|sqlite)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    return fenced[1].strip() if fenced else text


def split_queries(text):
    text = _strip_fence(text)
    tokens = re.finditer(
        r"--[^\n]*|/\*.*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|`(?:``|[^`])*`|\[[^\]]*\]"
        r"|\n[ \t\r]*\n|[A-Za-z_]+|.", text, re.DOTALL,
    )
    queries = []
    start, depth = 0, 0
    seen_select = False
    last_word = ""
    for token in tokens:
        value = token[0]
        if value == "(":
            depth += 1
        elif value == ")":
            depth -= 1
        elif depth == 0 and value.isalpha():
            last_word = value.upper()
            seen_select |= last_word == "SELECT"
        boundary = value == ";" and depth == 0
        boundary |= (
            value.startswith("\n") and len(value) > 1 and depth == 0 and seen_select
            and last_word not in {"UNION", "ALL", "INTERSECT", "EXCEPT"}
            and re.match(r"\s*(?:SELECT|WITH)\b", text[token.end():], re.IGNORECASE) is not None
        )
        if boundary:
            query = text[start:token.start()].strip()
            if query:
                queries.append(query)
            start = token.end()
            seen_select = False
            last_word = ""
    if text[start:].strip():
        queries.append(text[start:].strip())
    return queries


def _typed_cell(value):
    if value is None:
        return ["null", None]
    if isinstance(value, int):
        return ["integer", value]
    if isinstance(value, float):
        return ["real", value if math.isfinite(value) else str(value)]
    if isinstance(value, bytes):
        return ["blob", base64.b64encode(value).decode("ascii")]
    return ["text", value]


def execute(database, query):
    database = Path(database).resolve()
    if not database.is_file():
        raise FileNotFoundError(database)
    query = _strip_fence(query)
    statement = re.sub(r"\A(?:\s|--[^\n]*(?:\n|$)|/\*.*?\*/)*", "", query, flags=re.DOTALL)
    if not re.match(r"(?:SELECT|WITH)\b", statement, re.IGNORECASE):
        return {"sql": query, "error": "Expected one read-only SELECT or WITH statement."}
    try:
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as connection:
            connection.execute("PRAGMA query_only = ON")
            deadline = time.monotonic() + 5.0
            connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
            cursor = connection.execute(query)
            rows = [[_typed_cell(value) for value in row] for row in cursor.fetchall()]
            return {
                "sql": query,
                "result": {
                    "columns": [column[0] for column in cursor.description],
                    "rows": rows,
                    "row_count": len(rows),
                    "column_count": len(cursor.description),
                },
            }
    except (sqlite3.Error, sqlite3.Warning) as error:
        return {"sql": query, "error": str(error)}


def _projection(source, target):
    left = [tuple(tuple(cell) for cell in row) for row in source["rows"]]
    right = [tuple(tuple(cell) for cell in row) for row in target["rows"]]
    if len(left) != len(right) or source["column_count"] > target["column_count"]:
        return None
    choices = [
        [j for j in range(target["column_count"])
         if Counter(row[i] for row in left) == Counter(row[j] for row in right)]
        for i in range(source["column_count"])
    ]
    for columns in permutations(range(target["column_count"]), source["column_count"]):
        if any(column not in choices[i] for i, column in enumerate(columns)):
            continue
        projected = [tuple(row[j] for j in columns) for row in right]
        if Counter(left) == Counter(projected):
            return list(columns)
    return None


def relation_check(source, recovered):
    forward = _projection(source, recovered)
    reverse = _projection(recovered, source)
    return {
        "source_shape": [source["row_count"], source["column_count"]],
        "reanswer_shape": [recovered["row_count"], recovered["column_count"]],
        "source_is_lossless_projection_of_reanswer": forward is not None,
        "reanswer_column_indexes_for_source": forward,
        "reanswer_is_lossless_projection_of_source": reverse is not None,
        "source_column_indexes_for_reanswer": reverse,
    }


def enumerate_answers(task_input, prompts, model_config, temperature):
    messages = render_messages(
        prompts["enumeration"], **database_context(task_input["database"]),
        UNRESOLVED_REQUEST=task_input["request"],
    )
    return split_queries(generate(messages, model_config, temperature))


def clarify(task_input, source_answer, prompts, model_config, temperature):
    messages = render_messages(
        prompts["clarification"], **database_context(task_input["database"]),
        UNRESOLVED_REQUEST=task_input["request"], REPRESENTATIVE_SQL=source_answer,
    )
    text = generate(messages, model_config, temperature).strip()
    match = re.fullmatch(r"Clarification:\s*(.+)", text)
    if match is None:
        raise ValueError("Expected one Clarification: line.")
    return {**task_input, "request": match[1].strip()}


def reanswer(resolved_input, prompts, model_config, temperature):
    messages = render_messages(
        prompts["reanswer"], **database_context(resolved_input["database"]),
        RESOLVED_REQUEST=resolved_input["request"],
    )
    return _strip_fence(generate(messages, model_config, temperature))


def group_answers(task_input, answers, prompts, model_config, temperature):
    queries = list(dict.fromkeys(_strip_fence(answer) for answer in answers))
    results = [execute(task_input["database"], query) for query in queries]
    results = [result for result in results if "result" in result]
    if not results:
        return []
    by_id = {f"id{i}": result["sql"] for i, result in enumerate(results, 1)}
    if len(results) == 1:
        clusters = [{"members": list(by_id)}]
    else:
        messages = render_messages(
            prompts["grouping"], **database_context(task_input["database"]),
            INPUT_REQUEST=task_input["request"],
            SQL_RESULTS=json.dumps([
                {"id": name, **result} for name, result in zip(by_id, results)
            ], ensure_ascii=False),
        )
        clusters = _parse_json(generate(messages, model_config, temperature))["clusters"]
        members = [member for cluster in clusters for member in cluster["members"]]
        if (
            any(not isinstance(member, str) for member in members)
            or sorted(members) != sorted(by_id)
            or any(not cluster["members"] for cluster in clusters)
        ):
            raise ValueError("Clusters must partition all valid SQL IDs exactly once.")
    return [
        {
            "cluster_id": index,
            "member_indices": [
                i for i, answer in enumerate(answers)
                if _strip_fence(answer) in {by_id[name] for name in cluster["members"]}
            ],
        }
        for index, cluster in enumerate(clusters)
    ]


def judge_consistency(
    task_input, answer_a, answer_b, prompts, model_config, temperature, answer_group=None
):
    source = execute(task_input["database"], answer_a)
    recovered = [
        execute(task_input["database"], answer)
        for answer in dict.fromkeys(answer_group if answer_group is not None else [answer_b])
    ]
    if "error" in source or not recovered or any("error" in result for result in recovered):
        return {"score": False, "reason": "Source or re-answer SQL did not execute."}
    messages = render_messages(
        prompts["consistency_judge"], **database_context(task_input["database"]),
        RESOLVED_REQUEST=task_input["request"],
        SOURCE_SQL_RESULT=json.dumps(source, ensure_ascii=False),
        STABLE_RECOVERY_SQL_RESULTS=json.dumps(recovered, ensure_ascii=False),
        DETERMINISTIC_RELATION_CHECK=json.dumps([
            {"sql": item["sql"], **relation_check(source["result"], item["result"])}
            for item in recovered
        ], ensure_ascii=False),
    )
    result = _parse_json(generate(messages, model_config, temperature))
    if result["decision"] not in {"equivalent", "not_equivalent", "uncertain"}:
        raise ValueError("Expected equivalent, not_equivalent, or uncertain.")
    return {
        "score": result["decision"] == "equivalent",
        "decision": result["decision"],
        "reason": result["reason"],
    }


def match_reference(
    task_input, prediction_group, reference_groups, prompts, model_config, temperature
):
    if not reference_groups:
        return {"group_id": "NONE", "reason": "Reference support is empty."}
    def evidence(group):
        return {
            "group_id": group["group_id"],
            "answers": [execute(task_input["database"], answer) for answer in group["answers"]],
        }
    messages = render_messages(
        prompts["reference_matching"], **database_context(task_input["database"]),
        INPUT_REQUEST=task_input["request"],
        REFERENCE_GROUPS_JSON=json.dumps([evidence(group) for group in reference_groups], ensure_ascii=False),
        PREDICTED_GROUP_JSON=json.dumps(evidence(prediction_group), ensure_ascii=False),
    )
    result = _parse_json(generate(messages, model_config, temperature))
    if result["group_id"] not in {group["group_id"] for group in reference_groups} | {"NONE"}:
        raise ValueError("Expected a reference group ID or NONE.")
    return result
