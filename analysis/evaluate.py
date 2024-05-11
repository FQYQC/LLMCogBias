import numpy as np
import openpyxl
import json
import os
import os.path as osp

from metrics import compute_clip_cohen_d, compute_linear_l


def np_and_remove_null(A):
    r = [i for i in A if i is not None]
    return np.array(r)


def evaluate_dataset(output, savepath, name):
    with open("analysis/stat_template.json", "r") as f:
        results = json.load(f)

    output = output["tasks"]

    results[0]["data"]["A"] = np_and_remove_null(output[1]["answers"])  # task1
    results[0]["data"]["B"] = np_and_remove_null(output[0]["answers"])
    results[1]["data"]["A"] = np_and_remove_null(output[2]["answers"])  # task2
    results[2]["data"]["A"] = np_and_remove_null(output[3]["answers"])  # task3
    results[3]["data"]["A"] = np_and_remove_null(output[4]["answers"])  # task4
    results[4]["data"]["A"] = np_and_remove_null(output[5]["answers"])  # task5
    results[4]["data"]["B"] = np_and_remove_null(output[6]["answers"])  # task5
    results[5]["data"]["A"] = np_and_remove_null(output[7]["answers"])  # task6.1
    results[5]["data"]["B"] = np_and_remove_null(output[8]["answers"][1])  # task6.1
    results[6]["data"]["A"] = np_and_remove_null(output[8]["answers"][0])  # task6.2
    results[6]["data"]["B"] = np_and_remove_null(output[5]["answers"])  # task6.2
    results[7]["data"]["A"] = np_and_remove_null(output[9]["answers"])  # task7.1
    results[8]["data"]["A"] = np_and_remove_null(output[10]["answers"])  # task7.2
    results[9]["data"]["A"] = np_and_remove_null(output[11]["answers"])  # task7.3
    results[10]["data"]["B"] = np_and_remove_null(output[12]["answers"])  # task7.4
    results[11]["data"]["A"] = np_and_remove_null(output[13]["answers"])  # task8
    results[11]["data"]["B"] = np_and_remove_null(output[14]["answers"])  # task8
    task9data = np.array(
        [1] * np_and_remove_null(output[15]["answers"]).sum()
        + [0] * (np_and_remove_null(output[16]["answers"]).sum())
    )
    results[12]["data"]["A"] = task9data  # task9

    for i in range(len(results)):
        if results[i]["func"] == "d":
            results[i]["result"] = compute_clip_cohen_d(
                results[i]["data"]["A"], results[i]["data"]["B"]
            )

        elif results[i]["func"] == "l":
            results[i]["result"] = compute_linear_l(
                results[i]["data"]["A"],
                target=results[i]["target"],
                morethan=results[i]["morethan"],
                tot=len(results[i]["data"]["A"]) if i == 12 else 10,
            )
        if isinstance(results[i]["data"]["A"], np.ndarray):
            results[i]["data"]["A"] = results[i]["data"]["A"].tolist()
        if isinstance(results[i]["data"]["B"], np.ndarray):
            results[i]["data"]["B"] = results[i]["data"]["B"].tolist()

    dl = [r["result"] for r in results]
    e = [
        *(dl[0:5]),
        (dl[5] + dl[6]) / 2,
        (dl[7] + dl[8] + dl[9] + dl[10]) / 4,
        *(dl[11:13]),
    ]
    print(e)

    with open(save_path, "w") as f:
        json.dump(
            {
                "overview": {
                    "name": name,
                    "dl": dl,
                    "e": e,
                },
                "details": results,
            },
            f,
            indent=4,
        )


if __name__ == "__main__":
    eva_root = "results/collected_results/data_20240428044314/"
    save_root = "analysis/stat_results"
    folder = "basic_sbs"
    eva_folder = osp.join(eva_root, folder)
    save_folder = osp.join(save_root, folder)

    os.makedirs(save_folder, exist_ok=True)

    files = os.listdir(eva_folder)
    for file in files:
        if file.startswith("meta"):
            continue
        save_path = osp.join(save_folder, "eva_" + file)
        with open(osp.join(eva_folder, file), "r") as f:
            output = json.load(f)
        print(file)
        evaluate_dataset(output, savepath=save_path, name=folder)
