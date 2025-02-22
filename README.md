# Lexical Processing Tool with Gemini API Integration

This project is a Python-based tool designed to process lexical files, interact with the Gemini API for natural language processing, and generate structured outputs in JSON and Excel formats. It features a user-friendly graphical interface built with PyQt5, making it easy to upload files, configure processing parameters, and visualize results.

## Features

- **Lexical File Processing**: Splits and processes large lexical files into manageable segments.
- **Gemini API Integration**: Sends processed text segments to the Gemini API for advanced natural language processing.
- **JSON Validation and Fixing**: Automatically validates and fixes JSON responses from the API.
- **DataFrame Generation**: Converts JSON responses into structured Pandas DataFrames.
- **Excel Export**: Saves processed data into Excel files for further analysis.
- **User-Friendly GUI**: Built with PyQt5, offering an intuitive interface for file uploads, model selection, and processing.

## Prerequisites

Before running the tool, ensure you have the following installed:

- Python 3.7 or higher
- Required Python packages (install via `pip`):
  ```bash
  pip install -r requirements.txt
  ```
- A valid API key for the Gemini API.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/lexical-processing-tool.git
   cd lexical-processing-tool
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Replace the placeholder API key in the script with your actual Gemini API key:
   ```python
   self.api_key = ""  # Replace with your API key
   ```

## Usage

1. Run the script:
   ```bash
   python tool_v7_build_package.py
   ```

2. Use the GUI to:
   - Upload a lexical file (`.txt` format).
   - Select a Gemini model from the dropdown menu.
   - Specify the start and end pages for processing.
   - Enter a custom prompt for the API.
   - Start processing and view the results in the output text area.

3. Save the processed data as an Excel file.

## Creating a Desktop App with PyInstaller

To package the tool as a standalone desktop application:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Navigate to the project directory and run:
   ```bash
   pyinstaller --onefile --windowed tool_v7_build_package.py
   ```
   - `--onefile`: Packages the app into a single executable file.
   - `--windowed`: Prevents a terminal window from appearing when running the app.

3. The executable will be located in the `dist` folder. You can distribute this file to users who don’t have Python installed.

## Example

Here’s an example of how to use the tool:

1. Upload a lexical file (e.g., `lexical_file.txt`).
2. Select a model (e.g., `gemini-1.5-pro`).
3. Set the start page to `1` and the end page to `10`.
4. Enter a prompt like:
   ```
   Acheck uploaded prompt file <promot.txt>
   ```
5. Click "إنشاء الإخراج" (Generate Output) to start processing.
6. Save the results as an Excel file.

## Requirements File

The `requirements.txt` file lists all the dependencies needed to run the project. Here’s what it should contain:

```plaintext
PyQt5==5.15.9
pandas==2.0.3
requests==2.31.0
typing-extensions==4.7.1
openpyxl==3.1.2
```

To generate the `requirements.txt` file, run:
```bash
pip freeze > requirements.txt
```

## Troubleshooting

- **Qt Platform Plugin Error**: Ensure all Qt dependencies are installed. On Linux, run:
  ```bash
  sudo apt-get install libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0
  ```
- **API Key Issues**: Verify that your Gemini API key is valid and has sufficient permissions.
- **JSON Parsing Errors**: Check the API response format and ensure the prompt generates valid JSON.

## Contributing

Contributions are welcome! If you’d like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with a detailed description of your changes.
---

This updated `README.md` includes instructions for creating a desktop app with PyInstaller and a `requirements.txt` file for dependency management. Let me know if you need further assistance! 🚀
