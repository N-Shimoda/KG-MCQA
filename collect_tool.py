import json

model = "rebel"
filename = f"exp-mcqa/{model}/KR-200m/results.json"
# filename = "exp-mcqa/unirel/KR-200s/results.json"
# filename = "exp-mcqa/unirel/FPAI-100/results.json"
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
