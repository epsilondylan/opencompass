from mmengine import read_base

with read_base():
    from ..opencompass.configs.datasets.korbench.korbench_single_0_shot_gen import korbench_0shot_single_datasets as zero_shot_datasets
    from ..opencompass.configs.datasets.korbench.korbench_single_3_shot_gen import korbench_3shot_single_datasets as three_shot_datasets
    from ..opencompass.configs.datasets.korbench.korbench_mixed_a7dec3 import korbench_mixed_datasets as mixed_datasets
    from opencompass.configs.models.openai.gpt_4o_mini import models as gpt4
    from opencompass.configs.summarizers.groups.korbench import summarizer

datasets = zero_shot_datasets + three_shot_datasets + mixed_datasets
for dataset in datasets:
    dataset['reader_cfg']['test_range'] = '[0:8]'
models = gpt4
