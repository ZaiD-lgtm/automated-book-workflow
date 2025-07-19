import datetime
import json
import os
import re

import yaml
import asyncio

from AI_Agent.RL_Reward import reward_function
from AI_Agent.writer import generate
from web_scraping.scraper import fetch_chapter
from AI_Agent.reviewer import reviewer
search_path = "search.yaml"

with open(search_path, "r") as file:
    data = yaml.safe_load(file)
url = data["url"]
# url = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"
title, content = asyncio.run(fetch_chapter(url))
# print(f"title: {title}")
# print(f"content: {content}")

def gen_and_review(title, content):
    ai_written, content = generate(title,content)


    review = reviewer(content, ai_written, title)
    score_dict = parse_reviewer_scores(review)
    reviewer_Coherence = score_dict["Coherence"]
    reviewer_Readability = score_dict["Readability"]
    reviewer_Grammar = score_dict["Grammar"]
    reviewer_Faithfulness = score_dict["Faithfulness"]
    reviewer_Creativity = score_dict["Creativity"]
    reviewer_TotalScore = score_dict["Total Score"]  # reward1
    reward1 = reviewer_TotalScore

    scores = reward_function(content, ai_written)
    semantic_similarity = scores["semantic similarity"]
    grammar = scores["grammar"]
    readability = scores["readability"]
    reward2 = scores["reward"]

    total_reward = reward1 * .5 + (reward2 / 50) * .5  ## out of 1
    return ai_written, review, reviewer_Coherence, reviewer_Readability, reviewer_Grammar, reviewer_Faithfulness, reviewer_Creativity, reviewer_TotalScore, semantic_similarity, grammar, readability, reward2, total_reward

def parse_reviewer_scores(text: str) -> dict:
    pattern = r"(Coherence|Readability|Grammar|Faithfulness|Creativity|Total Score):\s*(\d+)"
    matches = re.findall(pattern, text)

    score_dict = {}
    for key, value in matches:
        score_dict[key] = int(value)

    return score_dict


ai_written, review, reviewer_Coherence, reviewer_Readability, reviewer_Grammar, reviewer_Faithfulness, reviewer_Creativity, reviewer_TotalScore, semantic_similarity, grammar, readability, reward2, total_reward = gen_and_review(title, content)
print("successfully ran gen and review")


ai_written, review, reviewer_Coherence, reviewer_Readability, reviewer_Grammar, reviewer_Faithfulness, reviewer_Creativity, reviewer_TotalScore, semantic_similarity, grammar, readability, reward2, total_reward = gen_and_review(title, content)

reward_threshold = .8
max_retries = 3

best_ai_written = ai_written
best_review = review
best_reviewer_Coherence = reviewer_Coherence
best_reviewer_Readability = reviewer_Readability
best_reviewer_Grammar = reviewer_Grammar
best_reviewer_Faithfulness = reviewer_Faithfulness
best_reviewer_Creativity = reviewer_Creativity
best_reviewer_TotalScore = reviewer_TotalScore
best_semantic_similarity = semantic_similarity
best_grammar = grammar
best_readability = readability
best_reward_llm = reward2
best_total_reward = total_reward

print(f"Initial attempt - Total Reward: {total_reward:.3f}")

for i in range(1, max_retries + 1):
    if total_reward >= reward_threshold:
        break
    else:
        current_ai_written, current_review, current_reviewer_Coherence, current_reviewer_Readability,current_reviewer_Grammar, current_reviewer_Faithfulness, current_reviewer_Creativity, current_reviewer_TotalScore, current_semantic_similarity, current_grammar,current_readability, current_reward_llm, current_total_reward = gen_and_review(title, content)

        if current_total_reward > best_total_reward:
            best_ai_written = current_ai_written
            best_review = current_review
            best_reviewer_Coherence = current_reviewer_Coherence
            best_reviewer_Readability = current_reviewer_Readability
            best_reviewer_Grammar = current_reviewer_Grammar
            best_reviewer_Faithfulness = current_reviewer_Faithfulness
            best_reviewer_Creativity = current_reviewer_Creativity
            best_reviewer_TotalScore = current_reviewer_TotalScore
            best_semantic_similarity = current_semantic_similarity
            best_grammar = current_grammar
            best_readability = current_readability
            best_reward_llm = current_reward_llm
            best_total_reward = current_total_reward

        total_reward = current_total_reward


total_reward = best_total_reward
reward2 = best_reward_llm
readability = best_readability
grammar = best_grammar
semantic_similarity = best_semantic_similarity
reviewer_TotalScore = best_reviewer_TotalScore
reviewer_Creativity = best_reviewer_Creativity
reviewer_Faithfulness = best_reviewer_Faithfulness
reviewer_Grammar = best_reviewer_Grammar
reviewer_Readability = best_reviewer_Readability
reviewer_Coherence = best_reviewer_Coherence
review = best_review
ai_written = best_ai_written


reward_json = "reward.json"

data = {
    "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
    "ai_written": ai_written,
    "review": review,
    "reviewer_Coherence": reviewer_Coherence,
    "reviewer_Readability": reviewer_Readability,
    "reviewer_Grammar": reviewer_Grammar,
    "reviewer_Faithfulness": reviewer_Faithfulness,
    "reviewer_Creativity": reviewer_Creativity,
    "reviewer_TotalScore": reviewer_TotalScore,
    "semantic_similarity": semantic_similarity,
    "grammar_score_from_tool": grammar,
    "readability_score_from_tool": readability,
    "llm_internal_reward": reward2,
    "total_combined_reward": total_reward
}

existing_rewards = []
if os.path.exists(reward_json):

    with open(reward_json, 'r', encoding='utf-8') as f:
        existing_rewards = json.load(f)
        if not isinstance(existing_rewards, list):
            existing_rewards = [existing_rewards]

existing_rewards.append(data)

with open(reward_json, 'w', encoding='utf-8') as f:
    json.dump(existing_rewards, f, indent=4, ensure_ascii=False)

now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
file_id = title.replace(" ", "_").replace("/", "-")[:50]
rewritten_path = os.path.join("AI_Agent", f"{file_id}_{now}_rewritten.json")
yaml_file_path = "search.yaml"
with open(yaml_file_path, 'r', encoding='utf-8') as f:
    yaml_data = yaml.safe_load(f)

yaml_data['path'] = rewritten_path
with open(yaml_file_path, 'w', encoding='utf-8') as f:
    yaml.safe_dump(yaml_data, f, indent=2, default_flow_style=False, allow_unicode=True)

data = {
    "title": title,
    "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
    "ai_written": ai_written,
    "review": review,
    "content": content,
    "Total Score": total_reward,

}
with open(rewritten_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

streamlit_script_path = "user_review.py"



