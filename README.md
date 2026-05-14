# Financial Statement Analyzer 📈

A free, AI-powered tool to extract key financial metrics from PDF reports and estimate intrinsic value using the Google Gemini API.

## Features

-   **PDF Parsing**: Upload annual reports (10-K, Annual Reports).
-   **AI Extraction**: Uses Gemini Pro/Flash to extract Revenue, EPS, Net Income, etc.
-   **Valuation**: Automatically calculates:
    -   **DCF (Discounted Cash Flow)**
    -   **Graham Number**
-   **Premium UI**: Dark-themed dashboard built with Streamlit.
-   **Completely Free**: Uses the Gemini API Free Tier.

## Tech Stack

-   **Python 3.10+**
-   **Frontend**: Streamlit
-   **AI**: Google Gemini API (`google-generativeai`)
-   **Data Processing**: `pdfplumber`, `pandas`
-   **Visualization**: `plotly`

## Setup Guide

### 1. Get an API Key
Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and create a **free** API key.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
python -m streamlit run app.py
```

### 4. Usage
1.  Enter your API Key in the sidebar (or set it in a `.env` file).
2.  Upload a PDF financial statement.
3.  Click **Analyze Report**.
4.  View extracted metrics and valuation estimates!

## Disclaimer
This tool is for educational purposes only. Do not use AI-generated estimates for financial investment decisions without verification.
