import gradio as gr
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google GenAI
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def generate_response(prompt):
    if not api_key or api_key == "your_gemini_api_key_here":
        return "Error: GEMINI_API_KEY not configured in .env file."

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio Interface
demo = gr.Interface(
    fn=generate_response,
    inputs=gr.Textbox(lines=5, label="Enter your prompt here"),
    outputs=gr.Textbox(label="AI Response"),
    title="Google GenAI Prompt Interface",
    description="Enter a prompt to see the response from Google's Gemini model."
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
