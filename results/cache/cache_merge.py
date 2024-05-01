import json

src1 = "cache_default.json"
src2 = "cache_default_para1.json"
dst = "cache_default_merged.json"

with open(src1, "r") as f:
    data1 = json.load(f)

with open(src2, "r") as f:
    data2 = json.load(f)

for bot in data2:
    if bot not in data1:
        data1[bot] = data2[bot]
    else:
        for text in data2[bot]:
            if text not in data1[bot]:
                data1[bot][text] = data2[bot][text]
            else:
                data1[bot][text].update(data2[bot][text])

with open(dst, "w") as f:
    json.dump(data1, f, indent=4)