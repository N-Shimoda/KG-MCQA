import json

model = ["rebel", "unirel"][0]
dataset = ["KR-200m", "KR-200s", "FPAI-100", "FPAI-20"][0]
el = True
filename = f"exp-mcqa/{model}{'_el' if el else ''}/{dataset}/results.json"

with open(filename, "r") as f:
    data = json.load(f)

correct, fail, unselectable = 0, 0, 0
for cat in data:
    stats = data[cat]["stats"]
    correct += stats["correct"]
    fail += stats["fail"]
    unselectable += stats["unselectable"]

print(f"Correct: {correct}")
print(f"fail: {fail}")
print(f"Unselectable: {unselectable}")
