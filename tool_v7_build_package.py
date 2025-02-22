import re
import pandas as pd
import requests
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QLabel, QTextEdit, QPushButton, QFileDialog, QWidget, QMessageBox, QScrollArea, QComboBox, QSpinBox, QHBoxLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sys
import typing_extensions as typing
import logging

# Configure logging (consider more specific config if needed)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to process the lexical file
def lexical_output(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        print(f"Size of file: {len(content) / 1024}KB")
    text_segments = re.split(r"\(\d+/\d+\)", content)
    text_segments = [segment.strip() for segment in text_segments if segment.strip()]
    return text_segments

# Function to get response from Gemini API
def gemini_output(prompt, model_name, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    })
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code != 200:
        error_message = response.json().get("error", {}).get("message", "Unknown error")
        raise ValueError(f"API returned an error: {response.status_code} - {error_message}")

    
    print(f"Response Size {len(response.text)/1024}KB")
    json_response = response.json()
    if 'candidates' not in json_response or not json_response['candidates']:
        raise ValueError("The API response does not contain 'candidates'. Check your API key and prompt format.")

    return json_response['candidates'][0]['content']['parts'][0]['text']



def response_handling(non_valid_json, model_name, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    prompt = f"""validate that next input_data is a valid json format if not, correct it to be a valid json format
                input_data:{non_valid_json}"""
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    })
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code != 200:
        raise ValueError(f"API returned an error: {response.text}")
    
    print(f"Response Size {len(response.text)/1024}KB")
    json_response = response.json()
    if 'candidates' not in json_response or not json_response['candidates']:
        raise ValueError("The API response does not contain 'candidates'. Check your API key and prompt format.")

    return json_response['candidates'][0]['content']['parts'][0]['text']


# New function to handle truncated JSON
def fix_truncated_json(json_string):
    """
    Fixes a truncated JSON string by ensuring proper closing of brackets and braces.
    """
    stack = []
    fixed_json = []

    for char in json_string:
        fixed_json.append(char)
        if char == '{' or char == '[':
            stack.append(char)
        elif char == '}' or char == ']':
            if stack:
                last_open = stack.pop()
                if (last_open == '{' and char != '}') or (last_open == '[' and char != ']'):
                    raise ValueError(f"Mismatched closing: expected {last_open} but got {char}")

    # Close any unclosed brackets/braces
    while stack:
        last_open = stack.pop()
        if last_open == '{':
            fixed_json.append('}')
        elif last_open == '[':
            fixed_json.append(']')

    return ''.join(fixed_json)

# Existing functions
def fix_json_keys(json_str):
    """Fixes unquoted keys in a JSON string by adding quotes around them."""
    pattern = r'(?<!")\s*([\w\u0600-\u06FF]+)\s*:(?!")'  # Matches unquoted keys (including Arabic)
    fixed_json = re.sub(pattern, r'"\1":', json_str)
    return fixed_json

def _sanitize_json(json_str):
    """Cleans common JSON issues (unescaped quotes, trailing commas)."""
    json_str = json_str.replace("“", '"').replace("”", '"')  # Replace smart quotes
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)  # Remove trailing commas
    return json_str

def validate_and_fix_json(json_str):
    """Validates and fixes JSON string."""
    try:
        cleaned_json = _sanitize_json(json_str)
        return json.loads(cleaned_json)
    except json.JSONDecodeError:
        logging.debug("Direct JSON parsing failed, attempting to extract")
    
    json_match = re.search(r'\[.*\]|\{.*\}', json_str, re.DOTALL)
    if json_match:
        try:
            json_data = json_match.group(0)
            cleaned_json = _sanitize_json(json_data)
            return json.loads(cleaned_json)
        except json.JSONDecodeError:
            logging.debug("JSON regex extraction failed")
    else:
        logging.debug("No JSON data found in input")    
    return None

# Updated store_df function
def store_df(response, model_name, api_key):
    logging.info("Starting store_df processing...")
    try:
        # Extract JSON portion and fix keys
        logging.info("Extracting and fixing JSON keys...")
        json_match = re.search(r'\[.*\]|\{.*\}', response, re.DOTALL)
        if not json_match:
            logging.warning("No JSON data found in the initial response.")
            return None
        
        json_data = json_match.group(0)
        
        # Fix truncated JSON
        logging.info("Fixing truncated JSON...")
        fixed_json_data = fix_truncated_json(json_data)
        
        # Fix keys in JSON
        fixed_json_data = fix_json_keys(fixed_json_data)
        
        # Validate and Fix
        logging.info("Validating and fixing JSON...")
        parsed_data = validate_and_fix_json(fixed_json_data)
        if parsed_data is not None:
            # Convert to DataFrame
            logging.info("Converting data to DataFrame...")
            df = pd.DataFrame(parsed_data) if isinstance(parsed_data, list) else pd.DataFrame([parsed_data])
            logging.info(f"DataFrame created. Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            return df
        else:
            logging.warning("First attempt parsing failed")

        # Fallback: Call response_handling
        logging.warning("First attempt parsing failed, falling back via Gemini model...")
        # print(fixed_json_data)
        try_valid_json = response_handling(response, model_name, api_key)
        # print(try_valid_json)
        # Validate fallback data
        logging.info("Validating fallback JSON...")
        json_match = re.search(r'\[.*\]|\{.*\}', try_valid_json, re.DOTALL)
        if not json_match:
            logging.warning("No JSON data found in fallback response.")
            return None
        
        json_data = json_match.group(0)
        fixed_json_data = fix_truncated_json(json_data)
        fixed_json_data = fix_json_keys(fixed_json_data)
        parsed_data = validate_and_fix_json(fixed_json_data)
        
        if parsed_data is not None:
            # Convert fallback to DataFrame
            logging.info("Converting fallback data to DataFrame...")
            df = pd.DataFrame(parsed_data) if isinstance(parsed_data, list) else pd.DataFrame([parsed_data])
            logging.info(f"DataFrame created using fallback. Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            return df
        else:
            logging.error("Failed to parse fallback response")
            return None

    except ValueError as e:
        logging.error(f"Error during processing or fallback: {e}")
        return None
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        return None


class ProcessWorker(QThread):
    update_output_signal = pyqtSignal(str)
    update_status_signal = pyqtSignal(str)
    save_data_signal = pyqtSignal(pd.DataFrame)
    finished_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.file_path = None
        self.user_prompt = None
        self.model_name = None
        self.start_page = None
        self.end_page = None
        self.api_key = None
        self.all_pages_data = []
        self.is_running = True
    
    def run(self):
        try:
            print("Starting ProcessWorker...")
            lexical_pages = lexical_output(self.file_path)
            self.all_pages_data = []

            self.update_output_signal.emit("")  # Clear output text area
            
            for row, page in enumerate(lexical_pages, start=1):
                if not self.is_running:
                    break  # Stop if requested
                if self.start_page <= row < self.end_page:
                    print(f"Processing page {row}")
                    prompt = self.user_prompt.replace("{lexical_page}", page)
                    try:
                        text_response = gemini_output(prompt, self.model_name, self.api_key)

                        self.update_output_signal.emit(f"\n\n======== صفحة {row} ========")
                        self.update_output_signal.emit(f"طلب النموذج: {prompt}")
                        self.update_output_signal.emit(f"إجابات النموذج:\n{text_response}")
                        
                        # Pass `api_key` explicitly to `store_df`
                        page_df = store_df(text_response,model_name = self.model_name, api_key=self.api_key)
                        if page_df is not None:
                            self.all_pages_data.append(page_df)
                    except ValueError as e:
                        self.update_status_signal.emit(f"خطأ في الصفحة {row}: {e}")
                        continue  # Skip current page

            if self.all_pages_data:
                df = pd.concat(self.all_pages_data, ignore_index=True)
                self.save_data_signal.emit(df)
                print("DataFrames created and sent successfully")
            else:
                self.update_status_signal.emit("لم يتم العثور على بيانات JSON صالحة لمعالجتها.")
            print("ProcessWorker finished successfully")
        except Exception as e:
            self.update_status_signal.emit(f"حدث خطأ: {e}")
        finally:
            self.finished_signal.emit()  # Emit finished signal before worker quits.

    def stop(self):
        self.is_running = False



# PyQt5 GUI setup
class LexicalTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("أداة معالجة الملفات المعجمية")
        self.setGeometry(100, 100, 800, 600)

        self.file_path = None
        self.model_names = ['gemini-2.0-flash-exp', 'gemini-1.5-flash-latest', 'gemini-1.5-pro', 'gemini-exp-1206']
        self.api_key = "AIzaSyDseZ2_rS5cS0xJILfdzo46q42MkHtDsXU"  # Add your API key here
        self.worker = None  # Initialize worker to None

        # Layout
        self.layout = QVBoxLayout()

        # File Upload Button
        self.upload_button = QPushButton("تحميل ملف المعجم")
        self.upload_button.clicked.connect(self.upload_file)
        self.layout.addWidget(self.upload_button)

        # Model Selection Dropdown
        model_layout = QHBoxLayout()
        self.model_label = QLabel("اختر النموذج:")
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems(self.model_names)
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.model_dropdown)
        self.layout.addLayout(model_layout)

        # Start and End Page Selection
        page_layout = QHBoxLayout()
        self.start_page_label = QLabel("صفحة البداية:")
        self.start_page_spinbox = QSpinBox()
        self.start_page_spinbox.setMinimum(1)
        self.start_page_spinbox.setMaximum(3000)  # Set a higher maximum limit
        self.end_page_label = QLabel("صفحة النهاية:")
        self.end_page_spinbox = QSpinBox()
        self.end_page_spinbox.setMinimum(1)
        self.end_page_spinbox.setMaximum(3000)    # Set a higher maximum limit
        page_layout.addWidget(self.start_page_label)
        page_layout.addWidget(self.start_page_spinbox)
        page_layout.addWidget(self.end_page_label)
        page_layout.addWidget(self.end_page_spinbox)
        self.layout.addLayout(page_layout)

        # Prompt Label and TextEdit
        self.prompt_label = QLabel("أدخل النص المخصص للمعالجة:")
        self.layout.addWidget(self.prompt_label)

        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("اكتب النص هنا...")
        self.layout.addWidget(self.prompt_text)

        # Process Button
        self.process_button = QPushButton("إنشاء الإخراج")
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.process_prompt)
        self.layout.addWidget(self.process_button)

       # Stop Button
        self.stop_button = QPushButton("إيقاف المعالجة")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_processing)
        self.layout.addWidget(self.stop_button)

        # Status Label
        self.status_label = QLabel("الحالة: في انتظار تحميل الملف")
        self.layout.addWidget(self.status_label)

        # Output text box with scroll area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.output_text)
        self.layout.addWidget(scroll_area)

        self.setLayout(self.layout)

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "اختر ملف", "", "Text Files (*.txt)")
        if file_path:
            self.file_path = file_path
            self.status_label.setText(f"تم اختيار الملف: {self.file_path}")
            self.process_button.setEnabled(True)

    def process_prompt(self):
        if not self.file_path:
            QMessageBox.critical(self, "خطأ", "لم يتم اختيار ملف.")
            return

        user_prompt = self.prompt_text.toPlainText().strip()
        if not user_prompt:
            QMessageBox.critical(self, "خطأ", "لم يتم إدخال النص المخصص.")
            return

        model_name = self.model_dropdown.currentText()
        start_page = self.start_page_spinbox.value()
        end_page = self.end_page_spinbox.value()

        if start_page >= end_page:
            QMessageBox.critical(self, "خطأ", "يجب أن تكون صفحة البداية أقل من صفحة النهاية.")
            return

        self.status_label.setText("الحالة: المعالجة قيد التنفيذ...")
        # Clear output area before starting the new process
        self.output_text.clear()

        self.worker = ProcessWorker()
        self.worker.file_path = self.file_path
        self.worker.user_prompt = user_prompt
        self.worker.model_name = model_name
        self.worker.start_page = start_page
        self.worker.end_page = end_page
        self.worker.api_key = self.api_key

        self.worker.update_output_signal.connect(self.update_output)
        self.worker.update_status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.on_worker_finished) # Connect the new signal
        self.worker.save_data_signal.connect(self.save_data)
        self.worker.start()
        self.stop_button.setEnabled(True) # Enable the stop button
        self.process_button.setEnabled(False) # Disable the process button

    def update_output(self, text):
        self.output_text.append(text)
        self.output_text.repaint()

    def update_status(self, status_text):
        self.status_label.setText(f"الحالة: {status_text}")

    def on_worker_finished(self):
        self.status_label.setText("الحالة: انتهت المعالجة")
        self.stop_button.setEnabled(False)
        self.process_button.setEnabled(True)
        self.worker = None # Set the worker to None after it is finished

    def stop_processing(self):
        if self.worker:
            self.worker.stop()
            self.status_label.setText("الحالة: إيقاف المعالجة...")
    
    def save_data(self, df):
        output_file, _ = QFileDialog.getSaveFileName(self, "حفظ الملف", "", "Excel Files (*.xlsx)")
        if output_file:
            if not output_file.endswith(".xlsx"):
                output_file += ".xlsx"
            df.to_excel(output_file, index=False, engine='openpyxl')
            self.update_status("تم حفظ البيانات")
        else:
             self.update_status("لم يتم حفظ البيانات")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LexicalTool()
    window.show()
    sys.exit(app.exec_())