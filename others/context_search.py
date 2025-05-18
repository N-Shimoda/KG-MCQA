from sentence_transformers import SentenceTransformer, util

import wikipedia

select = 5

model = SentenceTransformer("all-MiniLM-L6-v2")
context = [
    "Vine was a short-form video app that became popular for its six-second videos before being discontinued in 2017.",
    "One of Michelangelo’s most renowned marble sculptures is the david, which displays detailed human anatomy and emotion.",  # noqa E501
    "Parasite made history by becoming the first non-English-language film to win Best Picture at the 2020 Academy Awards.",  # noqa E501
    "Apple introduced the first iPhone in 2007, marking a major milestone in smartphone technology and changing mobile communication forever.",  # noqa E501
    "Fortnite became popular for its battle royale gameplay that combines shooting mechanics with unique building features during fights.",  # noqa E501
    "Chris Pratt provided the voice for the beloved video game character Mario in the 2023 animated film adaptation.",
][select]
word = ["Vine", "David", "Parasite", "Apple", "Battle Royale", "Mario"][select]

print("Word:", word)
print("Context:", context)

# Wikipedia 検索
candidates = wikipedia.search(word, results=10)
print("Candidates:", candidates)

# 文脈ベクトル
context_embedding = model.encode(context, convert_to_tensor=True)

# 候補ページとスコアを比較
best_match = None
best_score = -1

summaries = []
valid_titles = []
for title in candidates:
    try:
        summary = wikipedia.summary(title, sentences=3)
        summaries.append(summary)
        valid_titles.append(title)
    except Exception:
        continue

print("Summaries:", summaries)
if summaries:
    summary_embeddings = model.encode(summaries, convert_to_tensor=True)
    scores = util.pytorch_cos_sim(context_embedding, summary_embeddings)[0]
    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()
    best_match = valid_titles[best_idx]

print(f"Best match: {best_match} (score: {best_score})")
