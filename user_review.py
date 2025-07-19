import os
import streamlit as st
import json
import re
import yaml
from AI_Agent.RL_Reward import reward_function
from AI_Agent.writer import generate
from AI_Agent.reviewer import reviewer
from chromadb.utils import embedding_functions
import chromadb
from datetime import datetime

def get_llm_feedback(review_text: str) -> str:
    pattern = r"Total Score:\s*\d+/50\s*\n\n(.*)"
    match = re.search(pattern, review_text, re.DOTALL)
    if match:
        feedback = match.group(1).strip()
        return feedback
    return "Feedback not found."


def parse_reviewer_scores(text: str) -> dict:
    pattern = r"(Coherence|Readability|Grammar|Faithfulness|Creativity|Total Score):\s*(\d+)"
    matches = re.findall(pattern, text)
    score_dict = {key: int(value) for key, value in matches}
    return score_dict


def load_chapter_data():
    path_to_rewritten_chapter = "search.yaml"
    yaml_data = {}

    with open(path_to_rewritten_chapter, 'r', encoding='utf-8') as f:
        existing_data = yaml.safe_load(f)
        if existing_data:
            yaml_data = existing_data

    rewritten_json_path = yaml_data["path"]

    if not os.path.exists(rewritten_json_path):
        st.error("Rewritten path not found!")

    with open(rewritten_json_path, "r", encoding='utf-8') as file:
        data = json.load(file)
        return data


def initialize_session_state(data):
    if data:
        if 'original_text' not in st.session_state:
            st.session_state.original_text = data["content"]
        if 'AI_rewritten' not in st.session_state:
            st.session_state.AI_rewritten = data["ai_written"]
        if 'AI_review' not in st.session_state:
            st.session_state.AI_review = data["review"]
        if 'chapter_title' not in st.session_state:
            st.session_state.chapter_title = data["title"]
        if 'review_score' not in st.session_state:
            st.session_state.review_score = int(parse_reviewer_scores(st.session_state.AI_review)["Total Score"])
        if 'rl_reward' not in st.session_state:
            st.session_state.rl_reward = reward_function(st.session_state.original_text, st.session_state.AI_rewritten)["reward"]
        if 'current_action' not in st.session_state:
            st.session_state.current_action = "None"
        if 'edited_text_display' not in st.session_state:
            st.session_state.edited_text_display = st.session_state.AI_rewritten
        if 'comments' not in st.session_state:
            st.session_state.comments = ""
    else:
        st.error("Failed to load chapter data. Please check your files.")
        st.stop()


def handle_regeneration(feedback_type="llm"):
    title = st.session_state.chapter_title
    content = st.session_state.original_text

    if feedback_type == "llm":
        llm_feedback = get_llm_feedback(st.session_state.AI_review)
        additional_prompt = f"The Following is the feedback from an llm. Understand it and generate by understanding the areas of improvement|| LLM Feedback: {llm_feedback}"
    else:
        additional_prompt = f"Based on the following feedback rewrite the original chapter: {st.session_state.comments}"

    with st.spinner("Generating new response..."):
        new_AI_rewritten_list, new_AI_review = gen_response_review(title, content, additional_prompt=additional_prompt)
        new_AI_rewritten = new_AI_rewritten_list[0]

    new_review_score = int(parse_reviewer_scores(new_AI_review)["Total Score"])
    new_result = reward_function(st.session_state.original_text, new_AI_rewritten, title)
    new_rl_reward = new_result["reward"]

    st.session_state.temp_new_AI_rewritten = new_AI_rewritten
    st.session_state.temp_new_review_score = new_review_score
    st.session_state.temp_new_rl_reward = new_rl_reward
    st.session_state.show_regenerated_option = True


def gen_response_review(title, content, additional_prompt=""):
    mistral_response = generate(title, content, additional_prompt)
    if mistral_response is None:
        st.error("Unable to get response from AI writer!")
        return ["", ""]

    gemini_review = reviewer(content, mistral_response,title)
    if gemini_review is None:
        st.error("Unable to get review from AI reviewer!")
        return mistral_response, ""

    return mistral_response, gemini_review


def main():
    st.set_page_config(layout="wide", page_title="AI Chapter Review System")
    st.title(st.session_state.chapter_title if 'chapter_title' in st.session_state else "AI Chapter Review System")

    # Display Original Chapter
    st.subheader("Original Chapter")
    st.text_area("Original", st.session_state.original_text, height=300, disabled=True, key="original_chapter_text_area")

    st.markdown("---")

    st.subheader("AI-Written Chapter")
    st.session_state.edited_text_display = st.text_area("AI", st.session_state.edited_text_display, height=300, disabled=True, key="ai_written_text_area")

    st.markdown(f"**Reviewer Score:** {st.session_state.review_score} / 50")
    st.markdown(f"**RL Reward:** {st.session_state.rl_reward:.2f}")
    total_reward = (st.session_state.rl_reward * 0.5) + ((st.session_state.review_score / 50) * 0.5)
    st.markdown(f"**Total Reward:** {total_reward:.2f}")
    st.session_state.total_reward = total_reward

    st.markdown("---")

    action_options = ["Accept", "Edit", "Regenerate Better Response (LLM Feedback)", "Feedback (Human Input)", "Reject"]
    selected_action = st.radio("Choose Action", action_options, key="main_action_radio")

    if selected_action == "Edit":
        st.session_state.edited_text_display = st.text_area("Edit the Text", st.session_state.AI_rewritten, height=300, key="edit_text_area")
        st.session_state.current_action = "Edit"
        st.session_state.comments = "Human edited."

    elif selected_action == "Regenerate Better Response (based on llm feedback)":
        st.session_state.current_action = "Regenerate Better Response"
        if st.button("Generate based on LLM Feedback", key="generate_llm_btn"):
            handle_regeneration(feedback_type="llm")

    elif selected_action == "Regenerate (Human Feedback)":

        st.session_state.current_action = "Feedback"

        st.session_state.comments = st.text_area("Enter your feedback for regeneration:", st.session_state.comments,
                                                 key="human_feedback_text_area")

        if st.button("Generate based on Human Feedback", key="generate_human_btn"):
            if st.session_state.comments.strip():
                handle_regeneration(feedback_type="human")
            else:
                st.warning("Please provide feedback to regenerate the response.")


    elif selected_action == "Accept":
        st.session_state.current_action = "Accept"
        st.session_state.edited_text_display = st.session_state.AI_rewritten
        st.session_state.comments = "Accepted as is."

    elif selected_action == "Reject":
        st.session_state.current_action = "Reject"
        st.session_state.edited_text_display = ""
        st.session_state.comments = "Rejected."

    if st.session_state.get('show_regenerated_option', False):
        st.markdown("---")
        st.subheader("Newly Generated AI-Written Chapter")
        st.text_area("New AI", st.session_state.temp_new_AI_rewritten, height=300, disabled=True, key="new_ai_text_area")
        st.markdown(f"**New Reviewer Score:** {st.session_state.temp_new_review_score} / 50")
        st.markdown(f"**New RL Reward:** {st.session_state.temp_new_rl_reward:.2f}")
        new_total_reward = (st.session_state.temp_new_rl_reward * 0.5) + ((st.session_state.temp_new_review_score / 50) * 0.5)
        st.markdown(f"**New Total Reward:** {new_total_reward:.2f}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Accept New Response", key="accept_new_response"):
                st.session_state.AI_rewritten = st.session_state.temp_new_AI_rewritten
                st.session_state.AI_review = reviewer(st.session_state.original_text, st.session_state.AI_rewritten)
                st.session_state.review_score = st.session_state.temp_new_review_score
                st.session_state.rl_reward = st.session_state.temp_new_rl_reward
                st.session_state.edited_text_display = st.session_state.temp_new_AI_rewritten
                st.session_state.total_reward = new_total_reward
                st.session_state.current_action = "Accepted Regenerated"
                st.session_state.comments = "Regenerated content accepted."
                st.session_state.show_regenerated_option = False
                st.experimental_rerun()
        with col2:
            if st.button("Discard New Response", key="discard_new_response"):
                st.session_state.show_regenerated_option = False
                st.session_state.comments = "Regenerated content discarded."
                st.experimental_rerun()

    st.markdown("---")

    if st.button("✅ Submit Decision", key="submit_decision_button"):
        decision = {
            "action": st.session_state.current_action,
            "original": st.session_state.original_text,
            "final_text": st.session_state.edited_text_display,
            "comments": st.session_state.comments,
            "review_score": st.session_state.review_score,
            "rl_reward": st.session_state.rl_reward,
            "total_reward": st.session_state.total_reward,
        }
        st.success("✅ Decision submitted!")
        st.json(decision)

        json_dir = "final_edited_text.json"
        logs = []

        if os.path.exists(json_dir) and os.path.getsize(json_dir) > 0:
            with open(json_dir, "r", encoding="utf-8") as f:
                logs = json.load(f)
            if not isinstance(logs, list):
                st.warning(f"'{json_dir}' contained non-list JSON. Re-initializing.")
                logs = []

        logs.append(decision)

        with open(json_dir, "w", encoding="utf-8") as file:
            json.dump(logs, file, indent=2)
        st.success(f"Decision saved to {json_dir}")


if __name__ == "__main__":

    if 'data_loaded' not in st.session_state:
        chapter_data = load_chapter_data()
        if chapter_data:
            initialize_session_state(chapter_data)
            st.session_state.data_loaded = True
        else:
            st.error("Application cannot proceed without chapter data.")
            st.stop()
    main()