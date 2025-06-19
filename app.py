import streamlit as st
import json
from utils.ats_functions import extract_resume_text, analyze_with_gemini
import re
import time
import os
from huggingface_hub import InferenceClient

# Load the JSON file containing IT roles and skills
try:
    with open('Imp_skills.json', 'r') as file:
        it_roles_skills = json.load(file)
except FileNotFoundError:
    st.error("Error: 'Imp_skills.json' file not found. Please ensure it is in the same directory as this script.")
    st.stop()

# Set page configuration with a modern theme
st.set_page_config(
    page_title="Resume ATS Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for god-level UI
st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%);
        padding: 20px;
        color: #e5e7eb;
    }
    .stButton>button {
        background: linear-gradient(45deg, #8b5cf6, #ec4899);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 1.1em;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
        background: linear-gradient(45deg, #a78bfa, #f472b6);
    }
    .keyword-badge, .skill-badge, .resume-keyword-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.1);
        color: #ffffff;
        padding: 6px 12px;
        border-radius: 16px;
        margin: 5px;
        font-size: 0.95em;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .skill-badge {
        background: rgba(34, 197, 94, 0.2);
        color: #a3e635;
    }
    .resume-keyword-badge {
        background: rgba(59, 130, 246, 0.2);
        color: #93c5fd;
    }
    .section-header {
        font-size: 1.8em;
        font-weight: 700;
        color: #ffffff;
        margin-top: 30px;
        margin-bottom: 15px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    .sub-section-header {
        font-size: 1.4em;
        font-weight: 600;
        color: #ffffff;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    .stTextArea textarea, .stFileUploader {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        padding: 15px;
        color: #ffffff;
        font-size: 1em;
        box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.2);
        transition: all 0.3s;
    }
    .stTextArea textarea:focus, .stFileUploader:focus {
        border-color: #a78bfa;
        box-shadow: 0 0 10px rgba(167, 139, 250, 0.5);
    }
    .stSpinner > div {
        color: #ec4899;
    }
    .card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .progress-circle {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 120px;
        height: 120px;
        background: conic-gradient(#8b5cf6 calc(var(--percentage) * 3.6deg), rgba(255, 255, 255, 0.1) 0deg);
        border-radius: 50%;
        position: relative;
        margin: 20px auto;
    }
    .progress-circle::before {
        content: attr(data-text);
        position: absolute;
        background: rgba(255, 255, 255, 0.05);
        width: 90px;
        height: 90px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5em;
        font-weight: 600;
        color: #ffffff;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    .footer {
        text-align: center;
        color: rgba(255, 255, 255, 0.7);
        margin-top: 50px;
        font-size: 0.95em;
        font-style: italic;
    }
    .sidebar .stMarkdown {
        color: #e5e7eb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar for instructions with a futuristic touch
with st.sidebar:
    st.markdown(
        "<h2 style='color: #ffffff; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);'>Resume ATS Tracker</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style='background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1);'>
            <strong style='color: #a78bfa;'>How to Use:</strong><br>
            1. Enter a job description.<br>
            2. Upload a text-based PDF resume.<br>
            3. Click "Analyze Resume" to view:<br>
               - Keyword match percentage<br>
               - Missing keywords (from job description only)<br>
               - AI-powered suitability analysis<br>
               - Extracted skills (from Imp_skills.json)<br>
               - ATS keywords from job description and resume
        </div>
        <div style='margin-top: 15px; color: #d1d5db;'>
            <strong>Note:</strong> Use text-based PDFs for best results.
        </div>
        """,
        unsafe_allow_html=True,
    )

# Main title and description with a glowing effect
st.markdown(
    """
    <h1 style='text-align: center; color: #ffffff; font-size: 2.5em; text-shadow: 0 0 15px rgba(167, 139, 250, 0.7);'>
        Resume ATS Tracking System
    </h1>
    <p style='text-align: center; color: rgba(255, 255, 255, 0.9); font-size: 1.2em; margin-bottom: 30px;'>
        Unleash the power of AI to analyze your resume against job descriptions with precision and style.
        Powered by Google Gemini Pro and ATS-optimized IT skills.
    </p>
    """,
    unsafe_allow_html=True,
)

# Input section with neumorphic cards
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("<div class='section-header'>Job Description</div>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        job_description = st.text_area(
            "",
            height=300,
            placeholder="e.g., Seeking a Python developer with expertise in NLP, web development, and cloud platforms...",
            key="job_desc",
        )
        if job_description:
            def extract_keywords(text):
                # Initialize sets for each category
                technical_skills = set()
                soft_skills = set()
                tools = set()
                
                # Collect all keywords from JSON
                for role in it_roles_skills.values():
                    technical_skills.update(role.get("Technical Skills", []))
                    soft_skills.update(role.get("Soft Skills", []))
                    tools.update(role.get("Tools", []))
                
                # Extract keywords by category
                found_technical = set()
                found_soft = set()
                found_tools = set()
                text_lower = text.lower()
                
                for skill in technical_skills:
                    if skill.lower() in text_lower:
                        found_technical.add(skill)
                for skill in soft_skills:
                    if skill.lower() in text_lower:
                        found_soft.add(skill)
                for tool in tools:
                    if tool.lower() in text_lower:
                        found_tools.add(tool)
                
                # Combine all keywords for comparison purposes
                all_keywords = found_technical.union(found_soft).union(found_tools)
                
                return {
                    "Technical Skills": sorted(list(found_technical)),
                    "Soft Skills": sorted(list(found_soft)),
                    "Tools": sorted(list(found_tools)),
                    "All Keywords": sorted(list(all_keywords))
                }
            
            job_keywords = extract_keywords(job_description)
            st.markdown("<strong style='color: #ffffff;'>Extracted ATS Keywords from Job Description:</strong>", unsafe_allow_html=True)
            
            # Display keywords horizontally in three columns
            col_tech, col_soft, col_tools = st.columns(3)
            with col_tech:
                st.markdown("<div class='sub-section-header'>Technical Skills</div>", unsafe_allow_html=True)
                if job_keywords["Technical Skills"]:
                    for keyword in job_keywords["Technical Skills"]:
                        st.markdown(f"<span class='keyword-badge'>{keyword}</span>", unsafe_allow_html=True)
                else:
                    st.info("No Technical Skills found.", icon="ℹ️")
            with col_soft:
                st.markdown("<div class='sub-section-header'>Soft Skills</div>", unsafe_allow_html=True)
                if job_keywords["Soft Skills"]:
                    for keyword in job_keywords["Soft Skills"]:
                        st.markdown(f"<span class='keyword-badge'>{keyword}</span>", unsafe_allow_html=True)
                else:
                    st.info("No Soft Skills found.", icon="ℹ️")
            with col_tools:
                st.markdown("<div class='sub-section-header'>Tools Requirements</div>", unsafe_allow_html=True)
                if job_keywords["Tools"]:
                    for keyword in job_keywords["Tools"]:
                        st.markdown(f"<span class='keyword-badge'>{keyword}</span>", unsafe_allow_html=True)
                else:
                    st.info("No Tools found.", icon="ℹ️")
        
        st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='section-header'>Upload Resume</div>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        resume_file = st.file_uploader(
            "",
            type=["pdf"],
            help="Upload a text-based PDF resume for analysis.",
            key="resume_upload",
        )
        if resume_file:
            with st.spinner("Extracting resume text..."):
                resume_text = extract_resume_text(resume_file)
                time.sleep(1)  # Simulate processing for UX
            if "Error" not in resume_text:
                resume_keywords = extract_keywords(resume_text)
                st.markdown("<strong style='color: #ffffff;'>Extracted ATS Keywords from Resume:</strong>", unsafe_allow_html=True)
                
                # Display keywords horizontally in three columns
                col_tech, col_soft, col_tools = st.columns(3)
                with col_tech:
                    st.markdown("<div class='sub-section-header'>Technical Skills</div>", unsafe_allow_html=True)
                    if resume_keywords["Technical Skills"]:
                        for keyword in resume_keywords["Technical Skills"]:
                            st.markdown(f"<span class='resume-keyword-badge'>{keyword}</span>", unsafe_allow_html=True)
                    else:
                        st.info("No Technical Skills found.", icon="ℹ️")
                with col_soft:
                    st.markdown("<div class='sub-section-header'>Soft Skills</div>", unsafe_allow_html=True)
                    if resume_keywords["Soft Skills"]:
                        for keyword in resume_keywords["Soft Skills"]:
                            st.markdown(f"<span class='resume-keyword-badge'>{keyword}</span>", unsafe_allow_html=True)
                    else:
                        st.info("No Soft Skills found.", icon="ℹ️")
                with col_tools:
                    st.markdown("<div class='sub-section-header'>Tools Requirements</div>", unsafe_allow_html=True)
                    if resume_keywords["Tools"]:
                        for keyword in resume_keywords["Tools"]:
                            st.markdown(f"<span class='resume-keyword-badge'>{keyword}</span>", unsafe_allow_html=True)
                    else:
                        st.info("No Tools found.", icon="ℹ️")
        
        st.markdown("</div>", unsafe_allow_html=True)

# Analyze button with animation
st.markdown("<div style='text-align: center; margin: 30px 0;'>", unsafe_allow_html=True)
if st.button("Analyze Resume 🚀", key="analyze", use_container_width=True):
    if not resume_file or not job_description.strip():
        st.error("Please provide both a job description and a resume.", icon="⚠️")
    else:
        # Extract resume text
        with st.spinner("Extracting resume text..."):
            resume_text = extract_resume_text(resume_file)
            time.sleep(1)  # Simulate processing for UX
        
        if "Error" in resume_text:
            st.error(resume_text, icon="❌")
        else:
            # Calculate match percentage and missing keywords
            def calculate_match_percentage(resume_keywords, job_keywords):
                # Convert lists to sets for comparison
                resume_set = set(keyword.lower() for keyword in resume_keywords)
                job_set = set(keyword.lower() for keyword in job_keywords)
                
                # Find matching and missing keywords
                matching_keywords = resume_set.intersection(job_set)
                missing_keywords = job_set - resume_set
                
                # Calculate match percentage
                total_job_keywords = len(job_set)
                match_count = len(matching_keywords)
                match_percentage = (match_count / total_job_keywords * 100) if total_job_keywords > 0 else 0
                
                # Convert missing keywords back to original case
                missing_keywords = [keyword for keyword in job_keywords if keyword.lower() in missing_keywords]
                
                return round(match_percentage, 2), sorted(missing_keywords)
            
            # Extract keywords for comparison
            job_keywords = extract_keywords(job_description)
            resume_keywords = extract_keywords(resume_text)
            match_percentage, missing_keywords = calculate_match_percentage(resume_keywords["All Keywords"], job_keywords["All Keywords"])
            
            # Display results in cards
            st.markdown("<div class='section-header'>Analysis Results</div>", unsafe_allow_html=True)
            with st.container():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='progress-circle' style='--percentage: {match_percentage};' data-text='{match_percentage}%'></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"<div style='text-align: center; color: #ffffff; font-size: 1.2em;'>Resume Match Score</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Missing keywords (only from job description)
            with st.container():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("<strong style='color: #ffffff;'>Missing Keywords (from Job Description):</strong>", unsafe_allow_html=True)
                if missing_keywords:
                    for keyword in missing_keywords:
                        st.markdown(f"<span class='keyword-badge'>{keyword}</span>", unsafe_allow_html=True)
                else:
                    st.success("No missing keywords! 🎉", icon="✅")
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Hugging Face Resume Analysis (using chat_completion API for conversational models)
            with st.spinner("Analyzing you resume...."):
                client = InferenceClient(
                    api_key=os.environ["HF_TOKEN"],
                )
                hf_prompt = f"""
                You are an expert recruiter. Analyze the following resume and job description, compare common and different skill gaps.
                If the skill match between resume and job description is min 60% or higher, provide a positive summary about the candidate's suitability for the role, and give 1-2 specific suggestions for resume improvement. If the skill match is below 60%, focus on the gaps and provide constructive feedback on what is missing and how to improve the resume for this job.
                In your response, clearly specify:
                - Positives about the resume
                - Negatives about the resume
                - Overall result: State clearly if the resume is suitable for the job role (only if skill match is 60% or higher), otherwise state it is not suitable and why.
                Keep the summary concise (50-100 words).
                Also, provide exact ATS score for the uploaded resume against the provided job description.

                Resume: {resume_text[:1500]}...
                Job Description: {job_description[:1500]}...

                Output Format:
                Positives: [Positive points about the resume]
                Negatives: [Negative points or missing skills]
                Suggestions: [Specific improvements for the resume]
                Overall Result: [Suitable/Not Suitable for the Job Role and why]
                """
                try:
                    completion = client.chat_completion(
                        model="mistralai/Mistral-7B-Instruct-v0.2",
                        messages=[
                            {"role": "system", "content": "You are an expert recruite and Job Description Analyst. Suggest improvments and both positive and negative pointds of the Resume for the user."},
                            {"role": "user", "content": hf_prompt}
                        ],
                        temperature=0.7,
                    )
                    huggingface_analysis = completion.choices[0].message.content if hasattr(completion.choices[0], 'message') else str(completion)
                except Exception as e:
                    huggingface_analysis = f"Error: {str(e)}. Please try again or use a different model."
                st.markdown("<div class='section-header'>Resume Analysis and Suggestions</div>", unsafe_allow_html=True)
                with st.container():
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='color: #e5e7eb; line-height: 1.6;'>{huggingface_analysis}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Footer with a glowing effect
st.markdown(
    "<div class='footer'>Built with Streamlit & Google Gemini Pro | © 2025 SHIVAM KUMAR</div>",
    unsafe_allow_html=True,
)