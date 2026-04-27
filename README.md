<div align="center">

  # ⚠️ PROJECT ARCHIVED ⚠️
  **This project has been migrated and evolved into [Omnius](https://github.com/flxhrdyn/Omnius).**

  > [!IMPORTANT]
  > I have migrated this project from **Streamlit to React** to provide a more robust and premium experience. 
  > This repository is now archived and will no longer receive updates.

  ---

  # News Framing Analysis — Automated Media Intelligence
  **Automated Framing Analysis using Robert Entman's Methodology & LLM Intelligence.**
  
  [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
  [![Groq](https://img.shields.io/badge/Groq_Cloud-F55036?style=for-the-badge&logo=ai&logoColor=white)](https://console.groq.com/)
  [![Llama 3](https://img.shields.io/badge/Llama_3.3-0668E1?style=for-the-badge&logo=meta&logoColor=white)](https://llama.meta.com/)
  [![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![NLTK](https://img.shields.io/badge/NLTK-154F82?style=for-the-badge&logo=python&logoColor=white)](https://www.nltk.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
</div>

---

## Overview

In the era of information overload, understanding how media outlets frame an issue is crucial. **News Framing Analysis** is a media intelligence platform that implements **Robert Entman's (1993)** framing theory automatically to dissect online news narratives.

The application transforms static news text into deep analytical insights, allowing researchers and analysts to comparatively identify problem definitions, causes, moral evaluations, and implied solutions across various media sources.

## Technical Features

- **Automated Framing Intelligence**: Identifies Robert Entman's 4 framing functions (Problem Definition, Causal Interpretation, Moral Evaluation, Treatment Recommendation) using state-of-the-art LLMs.
- **Comparative Analysis Engine**: Generates formal comparative reports to objectively identify divergent perspectives across media outlets.
- **Actor & Sentiment Mapping**: Automatically detects prominent actors (individuals, groups, or institutions) and the underlying sentiment tone of the coverage.
- **Keyword Relationship Graph**: Interactive visualization using **NetworkX** to reveal narrative links between outlets based on shared keyword significance.
- **Premium Design System**: A Streamlit-based interface featuring a custom design system, modern typography (Inter), and optimized instant navigation.
- **Structured Data Validation**: Implements **Pydantic** to ensure LLM outputs are always consistent, validated, and reliable.

## Technology Stack

### Intelligence & Backend
- **Core Engine**: Python 3.12+
- **LLM Orchestration**: Groq SDK (Llama 3.3-70B, Llama 3.1-8B, Qwen)
- **NLP Processing**: NLTK (Stopwords removal), Scikit-learn (TF-IDF Vectorization)
- **Web Intelligence**: BeautifulSoup4 (Advanced scraping with garbage filtering)
- **Validation**: Pydantic v2

### Frontend & Visualization
- **Framework**: Streamlit (Custom Premium CSS)
- **Data Visualization**: Matplotlib, NetworkX (Graph Analysis)
- **Language Detection**: Langdetect

## System Architecture

```mermaid
graph TD
    subgraph Input_Layer [Input Layer]
        URL[News URLs] -->|Scrape| SCR[BS4 Scraper]
        TXT[Manual Text] -->|Process| SCR
    end
    
    subgraph Analysis_Layer [AI Processing]
        SCR -->|Clean Text| LLM[Groq AI Engine]
        LLM -->|Validate| PYD[Pydantic Models]
        PYD -->|Framing| FRM[Entman Analysis]
        PYD -->|Actors| ACT[Actor Mapping]
        PYD -->|Sentiment| SNT[Sentiment Detection]
    end
    
    subgraph Visualization_Layer [Intelligence Output]
        FRM -->|Compare| UI[Streamlit Dashboard]
        ACT -->|Display| UI
        SCR -->|TF-IDF| GRPH[Keyword Network Graph]
        GRPH -->|Visual| UI
    end
```

---

## Performance & Methodology

This application is developed with a strict focus on methodological accuracy according to Robert Entman's paradigm.

### Core Metrics & Capabilities
| Parameter | Value | Description |
| :--- | :--- | :--- |
| **Methodology** | **Robert Entman** | 4-Function Framing Analysis |
| **Processing Speed** | **< 5 seconds** | Per article analysis using Groq LPU |
| **Max Capacity** | **3,000 Words** | Optimized for long-form investigative news |
| **Data Validation** | **Pydantic** | Zero-failure structured output assurance |
| **Visual Engine** | **NetworkX** | Relationship graph for narrative links |

---

## Deployment Guide

### Prerequisites
*   Python 3.12+
*   Groq Cloud API Key
*   NLTK Corpora (Automated download)

### Execution Procedures

**Step 1: Environment Setup**
```bash
# Clone the repository
git clone https://github.com/flxhrdyn/Gemini-News-Framing-Analysis.git
cd Gemini-News-Framing-Analysis

# Setup project and install all dependencies automatically
uv sync
```

**Step 2: Configuration**
Create a `.streamlit/secrets.toml` file and add your API Key:
```toml
GROQ_API_KEY = "gsk_..."
```

**Step 3: Run Application**
```bash
uv run streamlit run app.py
```

**Step 4: Docker (Optional)**
If you prefer using Docker, you can build and run the containerized version:
```bash
# Build the image
docker build -t news-framing-analysis .

# Run the container
docker run -p 8501:8501 news-framing-analysis
```

---

## Configuration

The application can be configured via the sidebar and internal configuration files:
- `AVAILABLE_MODELS`: List of supported models (Llama 3.3, 3.1, Qwen).
- `MAX_ARTICLE_WORDS`: Word limit for API processing (Default: `3000`).
- `CUSTOM_STOPWORDS`: Keyword filters specifically tuned for Indonesian and Global media.

---

## Author

**Felix Hardyan**
*   [Omnius (New Project)](https://github.com/flxhrdyn/Omnius)
*   [GitHub](https://github.com/flxhrdyn)
*   [Hugging Face](https://huggingface.co/felixhrdyn)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
