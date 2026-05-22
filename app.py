import streamlit as st
import pandas as pd
import io
import google.generativeai as genai
import anthropic
import os
import sys

try:
    from dotenv import load_dotenv, find_dotenv
    # Load environment variables
    dotenv_path = find_dotenv()
    LOAD_SUCCESS = load_dotenv(dotenv_path)
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    LOAD_SUCCESS = False
    dotenv_path = "N/A"


st.set_page_config(page_title="Prompt Comparison App", layout="wide")

def call_gemini(api_key, model_name, prompt):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text, response.usage_metadata
    except Exception as e:
        return f"Error: {str(e)}", None

def call_claude(api_key, model_name, prompt):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model_name,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text, message.usage
    except Exception as e:
        return f"Error: {str(e)}", None

def call_llm_judge(provider, model_name, original_prompt, response_text):
    judge_prompt = f"""
    You are an impartial judge evaluating the quality of an AI-generated response.

    Original Prompt: {original_prompt}
    AI Response: {response_text}

    Please evaluate the response based on accuracy, relevance, and completeness.
    Provide a brief justification and a score out of 10.
    """

    if provider == "Gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            return "Error: Gemini API Key not configured", None
        return call_gemini(api_key, model_name, judge_prompt)
    else:
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key or api_key == "your_claude_api_key_here":
            return "Error: Claude API Key not configured", None
        return call_claude(api_key, model_name, judge_prompt)

def calculate_cost(model_name, input_tokens, output_tokens):
    costs = {
        "gemini-1.5-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
        "gemini-1.5-pro": {"input": 3.50 / 1_000_000, "output": 10.50 / 1_000_000},
        "claude-3-5-sonnet-20240620": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
        "claude-3-opus-20240229": {"input": 15.00 / 1_000_000, "output": 75.00 / 1_000_000},
    }

    if model_name in costs:
        input_cost = input_tokens * costs[model_name]["input"]
        output_cost = output_tokens * costs[model_name]["output"]
        return input_cost + output_cost
    return 0.0

st.title("Prompt Comparison App")

if not HAS_DOTENV:
    st.error("The 'python-dotenv' package is not installed or cannot be found.")
    st.info(f"**Current Python Executable:** {sys.executable}")
    st.info(f"**Python Path:** {sys.path}")
    st.warning("Please try running: `pip uninstall dotenv` then `pip install python-dotenv` in your terminal.")
elif not LOAD_SUCCESS:
    st.warning("Failed to load .env file. Please ensure a file named `.env` exists in the same directory as `app.py`.")
    st.info(f"**Attempted .env path:** {dotenv_path}")
    st.info(f"**Current Working Directory:** {os.getcwd()}")
else:
    # Diagnostic: Check if keys are present
    keys_found = []
    if os.getenv("GEMINI_API_KEY"): keys_found.append("GEMINI_API_KEY")
    if os.getenv("CLAUDE_API_KEY"): keys_found.append("CLAUDE_API_KEY")

    if not keys_found:
        st.error("No API keys found in the loaded .env file.")
        st.info(f"**Loaded .env path:** {dotenv_path}")
        st.info("Please ensure the file contains: `GEMINI_API_KEY=...` and `CLAUDE_API_KEY=...`")

with st.sidebar:
    st.header("Model Selection")
    model_provider = st.selectbox("Select Model Provider", ["Gemini", "Claude"])

    if model_provider == "Gemini":
        model_name = st.selectbox("Select Gemini Model", ["gemini-1.5-flash", "gemini-1.5-pro"])
    else:
        model_name = st.selectbox("Select Claude Model", ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"])

    st.header("LLM Judge Configuration")
    enable_judge = st.checkbox("Enable LLM Judge")
    judge_provider = None
    judge_model_name = None
    if enable_judge:
        judge_provider = st.selectbox("Select Judge Provider", ["Gemini", "Claude"], key="judge_provider")
        if judge_provider == "Gemini":
            judge_model_name = st.selectbox("Select Gemini Judge Model", ["gemini-1.5-flash", "gemini-1.5-pro"], key="gemini_judge")
        else:
            judge_model_name = st.selectbox("Select Claude Judge Model", ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"], key="claude_judge")

    st.header("Prompt Optimization")
    optimization_mode = st.checkbox("Optimization Mode (Batch)")
    if optimization_mode:
        uploaded_file = st.file_uploader("Upload Production Data (CSV or Excel)", type=["csv", "xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    prod_data = pd.read_csv(uploaded_file)
                else:
                    prod_data = pd.read_excel(uploaded_file)
                st.success(f"Loaded {len(prod_data)} rows of production data.")
                column_to_use = st.selectbox("Select Column for Prompt Injection", prod_data.columns)
            except Exception as e:
                st.error(f"Error loading file: {e}")

if "history" not in st.session_state:
    st.session_state.history = []

if optimization_mode:
    st.info("In Optimization Mode, use `{{data}}` as a placeholder for production data from your file.")
    prompt = st.text_area("Enter your prompt template here:", height=150, value="Analyze this production data: {{data}}")
else:
    prompt = st.text_area("Enter your prompt here:", height=150)

def process_prompt(prompt_text, model_provider, model_name, enable_judge, judge_provider, judge_model_name):
    response_text = ""
    usage = None
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    cost = 0.0

    if model_provider == "Gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            return "Error: Gemini API Key not configured", None, 0, 0, 0, 0.0
        response_text, usage = call_gemini(api_key, model_name, prompt_text)
        if usage:
            input_tokens = usage.prompt_token_count
            output_tokens = usage.candidates_token_count
            total_tokens = usage.total_token_count
            cost = calculate_cost(model_name, input_tokens, output_tokens)
    else:
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key or api_key == "your_claude_api_key_here":
            return "Error: Claude API Key not configured", None, 0, 0, 0, 0.0
        response_text, usage = call_claude(api_key, model_name, prompt_text)
        if usage:
            input_tokens = usage.input_tokens
            output_tokens = usage.output_tokens
            total_tokens = input_tokens + output_tokens
            cost = calculate_cost(model_name, input_tokens, output_tokens)

    judge_eval = "N/A"
    if usage and enable_judge:
        judge_eval, judge_usage = call_llm_judge(judge_provider, judge_model_name, prompt_text, response_text)
        if judge_usage:
            if judge_provider == "Gemini":
                j_input = judge_usage.prompt_token_count
                j_output = judge_usage.candidates_token_count
            else:
                j_input = judge_usage.input_tokens
                j_output = judge_usage.output_tokens

            cost += calculate_cost(judge_model_name, j_input, j_output)
            input_tokens += j_input
            output_tokens += j_output
            total_tokens += (j_input + j_output)

    return response_text, judge_eval, input_tokens, output_tokens, total_tokens, cost

if st.button("Generate Response" if not optimization_mode else "Run Batch Optimization"):
    if not prompt:
        st.warning("Please enter a prompt.")
    elif optimization_mode and ('uploaded_file' not in locals() or uploaded_file is None):
        st.warning("Please upload a production data file.")
    else:
        if optimization_mode:
            batch_prompts = []
            for _, row in prod_data.iterrows():
                data_val = str(row[column_to_use])
                batch_prompts.append(prompt.replace("{{data}}", data_val))

            progress_bar = st.progress(0)
            for i, p_text in enumerate(batch_prompts):
                with st.spinner(f"Processing item {i+1}/{len(batch_prompts)}..."):
                    res, eval, in_t, out_t, tot_t, c = process_prompt(
                        p_text, model_provider, model_name,
                        enable_judge, judge_provider, judge_model_name
                    )
                    st.session_state.history.append({
                        "Model": model_name,
                        "Prompt": p_text,
                        "Response": res,
                        "Judge Model": judge_model_name if enable_judge else "N/A",
                        "Judge Evaluation": eval,
                        "Input Tokens": in_t,
                        "Output Tokens": out_t,
                        "Total Tokens": tot_t,
                        "Cost ($)": f"{c:.6f}"
                    })
                progress_bar.progress((i + 1) / len(batch_prompts))
            st.success("Batch Optimization Complete!")
        else:
            with st.spinner("Generating response..."):
                res, eval, in_t, out_t, tot_t, c = process_prompt(
                    prompt, model_provider, model_name,
                    enable_judge, judge_provider, judge_model_name
                )
                if in_t > 0 or "Error" not in res:
                    st.session_state.history.append({
                        "Model": model_name,
                        "Prompt": prompt,
                        "Response": res,
                        "Judge Model": judge_model_name if enable_judge else "N/A",
                        "Judge Evaluation": eval,
                        "Input Tokens": in_t,
                        "Output Tokens": out_t,
                        "Total Tokens": tot_t,
                        "Cost ($)": f"{c:.6f}"
                    })
                else:
                    st.error(res)

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)

    if optimization_mode:
        st.header("Optimization Dashboard")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Runs", len(df))
        col2.metric("Total Tokens", df["Total Tokens"].sum())
        col3.metric("Total Cost", f"${df['Cost ($)'].astype(float).sum():.4f}")

        st.subheader("Performance Highlights")
        # Simple heuristic to find poor-performing prompts (e.g., if judge mentioned 'poor' or score < 7)
        poor_mask = df["Judge Evaluation"].str.contains("score: [0-6]/10|poor|incorrect", case=False, na=False)
        if poor_mask.any():
            st.warning("Identified poor-performing responses. Consider experimenting with new prompt templates.")
            st.table(df[poor_mask])
        else:
            st.success("All responses evaluated positively by the judge.")

    st.header("Comparison Table")
    st.table(df)

    # Export to Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Prompt Responses')
    processed_data = output.getvalue()

    st.download_button(
        label="Export to Excel",
        data=processed_data,
        file_name="prompt_comparison.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()
else:
    st.info("No history yet. Enter a prompt and click 'Generate Response'.")
