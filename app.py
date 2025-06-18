import streamlit as st
from utils.ats_functions import extract_resume_text, calculate_match_percentage, analyze_with_gemini

# Set page configuration
st.set_page_config(page_title="Resume ATS Tracker", layout="wide")

# Title and description
st.title("Resume ATS Tracking System")
st.markdown("""
Upload a PDF resume and enter a job description to analyze candidate suitability.
The system calculates a keyword match percentage and uses Google Gemini Pro to provide
a detailed suitability analysis and resume improvement suggestions.
""")

# Create two columns for input
col1, col2 = st.columns(2)

with col1:
    # Job description input
    job_description = st.text_area("Enter Job Description", height=200, placeholder="e.g., Seeking a Python developer with experience in NLP and web development...")
    print(job_description)  # Debugging line to check job description input

with col2:
    # Resume file uploader
    resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"], help="Upload a text-based PDF resume.")

# Analyze button
if st.button("Analyze Resume", key="analyze"):
    if not resume_file or not job_description.strip():
        st.warning("Please provide both a job description and a resume.")
    else:
        # Extract resume text
        with st.spinner("Extracting resume text..."):
            resume_text = extract_resume_text(resume_file)
            print(resume_text)  # Debugging line to check extracted text
        
        if "Error" in resume_text:
            st.error(resume_text)
        else:
            # Calculate match percentage
            match_percentage, missing_keywords = calculate_match_percentage(resume_text, job_description)
            
            # Display results
            st.subheader("Analysis Results")
            st.metric("Match Percentage", f"{match_percentage}%")
            st.write("**Missing Keywords**:")
            st.write(", ".join(missing_keywords) if missing_keywords else "None")
            
            # Gemini analysis
            with st.spinner("Analyzing with Google Gemini Pro..."):
                gemini_analysis = analyze_with_gemini(resume_text, job_description)
                st.subheader("Candidate Suitability Analysis")
                st.markdown(gemini_analysis)

# Footer
st.markdown("---")
st.markdown("Built with Streamlit and Google Gemini Pro | © 2025 [SHIVAM KUMAR]")