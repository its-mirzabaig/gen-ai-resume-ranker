📄 Resume Evaluator using FastAPI & Generative AI
This is a FastAPI-based web service that helps HR teams and hiring managers evaluate resumes at scale. It leverages (Google’s Gemini) LLM to extract key criteria from a job description and then scores resumes against those criteria. It also supports anonymizing personally identifiable information (PII) and exporting results to a CSV file.

🚀 Features
Upload a job description and multiple resumes

Extract top hiring criteria from the JD using LLM

Score resumes based on the criteria

Anonymize sensitive data using Presidio

Export results as a downloadable CSV

Supports PDF and DOCX resume formats

Project Overview
1. Gen AI Powered Resume Ranker is an innovative solution that leverages Generative AI (LLM) to evaluate and rank resumes against job description criteria. The system offers a streamlined process for analyzing resumes, extracting key criteria from job descriptions, anonymizing personal information, and generating scores that reflect how well a resume matches the job's requirements.

2. The project is designed to run locally but has been structured with modularity and future scalability in mind. In the current setup, files are stored temporarily on the local machine, but future versions could support cloud hosting for enhanced scalability. The architecture also includes future integration for authentication, ensuring secure access and protecting sensitive data.

Key Features:
- Generative AI Integration: The system utilizes a Generative AI model to extract critical job selection criteria from job descriptions (e.g., education, skills, experience, certifications) and rank resumes based on how closely they align with these criteria.

- Anonymization for Fairness: Resumes are anonymized using a privacy-preserving tool, ensuring that any personal identifiable information (PII) such as names, email addresses, and phone numbers are removed before the scoring process. This ensures that the LLM ranking is free from any bias related to personal data.

- Independent Resume Evaluation: Each resume is processed independently along with its corresponding criteria. This isolation ensures there is no bias in how the resumes are ranked. The scoring process takes place solely based on the relevance of the content to the job description.

- Modular API Design: The API calls to the Generative AI model are isolated in separate functions, making it easy to swap out the current LLM provider with another or extend the system to support batch processing. This modularity ensures that future updates or changes to the AI service provider can be integrated without disrupting the entire workflow.

- CSV Generation: After processing and scoring the resumes, the system generates a CSV report that lists the candidate names, criteria-based scores, and total scores. This report can be used by HR or hiring teams for further evaluation and decision-making.

- Future Enhancements: There are plans to add Authentication (Auth) to the system for user security, ensuring only authorized personnel can interact with the API. Additionally, cloud hosting will be integrated in the future to handle large-scale data processing and provide more flexibility in managing multiple users and large file sizes.

Current Design Considerations:
- Local Run Environment: The current design is optimized to run locally on the user’s machine. Temporary files are stored in a local directory (e.g., for CSV generation) to minimize reliance on external systems. This makes the system lightweight and suitable for small-scale use.

- Authentication and Security: While the current version does not have authentication implemented, there are plans to incorporate user authentication in future updates. This would ensure that only authorized users can interact with sensitive data such as resumes and job descriptions.

- Cloud Hosting in the Future: In the long term, the system will be adapted for cloud hosting. This will allow the platform to handle a larger number of requests, users, and data. Cloud hosting will also enable advanced features like distributed processing and more secure, centralized storage for files and reports.

The modular approach to the design makes it adaptable, and the isolated processing of resumes ensures fairness and objectivity in ranking. With planned future upgrades for authentication and cloud hosting, the system is set for further growth and can be expanded to support enterprise-level use cases.

📦 Dependency Management
This project uses a pinned requirements.txt to ensure consistent environments.

🧪Setup Instructions
1. Clone the Repository
First, clone this repository to your local machine:
```
git clone https://github.com/its-mirzabaig/gen-ai-resume-ranker.git
cd gen-ai-resume-ranker
```
2. Set up a Virtual Environment
Create a virtual environment using the following command:
```
python3 -m venv venv
```
This will create a virtual environment folder named venv.

3. Activate the Virtual Environment
For Windows:
```
.venv\Scripts\activate
```
For macOS/Linux:
```
source venv/bin/activate
```
Once activated, your terminal prompt should change to show the virtual environment name (venv).

4. Install Dependencies
Make sure you're in the root directory of the project (where requirements.txt is located). Install the necessary dependencies using:
```
pip install -r requirements.txt
```
5. Set up Environment Variables
Create a .env file in the root directory with the following environment variable:
```
AI_API_KEY=your_api_key_here
```
Replace your_api_key_here with your actual API key for the AI integration.

6. Run the Application
Now, you can run the FastAPI app using Uvicorn:
```
uvicorn main:app --reload
```
This will start the server at http://127.0.0.1:8000.

7. Testing the Endpoints
You can test the endpoints with a tool like Postman or through the OpenAPI docs (Swagger UI) at:
```
http://127.0.0.1:8000/docs
```


🧠 Endpoints
POST /extract-criteria
Upload a job description file and extract top 5 criteria.

Request:

File (PDF or DOCX)

Response:
```
{
"criteria": ["Python", "5+ years experience", "AWS", "LLM knowledge", "Bachelor’s degree"]
}
```

POST /score-resumes
Score multiple resumes against given criteria.

Request:

criteria (List of strings in the request body)

Multiple resume files (PDF or DOCX)

Response:
```
{
"file_path": "/tmp/tmpabcd/resume_scores.csv"
}
```

POST /extract-and-score
Combined workflow: extract criteria from JD and score resumes.

Request:

job_description (UploadFile)

files (List of UploadFile resumes)

Response:
```
{
"file_path": "/tmp/tmpabcd/resume_scores.csv"
}
```

🛡️ Anonymization
The app uses Presidio to anonymize PII like:

Person names

Phone numbers

Email addresses

IP addresses

This ensures privacy-compliant processing of candidate data.

📤 Export
The final resume scores are exported to a CSV with the following structure:
Serial Number	Candidate Name	Skill 1	Skill 2	...	Total Score	Rank

- Serial Number: Represents the original sequence of resumes as they were uploaded.
- Candidate Name: The name of the candidate (extracted from the file name).
- Skills: Columns for each skill criterion with scoes.
- Total Score: The sum of scores for each candidate.
- Rank: The rank of the candidate based on their total score (Rank 1 is the highest score).
The CSV is sorted by Rank, with Rank 1 at the top, followed by lower ranks in descending order of score.

🧑‍💻 Tech Stack
FastAPI – API framework

(Gemini) LLM API – for NLP reasoning

SpaCy – for language model integration with Presidio

Presidio – for PII detection and anonymization

Pandas – for tabular data export

PyMuPDF / python-docx – for reading resume files

📂 Project Structure
``` 
main.py             # The entry point of your FastAPI application
requirements.txt    # Contains pinned Python dependencies
.env                # Holds environment variables like API keys (not committed to Git)
README.md           # Documentation for the project
 ```
📃 License
MIT License © 2025 its-mirzabaig