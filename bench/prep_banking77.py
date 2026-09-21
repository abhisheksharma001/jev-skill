#!/usr/bin/env python3
"""Build the Banking77 benchmark inputs (PolyAI, CC-BY-4.0): a seeded 400-row sample of the test split,
three Choice members over the same 77 options (+ other), and a label-free file for the Fable baseline."""
import csv, json, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, "data", "banking77_test.csv"), encoding="utf-8")))
random.Random(77).shuffle(rows)
rows = rows[:400]
desc = json.load(open(os.path.join(HERE, "banking77_descriptions.json")))
os.makedirs(os.path.join(HERE, "work"), exist_ok=True)
with open(os.path.join(HERE, "work", "b77_cases.jsonl"), "w") as f, open(os.path.join(HERE, "work", "b77_unlabelled.jsonl"), "w") as u:
    for i, r in enumerate(rows):
        f.write(json.dumps({"id": f"b{i:03d}", "state": {"customer_message": r["text"]}, "labels": {"intent": r["category"]}}) + "\n")
        u.write(json.dumps({"id": f"b{i:03d}", "text": r["text"]}) + "\n")
other = {"other": "None of the listed intents fits."}
questions = {
    # the naive single question most people would write first: label names only
    "names_only": {"type": "choice", "instructions": "Which intent does the customer message express?",
                   "criteria": {**{k: None for k in desc}, **other}},
    # same options, each with a policy-style description written by a strong model at design time
    "described": {"type": "choice", "instructions": "Which intent does the customer message express?",
                  "criteria": {**desc, **other}},
    # a second phrasing of the instruction, to decorrelate errors
    "described_goal": {"type": "choice",
                       "instructions": "A bank customer wrote `customer_message`. Pick the option that best states what happened to them or what they want done.",
                       "criteria": {**desc, **other}},
}
json.dump(questions, open(os.path.join(HERE, "work", "b77_questions.json"), "w"), indent=1)
print("cases 400, options", len(desc) + 1)
