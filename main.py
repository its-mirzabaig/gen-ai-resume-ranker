import os
import io
import fitz  # PyMuPDF
import httpx
import logging
import tempfile
import pandas as pd
from typing import List
from docx import Document
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import SpacyNlpEngine

load_dotenv()  # Load environment variables from .env

# ---------------------- Logging Configuration ----------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------- FastAPI Initialization ---------------------
app = FastAPI()

# ---------------------- API Key Initialization ---------------------
API_KEY = os.getenv("AI_API_KEY")
if not API_KEY:
    raise ValueError("AI_API_KEY is not set")

# ---------------------- Presidio Initialization --------------------
nlp_engine = SpacyNlpEngine()
analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
anonymizer = AnonymizerEngine()

# ---------------------- Models -------------------------------------
class CriteriaResponse(BaseModel):
    criteria: List[str]

# ---------------------- LLM Functions --------------------------
async def call_llm(prompt: str) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    payload = {
        "system_instruction": {"parts": [{"text": "You are a helpful assistant..."}]},
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return {"data": response.json()}
    except httpx.HTTPStatusError as e:
        logger.error(f"LLM call failed with HTTP {e.response.status_code}")
        return {"error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error(f"LLM call general error: {e}")
        return {"error": str(e)}
    
def extract_llm_content(response: dict) -> str:
    try:
        return response["data"]["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Failed to extract LLM content: {e}")
        raise ValueError("Invalid LLM response format")

# ---------------------- File Text Extraction -----------------------
def extract_text_from_pdf(file: UploadFile) -> str:
    try:
        pdf_data = io.BytesIO(file.file.read())
        doc = fitz.open("pdf", pdf_data)
        return "\n".join(page.get_text("text") for page in doc)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise HTTPException(status_code=400, detail="PDF extraction failed")

def extract_text_from_docx(file: UploadFile) -> str:
    try:
        docx_data = io.BytesIO(file.file.read())
        doc = Document(docx_data)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        raise HTTPException(status_code=400, detail="DOCX extraction failed")

def extract_text_from_file(file: UploadFile) -> str:
    if file.filename.endswith('.pdf'):
        return extract_text_from_pdf(file)
    elif file.filename.endswith('.docx'):
        return extract_text_from_docx(file)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

# ---------------------- Anonymization ------------------------------
def anonymize_text(text: str) -> str:
    try:
        pii_entities = analyzer.analyze(
            text=text, language="en", 
            entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "IP_ADDRESS"]
        )
        result = anonymizer.anonymize(text=text, analyzer_results=pii_entities)
        return result.text
    except Exception as e:
        logger.error(f"Anonymization failed: {e}")
        raise HTTPException(status_code=500, detail="PII anonymization failed")

# ---------------------- LLM-Powered Criteria Extraction ------------
async def fetch_criteria_from_text(jd_text: str) -> dict:
    prompt = f"""
Extract the top 5 selection criteria such as education, skills, certifications, experience, and tools from this job description.
Return a plain list of criteria, each on a new line.
Job Description:
{jd_text}
"""
    result = await call_llm(prompt)
    if "error" in result:
        return {"error": result["error"]}
    
    try:
        raw_text = extract_llm_content(result)
        criteria_list = [line.strip() for line in raw_text.split("\n") if line.strip()]
        return {"criteria": criteria_list}
    except Exception as e:
        logger.error(f"LLM response parsing failed: {e}")
        return {"error": "Failed to parse criteria"}

# ---------------------- Resume Scoring -----------------------------
async def score_resume(resume_text: str, criteria_list: List[str]) -> dict:
    try:
        anonymized_text = anonymize_text(resume_text)
        prompt = f"""
Score the resume based on the following criteria on a scale from 0 to 10.
Return only comma-separated scores (e.g., 7,8,6,4,9).

Resume:
{anonymized_text}

Criteria:
{', '.join(criteria_list)}
"""
        result = await call_llm(prompt)
        if "error" in result:
            return {"error": result["error"]}
        
        raw_scores = extract_llm_content(result)
        scores = [int(s.strip()) for s in raw_scores.split(",") if s.strip().isdigit()]

        if len(scores) != len(criteria_list):
            logger.error("Score/criteria mismatch")
            raise HTTPException(status_code=400, detail="Score and criteria count mismatch")

        return {"scores": scores, "criteria": criteria_list}
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        return {"error": str(e)}

# ---------------------- CSV Generation -----------------------------
def generate_scores_csv(data: List[dict], criteria: List[str]) -> str:
    try:
        # Convert the data to a DataFrame
        df = pd.DataFrame(data)
        
        # Add a 'Serial Number' column to maintain the original order (starting from 1)
        df['Serial Number'] = range(1, len(df) + 1)
        
        # Sort the DataFrame by 'Total Score' to rank the resumes
        df['Rank'] = df['Total Score'].rank(ascending=False, method='min').astype(int)
        
        # Sort by 'Rank' (Rank 1 at the top)
        df = df.sort_values(by='Rank', ascending=True)
        
        # Define the file path to save the CSV file
        tmp_dir = tempfile.mkdtemp()
        file_path = os.path.join(tmp_dir, "resume_scores.csv")
        
        # Write the DataFrame to CSV, including Serial Number and Rank
        df.to_csv(file_path, index=False, columns=["Serial Number"] + ["Candidate Name"] + criteria + ["Total Score", "Rank"])
        
        return file_path
    except Exception as e:
        logger.error(f"CSV generation failed: {e}")
        raise HTTPException(status_code=500, detail="CSV generation failed")


# ---------------------- Endpoints ----------------------------------

@app.post("/extract-criteria", response_model=CriteriaResponse)
async def extract_criteria_endpoint(file: UploadFile = File(...)):
    text = extract_text_from_file(file)
    result = await fetch_criteria_from_text(text)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"criteria": result["criteria"]}

@app.post("/score-resumes")
async def score_resumes_endpoint(criteria: List[str], files: List[UploadFile] = File(...)):
    results = []

    for file in files:
        file.file.seek(0)
        text = extract_text_from_file(file)
        result = await score_resume(text, criteria)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        scores = result["scores"]
        results.append({
            "Candidate Name": file.filename.split(".")[0],
            **{criteria[i]: scores[i] for i in range(len(criteria))},
            "Total Score": sum(scores),
        })

    path = generate_scores_csv(results, criteria)
    return {"file_path": path}

@app.post("/extract-and-score")
async def extract_and_score_endpoint(job_description: UploadFile = File(...), files: List[UploadFile] = File(...)):
    jd_text = extract_text_from_file(job_description)
    result = await fetch_criteria_from_text(jd_text)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    criteria = result["criteria"]

    results = []
    for file in files:
        file.file.seek(0)
        text = extract_text_from_file(file)
        scored = await score_resume(text, criteria)
        if "error" in scored:
            raise HTTPException(status_code=400, detail=scored["error"])

        results.append({
            "Candidate Name": file.filename.split(".")[0],
            **{criteria[i]: scored["scores"][i] for i in range(len(criteria))},
            "Total Score": sum(scored["scores"]),
        })

    path = generate_scores_csv(results, criteria)
    return {"file_path": path}
