# ◈ Truth Layer – PDF Fact Checker

> AI-powered PDF fact-verification platform. Upload any PDF and instantly detect false, outdated, or misleading claims using live web search + LLM reasoning.

---

## 🚀 Features

| Feature | Details |
|---|---|
| **PDF Upload & Parse** | PyMuPDF + pdfplumber with OCR fallback |
| **Claim Extraction** | LLM identifies statistics, dates, financial figures, technical claims |
| **Live Web Verification** | Tavily / DuckDuckGo / SerpAPI search |
| **AI Verdict** | VERIFIED / INACCURATE / FALSE with confidence score |
| **Corrected Facts** | Provides accurate replacement for wrong claims |
| **Evidence Panel** | Source URLs and snippets for every verdict |
| **Report Export** | CSV, JSON, and branded HTML report |
| **Source Credibility** | Prioritises government, research, and tier-1 media |

---

## 📦 Installation

```bash
# 1. Clone / download the project
cd truth-layer

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env and fill in your keys

# 5. Run the app
streamlit run app.py
```

---

## 🔑 API Keys

| Key | Required? | Where to get |
|---|---|---|
| `GEMINI_API_KEY` | Recommended | [aistudio.google.com](https://aistudio.google.com) |
| `OPENAI_API_KEY` | Alternative | [platform.openai.com](https://platform.openai.com) |
| `TAVILY_API_KEY` | Optional | [tavily.com](https://tavily.com) |
| `SERPAPI_KEY` | Optional | [serpapi.com](https://serpapi.com) |

> **DuckDuckGo search is free and requires no API key** — perfect for getting started.

---

## 🏗️ Architecture

```
PDF Upload
    ↓
Text Extraction (PyMuPDF / pdfplumber)
    ↓
Claim Extractor Agent (LLM prompt → JSON claims)
    ↓
Search Agent (Tavily / DDG per claim)
    ↓
Verifier Agent (LLM + evidence → verdict)
    ↓
Report Agent (CSV / JSON / HTML)
    ↓
Streamlit Dashboard
```

---

## 📁 Project Structure

```
truth-layer/
├── app.py                  # Main Streamlit application
├── requirements.txt
├── .env.example
├── README.md
├── agents/
│   ├── extractor.py        # Claim Extractor Agent
│   ├── search_agent.py     # Web Search Agent
│   ├── verifier.py         # Verification Agent
│   └── report_agent.py     # Report Generator Agent
├── utils/
│   ├── pdf_parser.py       # PDF text extraction
│   ├── web_search.py       # Multi-provider search
│   └── helpers.py          # CSS, formatters
└── outputs/                # Generated reports
```

---

## 🎯 Supported Claim Types

- **Statistics** – percentages, growth rates, rankings
- **Financial** – revenue, market cap, funding amounts
- **Market Size** – TAM projections, industry forecasts
- **Dates** – product launches, policy dates, historical events
- **Technical** – AI benchmarks, performance claims
- **Scientific** – research findings, health claims
- **Demographic** – population figures, user counts

---

## 📊 Output Format

```json
{
  "claim": "India has 500 million internet users",
  "status": "INACCURATE",
  "confidence": 92,
  "corrected_fact": "India had over 950 million internet users in 2025.",
  "evidence": [
    {
      "source": "TRAI Report 2025",
      "url": "https://trai.gov.in/...",
      "snippet": "India's internet subscriber base crossed 950 million..."
    }
  ],
  "reasoning": "The claim underestimates India's internet user base by nearly half."
}
```

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **LLM**: Google Gemini 1.5 Flash / OpenAI GPT-4o Mini
- **Search**: Tavily · DuckDuckGo · SerpAPI
- **PDF**: PyMuPDF · pdfplumber
- **Charts**: Plotly
- **Data**: Pandas

---

## 📄 License

MIT License – free for personal, educational, and commercial use.

---

*Built with ❤️ for hackathons, demos, and production deployments.*
