from sentence_transformers import SentenceTransformer, util
import language_tool_python
import textstat

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
tool = language_tool_python.LanguageTool('en-US')


def compute_similarity(original: str, spun: str) -> float:
    emb1 = model.encode(original[:1000], convert_to_tensor=True)
    emb2 = model.encode(spun[:1000], convert_to_tensor=True)
    score = util.pytorch_cos_sim(emb1, emb2).item()
    return score  # semantic similarity


def grammar_score(text: str) -> float:
    matches = tool.check(text[:1000])
    total_words = len(text.split())
    error_ratio = len(matches) / max(1, total_words)
    return max(0.0, 1.0 - error_ratio)


def readability_score(text: str) -> float:
    flesch = textstat.flesch_reading_ease(text[:1000])
    return min(max(flesch / 100, 0), 1.0)


def reward_function(original: str, spun: str) -> dict:
    sim = compute_similarity(original, spun)
    grammar = grammar_score(spun)
    read = readability_score(spun)

    reward = 0.4 * sim + 0.3 * grammar + 0.3 * read

    return {
        "semantic similarity": round(sim, 3),
        "grammar": round(grammar, 3),
        "readability": round(read, 3),
        "reward": round(reward, 3)
    }


