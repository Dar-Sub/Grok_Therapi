## Therapi Grok Chat
A Flask-based web application that provides therapy-related chat support in multiple languages using the xAI API. The app detects the user's language, translates the input to English for processing, and responds in the original language.

## Features
Multi-Language Support: Supports languages like English, German, French, Chinese, and more using `langdetect` for language detection and `deep-translator/googletrans` for translation.
Therapy-Focused Responses: Uses the xAI API to provide mental health and therapy-related responses.
User Authentication: Includes sign-up, login, and logout functionality with password hashing.
Chat History: Stores user chat sessions in a JSON file.
Rate Limiting: Implements request limits using `flask-limiter`.

## Prerequisites

Python 3.6+
A valid xAI API key (set in .env)

## Installation

Clone the Repository:
```
git clone https://github.com/yourusername/therapy-grok-chat.git
cd therapy-grok-chat
```


## Set Up a Virtual Environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


## Install Dependencies:
```
pip install -r requirements.txt
```


## Set Up Environment Variables:Create a .env file in the root directory and add:
```
FLASK_SECRET_KEY=your-secret-key
XAI_API_KEY=your-xai-api-key
PORT=5001
```



## Usage

Run the App Locally:
```
python app.py
```


Open `http://127.0.0.1:5001` in your browser.


## Sign Up/Login:

Sign up with a username and password, then log in.


## Start Chatting:

Create a chat session and send therapy-related messages in any supported language.


## File Structure

`app.py`: Main Flask application.
`chat.html`: Chat interface template.
`login.html`: Login page template.
`users.json`: Stores user credentials.
`history.json`: Stores chat history.
`requirements.txt`: Python dependencies.

## Dependencies

Flask
flask-limiter
werkzeug
requests
python-dotenv
deep-translator
langdetect
googletrans


## License
MIT License
