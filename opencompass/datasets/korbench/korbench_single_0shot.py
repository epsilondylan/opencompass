
import json
import os
from datasets import Dataset
from opencompass.registry import LOAD_DATASET
from opencompass.utils import get_data_path
from ..base import BaseDataset
from opencompass.datasets.korbench.korbench_utils import evaluate_responses, load_json_or_jsonl, find_file, load_yaml

import yaml
from opencompass.openicl.icl_evaluator import BaseEvaluator
from opencompass.registry import ICL_EVALUATORS

@LOAD_DATASET.register_module()
class korbenchsingle0shotDataset(BaseDataset):
    """
    Dataset loader for the  task in KOR-Bench.
    """

    @staticmethod
    def load(path, category, subquestions=False):
        """
        Load the  dataset using shared .
        """
        base_path = get_data_path(path)
        rule_file = find_file(base_path, os.path.join(category, "rule"))
        sample_file = find_file(base_path, os.path.join(category, "sample"))
        
        # Load data
        rules = load_json_or_jsonl(rule_file) or []
        samples = load_json_or_jsonl(sample_file) or []

        # Load the prompt template
        template_path = os.path.join(os.path.dirname(__file__), "korbench_dataset_config/prompt/0_shot.yaml")
        print(f"template_path: {template_path}")
        try:
            template = load_yaml(template_path)
        except FileNotFoundError:
            print(f"[ERROR] Missing prompt template: {template_path}")
            return Dataset.from_list([])

        # Process data

        if category == "cipher" and subquestions:
            # Load data
            subquestions_file = find_file(base_path, os.path.join(category, "subquestions"))
            rules = load_json_or_jsonl(rule_file) or []
            samples = load_json_or_jsonl(subquestions_file) or []

            # Load the prompt template
            template_path = os.path.join(os.path.dirname(__file__), "korbench_dataset_config/prompt/0_shot.yaml")
            print(f"template_path: {template_path}")
            try:
                template = load_yaml(template_path)
            except FileNotFoundError:
                print(f"[ERROR] Missing prompt template: {template_path}")
                return Dataset.from_list([])

            # Process data
            data = []
            for sample in samples:
                rule_id = sample["rule_id"]
                rule = next((r for r in rules if r["idx"] == rule_id), None)
                if not rule:
                    print(f"[WARNING] Rule ID {sample['rule_id']} not found for sample {sample}. Skipping...")
                    continue
                
                input = sample["input"]
                for detail in sample["steps_details"]:
                    item = {}
                    steps_details_key_exists = False
                    for key, value in sample.items():
                        if key != "steps_details":
                            item[key] = value
                        else:
                            steps_details_key_exists = True
                    
                    if not steps_details_key_exists:
                        raise ValueError("steps_details key not found in the sample")

                    description = detail["description"]
                    subquestion = input + "\n\n" + description
                    prompt_format = [rule["rule_content"], subquestion]
                    prompt = template[f"{category}_prompt_format"][0].format(*prompt_format)

                    for key, value in detail.items():
                        item[key] = value

                    data.append({
                        "rule_content": rule["rule_content"],
                        "question": subquestion,
                        "answer": item["answer"],
                        "prompt": prompt,
                        "rule_id": rule["idx"],
                        "mode": "0_shot",
                        "category": category,
                    })
            
            return Dataset.from_list(data)

        data = []
        for sample in samples:
            rule_id = sample["rule_id"]
            rule = next((r for r in rules if r["idx"] == rule_id), None)
            if not rule:
                print(f"[WARNING] Rule ID {sample['rule_id']} not found for sample {sample}. Skipping...")
                continue

            prompt_key = f"{category}_prompt_format"
            prompt = template[prompt_key][0].format(rule["rule_content"], sample["question"])

            # Add processed item
            data.append({
                "rule_content": rule["rule_content"],
                "question": sample["question"],
                "answer": sample["answer"],
                "prompt": prompt,
                "rule_id": rule["idx"],
                "mode": "0_shot",
                "category": category,
            })        


        return Dataset.from_list(data)

@ICL_EVALUATORS.register_module()
class korbenchsingle0shotEvaluator(BaseEvaluator):
    def __init__(self):
        super().__init__()

    def score(self, predictions, references, test_set):
        """
        Evaluate predictions for the  task.
        """
        dataset_scores = {}
        data = {}
        count = 0


        for i in range(len(predictions)):
            if test_set[i]["mode"] == "0_shot":
                data[count] = {
                    "prediction": predictions[i],
                    "gold": references[i],
                    "rule_id": test_set[i]["rule_id"],
                    "category": test_set[i]["category"],
                }
                count += 1
                

        if data:
            evaluation_results = evaluate_responses(data, "0_shot")
            correct_count = sum(res["is_correct"] for res in evaluation_results)
            accuracy = (correct_count / len(evaluation_results)) * 100 if evaluation_results else 0
            dataset_scores["accuracy"] = accuracy

        else:
            raise ValueError("0_shot data is empty")

        return dataset_scores
