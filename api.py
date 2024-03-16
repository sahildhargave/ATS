from flask import Flask, request, jsonify
import pickle
import base64
import io
from PIL import Image
import pdf2image
import google.generativeai as genai

app = Flask(__name__)

# Load input prompts from pickle file
with open('input_prompts.pkl', 'rb') as f:
    input_prompts = pickle.load(f)

# Configure Google Generative AI
genai.configure(api_key="YOUR_GOOGLE_API_KEY")  # Update with your API key

def get_gemini_response(input_text, pdf_content, prompt):
    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([input_text, pdf_content[0], prompt])
    return response.text

def process_resume(uploaded_file):
    if uploaded_file is not None:
        # Convert the PDF to image
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]

        # Convert to bytes
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()  # encode to base64
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")

@app.route('/analyze_resume', methods=['POST'])
def analyze_resume():
    # Get job description and resume data from request
    input_text = request.form.get('input')
    pdf_content = request.form.get('pdf_content')
    prompt = request.form.get('prompt')

    # Retrieve the appropriate input prompt based on the job description
    input_prompt = input_prompts.get(prompt, '')

    if not input_prompt:
        return jsonify({'error': 'Job description not found'}), 400

    # Process the resume
    pdf_content = process_resume(pdf_content)

    # Get Gemini response
    response = get_gemini_response(input_text, pdf_content, input_prompt)

    return jsonify({'response': response})

if __name__ == "__main__":
    app.run(debug=True)
