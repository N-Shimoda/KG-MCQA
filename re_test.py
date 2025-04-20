import json

from kgraph.extraction import extract_triples

with open("wikipedia/rebel/FPAI-20/g/Greta_Thunberg.json", "r") as f:
    data = json.load(f)
    s = data["summary"]

print(s, len(s))

inc = 10
for i in range(1, len(s) // inc):
    s_part = s[: inc * i]
    print("s[: {}] {}".format(inc * i, extract_triples(s_part, "rebel")))
