import streamlit as st
import pandas as pd
import io
import google.generativeai as genai
import anthropic
import os
import sys

try:
    from dotenv import load_dotenv
    # Load environment variables
    load_dotenv()
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


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

with st.sidebar:
    st.header("Model Selection")
    model_provider = st.selectbox("Select Model Provider", ["Gemini", "Claude"])

    if model_provider == "Gemini":
        model_name = st.selectbox("Select Gemini Model", ["gemini-1.5-flash", "gemini-1.5-pro"])
    else:
        model_name = st.selectbox("Select Claude Model", ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"])

if "history" not in st.session_state:
    st.session_state.history = []

prompt = st.text_area("Enter your prompt here:", height=150)

if st.button("Generate Response"):
    if not prompt:
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Generating response..."):
            if model_provider == "Gemini":
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key or api_key == "your_gemini_api_key_here":
                    st.error("Please configure GEMINI_API_KEY in the .env file.")
                else:
                    response_text, usage = call_gemini(api_key, model_name, prompt)
                    if usage:
                        input_tokens = usage.prompt_token_count
                        output_tokens = usage.candidates_token_count
                        total_tokens = usage.total_token_count
                        cost = calculate_cost(model_name, input_tokens, output_tokens)
                        st.session_state.history.append({
                            "Model": model_name,
                            "Prompt": prompt,
                            "Response": response_text,
                            "Input Tokens": input_tokens,
                            "Output Tokens": output_tokens,
                            "Total Tokens": total_tokens,
                            "Cost ($)": f"{cost:.6f}"
                        })
                    else:
                        st.error(response_text)
            else:
                api_key = os.getenv("CLAUDE_API_KEY")
                if not api_key or api_key == "your_claude_api_key_here":
                    st.error("Please configure CLAUDE_API_KEY in the .env file.")
                else:
                    response_text, usage = call_claude(api_key, model_name, prompt)
                    if usage:
                        input_tokens = usage.input_tokens
                        output_tokens = usage.output_tokens
                        total_tokens = input_tokens + output_tokens
                        cost = calculate_cost(model_name, input_tokens, output_tokens)
                        st.session_state.history.append({
                            "Model": model_name,
                            "Prompt": prompt,
                            "Response": response_text,
                            "Input Tokens": input_tokens,
                            "Output Tokens": output_tokens,
                            "Total Tokens": total_tokens,
                            "Cost ($)": f"{cost:.6f}"
                        })
                    else:
                        st.error(response_text)

if st.session_state.history:
    st.header("Comparison Table")
    df = pd.DataFrame(st.session_state.history)
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
