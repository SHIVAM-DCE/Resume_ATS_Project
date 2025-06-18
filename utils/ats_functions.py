import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def extract_resume_text(pdf_file):
    """
    Extract text from a PDF resume.
    Args:
        pdf_file: Streamlit uploaded file object.
    Returns:
        Extracted text or error message.
    """
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
        if not text.strip():
            return "Error: No text found in the PDF."
        return text.strip()
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def calculate_match_percentage(resume_text, job_description):
    """
    Calculate keyword match percentage between resume and job description.
    Args:
        resume_text: Extracted resume text.
        job_description: Job description text.
    Returns:
        Tuple of (match percentage, set of missing keywords).
    """
    # Clean text: remove punctuation, convert to lowercase
    def clean_text(text):
        text = re.sub(r'[^\w\s]', '', text.lower())
        return set(text.split())

    resume_words = clean_text(resume_text)
    job_words = clean_text(job_description)
    
    if not job_words:
        return 0, set()
    
    common_words = resume_words.intersection(job_words)
    match_percentage = (len(common_words) / len(job_words)) * 100
    missing_keywords = job_words - resume_words
    
    return round(match_percentage, 2), missing_keywords

def analyze_with_gemini(resume_text, job_description):
    """
    Use Gemini Pro to analyze resume suitability.
    Args:
        resume_text: Extracted resume text.
        job_description: Job description text.
    Returns:
        Gemini's analysis or error message.
    """
    try:
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"""
        You are an expert recruiter. Analyze the following resume and job description.
        Provide a concise summary (50-100 words) of the candidate's suitability for the role
        and suggest 1-2 specific improvements for the resume.

        **Resume**: {resume_text[:1500]}...
        **Job Description**: {job_description[:1500]}...

        **Output Format**:
        **Suitability**: [Summary of candidate's fit for the role]
        **Suggestions**: [Specific improvements for the resume]
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error with Gemini API: {str(e)}"