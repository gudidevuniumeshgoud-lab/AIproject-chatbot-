import os
from dotenv import load_dotenv
from PIL import Image
import pytesseract
import docx
import PyPDF2
from automation import handle_automation
from brain import get_gemini_response

load_dotenv()

# Tesseract Configuration
TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
else:
    print(f"WARNING: Tesseract not found at {TESSERACT_PATH}. OCR will be disabled.")

# GLOBAL MEMORY FOR CONTENT
last_uploaded_content = ""

SYSTEM_PROMPTS = {
    "Normal Assistant": "You are NEXUS, a helpful and intelligent AI student assistant. Provide concise, accurate, and student-friendly answers.",
    "Viva Mode": "You are a strict college viva interviewer. Your goal is to test the student's knowledge. Ask one technical question at a time. After the student answers, give a brief evaluation (e.g., 'Correct', 'Partially correct', 'Incorrect') and then ask the next question. Do not provide long explanations unless asked.",
    "Quiz Mode": "You are a Quiz Generator. When the user asks for a quiz, generate 5 Multiple Choice Questions (MCQs) with 4 options (A, B, C, D) each. Provide the correct answers at the bottom. Make the questions challenging but fair.",
    "Study Notes Mode": "You are a Study Notes Specialist. Your goal is to help students revise effectively. Provide structured notes, key concepts, and summaries in an easy-to-read format with bullet points."
}

def reset_orchestrator():
    global last_uploaded_content
    last_uploaded_content = ""

def detect_intent(query):
    query = query.lower().strip()
    if "analyze file" in query:
        return "file"
    if any(word in query for word in ["open", "search", "launch", "start", "search for"]):
        return "automation"
    return "chat"

def handle_file_task(query):
    global last_uploaded_content
    parts = query.split("analyze file")
    if len(parts) > 1:
        file_path = parts[1].strip()
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"

        extension = file_path.split(".")[-1].lower()
        extracted_text = ""

        try:
            if extension in ["jpg", "jpeg", "png"]:
                if not os.path.exists(TESSERACT_PATH):
                    return "Error: Tesseract OCR not found. Cannot analyze images."
                image = Image.open(file_path)
                extracted_text = pytesseract.image_to_string(image)
            elif extension == "txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    extracted_text = f.read()
            elif extension == "pdf":
                with open(file_path, "rb") as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        extracted_text += page.extract_text() + "\n"
            elif extension == "docx":
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    extracted_text += para.text + "\n"
            else:
                return f"Error: File type '{extension}' not supported."
        except Exception as e:
            return f"Error processing file: {str(e)}"

        if extracted_text.strip():
            last_uploaded_content = extracted_text
            from brain import add_to_history
            doc_context = f"Context from uploaded file '{os.path.basename(file_path)}':\n\n{extracted_text[:15000]}"
            add_to_history("user", f"I have uploaded a document: {os.path.basename(file_path)}")
            add_to_history("model", f"I have analyzed '{os.path.basename(file_path)}'. I'm ready to help you with it. You can now use the action buttons below (Summarize, Generate Notes, etc.) or ask me questions directly.")
            return f"Successfully analyzed '{os.path.basename(file_path)}'. What would you like to do with it?"
        else:
            return "File uploaded, but no readable content was found."
    return "Invalid file analysis request."

def process_full_query(query, ai_mode="Normal Assistant"):
    global last_uploaded_content
    
    intent = detect_intent(query)
    
    # ---------------- SPECIAL STUDENT COMMANDS ---------------- #
    lower_query = query.lower()
    if "generate quiz" in lower_query or "create mcqs" in lower_query:
        ai_mode = "Quiz Mode"
    
    if last_uploaded_content:
        if lower_query == "summarize content":
            query = f"Summarize this document content: {last_uploaded_content[:10000]}"
        elif lower_query == "generate study notes":
            query = f"Generate detailed study notes from this document: {last_uploaded_content[:10000]}"
        elif lower_query == "generate important questions":
            query = f"Identify the most important exam questions from this document: {last_uploaded_content[:10000]}"
        elif lower_query == "generate viva questions":
            query = f"Generate potential viva/oral exam questions based on this document: {last_uploaded_content[:10000]}"

    # ---------------- FILE ---------------- #
    if intent == "file":
        return handle_file_task(query)

    # ---------------- AUTOMATION ---------------- #
    if intent == "automation":
        auto_res = handle_automation(query)
        if auto_res:
            return auto_res

    # ---------------- AI RESPONSE ---------------- #
    system_instruction = SYSTEM_PROMPTS.get(ai_mode, SYSTEM_PROMPTS["Normal Assistant"])
    
    try:
        response = get_gemini_response(query, system_instruction=system_instruction)
        return response.strip() if response else "No response from AI."
    except Exception as e:
        error_str = str(e)
        print(f"Gemini Error: {error_str}")
        
        manual_result = handle_automation(query)
        if manual_result:
            return f"(Local Mode) {manual_result}"
        
        return f"AI Error: {error_str}"

