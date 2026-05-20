# Prompt Comparison App

A Streamlit-based web application to facilitate user entry of prompts, dynamic changing of prompts, and comparison of results across different LLM models (Google Gemini and Anthropic Claude).

## Features

- **Prompt Comparison**: Compare responses from different models for the same or different prompts.
- **Model Selection**: Choose between Google Gemini (1.5 Flash, 1.5 Pro) and Anthropic Claude (3.5 Sonnet, 3 Opus).
- **Usage Tracking**: Automatically calculates token usage and cost for each model call.
- **LLM Judge**: Validate responses using an automated LLM judge (Gemini, Claude, or Arize Phoenix).
- **Prompt Optimization**: Run batch tests against production data (CSV/Excel) using prompt templates.
- **Arize Phoenix Integration**: Advanced observability and tracing for all LLM calls.
- **Export to Excel**: Export your prompt history, responses, and usage data to an Excel spreadsheet.
- **Session History**: Maintain a history of your current session's prompts and responses in a tabular format.

## Setup

### Prerequisites

- Python 3.10 or higher
- API keys for Google Gemini and/or Anthropic Claude

### Installation

1. Clone the repository (if applicable) or download the source code.
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

*Note: Make sure you install `python-dotenv`, not the `dotenv` package.*

3. Create a `.env` file in the root directory and add your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here
```

## Features Detail

### Prompt Optimization Mode
Identify poor-performing prompts by uploading a production dataset (CSV or Excel). Use the `{{data}}` placeholder in your prompt template to dynamically inject row values and run batch evaluations.

### Arize Phoenix Observability
All LLM calls are instrumented using Arize Phoenix. View detailed traces, latency, and token usage by clicking the Phoenix UI link in the sidebar (defaults to `http://localhost:6006`).

## Usage

1. Run the Streamlit application:

```bash
streamlit run app.py
```

2. Open the application in your browser (usually at `http://localhost:8501`).
3. Select your desired model provider and model in the sidebar.
5. Enter your prompt in the main area and click **Generate Response**.
6. View the results in the comparison table below.
7. Click **Export to Excel** to download your session history.

## Cost Calculation

Costs are calculated based on the following (approximate) rates per million tokens:

| Model | Input Cost ($/1M) | Output Cost ($/1M) |
|-------|-------------------|--------------------|
| gemini-1.5-flash | 0.075 | 0.30 |
| gemini-1.5-pro | 3.50 | 10.50 |
| claude-3-5-sonnet | 3.00 | 15.00 |
| claude-3-opus | 15.00 | 75.00 |

## License

MIT
