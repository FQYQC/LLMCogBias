# imports
import os
import os.path as osp
import sys
import json
import tqdm
import yaml
import copy
import argparse

from poe_api_wrapper import PoeApi
from cache import Cacher

# configs
os.environ["http_proxy"] = "http://172.22.160.1:7880"
os.environ["https_proxy"] = "http://172.22.160.1:7880"


parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, required=True)
parser.add_argument("--api", type=str, required=False, default="default")

args = parser.parse_args()

api_config_file = "api_configs.json"
with open(api_config_file, "r") as f:
    api_configs = json.load(f)

if args.api == "default":
    tokens = api_configs["poe_tokens"]
else:
    tokens = api_configs[f"poe_tokens_{args.api}"]
tokens

# experiment settings

force_replace = False

config_path = "results/configs"
config_name = args.config
config_path = osp.join(config_path, config_name + ".yaml")
if "/" in config_name:
    config_name = config_name.split("/")[-1]

configs = yaml.load(open(config_path, "r"), Loader=yaml.FullLoader)

dataset_path = osp.join(
    configs["data"]["data_path"], configs["data"]["dataset_name"] + ".json"
)

if configs["use_cache"]:
    cache_path = osp.join(
        configs["save_path"], "cache", "cache_" + configs["cache_name"] + ".json"
    )
else:
    cache_path = osp.join(configs["save_path"], "cache", "cache_default" + ".json")

# initialize apis
client = PoeApi(tokens)
cacher = Cacher(
    cache_path,
    cache_id="default",
    cache_type="json",
    write_cache=True,
    write_interval=1,
    main_args=args,
)

print("APIs initialized, using cache at", cache_path)

tot_price = 0


# experiment

# load dataset
while True:
    try:

        with open(dataset_path, "r") as f:
            dataset = json.load(f)

        os.makedirs(
            osp.join(
                configs["save_path"],
                "responds",
                configs["data"]["dataset_name"],
                config_name,
            ),
            exist_ok=True,
        )

        for bot_id, bot in tqdm.tqdm(
            enumerate(configs["bot_list"]), total=len(configs["bot_list"]), position=0
        ):

            if (
                osp.exists(
                    osp.join(
                        configs["save_path"],
                        "responds",
                        configs["data"]["dataset_name"],
                        config_name,
                        configs["data"]["dataset_name"]
                        + "_"
                        + config_name
                        + "_"
                        + bot
                        + ".json",
                    )
                )
                and not force_replace
            ):
                print(
                    f"File exists: {configs['data']['dataset_name']}_{config_name}_{bot}.json"
                )
                continue

            answers = copy.deepcopy(dataset)

            bar2 = tqdm.tqdm(
                enumerate(dataset["tasks"]), total=len(dataset["tasks"]), position=1
            )

            for task_id, task in bar2:

                task_text = task["text"]

                task_text = (
                    configs["text_modifier"]["prefixes"]
                    + task_text
                    + configs["text_modifier"]["suffixes"]
                )

                answers["tasks"][task_id]["prefixes"] = configs["text_modifier"][
                    "prefixes"
                ]
                answers["tasks"][task_id]["suffixes"] = configs["text_modifier"][
                    "suffixes"
                ]
                answers["tasks"][task_id]["answers"] = []

                for i in range(configs["exp_start"], configs["exp_repeats"]):

                    ans = cacher.send_message(
                        client=client,
                        bot=bot,
                        message=task_text,
                        use_cache=True,
                        add_to_cache=True,
                        trial_id=str(i),
                    )

                    if cacher.last_ret is not None:
                        tot_price += cacher.last_ret["msgPrice"]

                    bar2.set_description(
                        f"Task: {task['id']},{task['effect_name']}, "
                        f"Cache hit: {cacher.cache_hit}/{cacher.call_count}, "
                        f"Total price: {tot_price}, ",
                    )

                    answers["tasks"][task_id]["answers"].append(ans)

            answers["bot"] = bot

            with open(
                osp.join(
                    configs["save_path"],
                    "responds",
                    configs["data"]["dataset_name"],
                    config_name,
                    configs["data"]["dataset_name"]
                    + "_"
                    + config_name
                    + "_"
                    + bot
                    + ".json",
                ),
                "w",
            ) as f:
                json.dump(answers, f, indent=4)

        save_file = osp.join(
            configs["save_path"],
            "responds",
            configs["data"]["dataset_name"],
            config_name,
            "meta.json",
        )

        with open(
            osp.join(
                configs["save_path"],
                "responds",
                configs["data"]["dataset_name"],
                config_name,
                "meta.json",
            ),
            "w",
        ) as f:
            json.dump(
                {
                    "request_times": cacher.call_count,
                    "cache_hit": cacher.cache_hit,
                    "hit_rate": cacher.cache_hit / cacher.call_count,
                    "tot_price": tot_price,
                },
                f,
                indent=4,
            )

        if cacher.last_ret is not None:
            if args.api == "wzx":
                client.delete_chat(cacher.last_ret["bot"], cacher.last_ret["chatId"])

        break

    except Exception as e:
        print(e)
        print(cacher.active_bot_chatId)
        print("Error, retrying...")
        continue

    except KeyboardInterrupt:
        print("Interrupted, saving cache...")
        cacher.save_cache()
        break