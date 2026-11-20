# Blockchain-Enabled Hybrid Cyberbullying Detection and Evidence Preservation System

A Flask-based social-media-style web application that identifies potentially abusive content and records evidence of detected cyberbullying on a local Ethereum blockchain. The project combines a trained text-classification model, keyword checks, SQLite storage, SHA-256 hashing, and an Ethereum smart contract.

## Features

- User registration and login
- Create image posts and view the feed
- Like posts and add comments
- Classify post captions and comments with a saved machine-learning model and TF-IDF vectorizer
- Apply an additional list of abusive phrases when checking comments
- Count abusive comments for each user
- Show a warning when the abusive-comment count reaches three
- Mark an account as blocked when the count exceeds three
- Generate a SHA-256 hash for detected abusive comments
- Submit detected-comment evidence to an Ethereum smart contract through Web3.py and Ganache
- View blockchain evidence through the application
- Reels, profile, and chat pages

## Technology Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS
- **Database:** SQLite
- **Text classification:** Scikit-learn-compatible saved model and TF-IDF vectorizer
- **Blockchain integration:** Web3.py, Ethereum, Ganache
- **Smart contracts:** Solidity (contract deployment is performed separately, for example with Remix IDE)
- **Evidence hashing:** SHA-256 (`hashlib`)

## Project Files

```text
project-root/
├── app.py
├── blockchain.py
├── create_db.py
├── reset.py
├── bullying_model.pkl
├── model.pkl
├── vectorizer.pkl          # Required by app.py; not included in the uploaded ZIP
├── database.db
├── home.html
├── login.html
├── register.html
├── profile.html
├── reels.html
├── chat.html
├── warning.html
├── blocked.html
├── blockchain.html
├── styles.css
└── README.md
```

The uploaded archive contains the files listed above except `vectorizer.pkl`. Flask's `render_template()` normally looks for HTML files inside a `templates/` directory, and uploaded media is saved under `static/`; arrange the HTML files and create the `static/` directory accordingly if they are not already in those locations in your working copy.

## Requirements

- Python 3
- pip
- Ganache running locally
- A deployed Ethereum smart contract compatible with the ABI in `app.py`
- The matching `vectorizer.pkl` file used to train/prepare `bullying_model.pkl`

## Installation and Setup

1. **Clone or download this repository.**

   ```bash
   git clone <YOUR_REPOSITORY_URL>
   cd BlockChain-Enabled-Hybrid-CyberBullying-Detection-and-Evidence-Preservation-System-main
   ```

2. **Create and activate a virtual environment (recommended).**

   Windows PowerShell:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   macOS/Linux:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the Python packages.**

   ```bash
   pip install Flask web3 scikit-learn
   ```

   Install any additional packages required by the environment used to create the saved model files.

4. **Add the model vectorizer.**

   Place the correct `vectorizer.pkl` beside `app.py`. The application loads both `bullying_model.pkl` and `vectorizer.pkl` when it starts, so it will not start successfully without both compatible files.

5. **Prepare the Flask folders.**

   Place the HTML templates in a folder named `templates/` and ensure a `static/` folder exists for uploaded images and videos, if your working copy does not already have these folders.

6. **Start Ganache.**

   Run a local Ganache blockchain and confirm that its RPC endpoint matches the value configured in `app.py` (`http://127.0.0.1:7545`). The contract address and account configuration in `app.py` must also match your current Ganache deployment.

7. **Deploy and configure the smart contract.**

   Deploy the compatible evidence-storage Solidity contract using Remix or another Solidity development tool. Update the contract address and ABI in `app.py` to match the deployed contract. The contract must provide the `storeEvidence` and evidence-reading functions with signatures compatible with the ABI used by the application.

8. **Initialize the database if needed.**

   ```bash
   python create_db.py
   ```

   This script creates the SQLite tables. Run it only when you intend to create a fresh database; it may fail if the tables already exist.

9. **Run the Flask application.**

   ```bash
   python app.py
   ```

10. **Open the application.**

    Visit [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in your browser. The root route redirects to the login page.

## How Evidence Preservation Works

1. A user submits a comment on a post.
2. The application transforms the comment with the saved TF-IDF vectorizer and obtains a prediction from the saved classification model. It also checks the comment against a list of abusive phrases.
3. If the comment is detected as abusive, the user's abusive-comment count is increased.
4. The application computes a SHA-256 hash from the username and comment text.
5. It calls the smart contract's `storeEvidence` function through Web3.py and waits for the transaction receipt.
6. The application warns or blocks the user based on the abusive-comment count.

The blockchain stores the evidence fields passed by the application. The hash can help check whether the corresponding content has changed, but it does not by itself establish the real-world identity of an account holder or prove that a comment was authored by a particular person.

## Important Configuration Notes

- The Ganache RPC URL and deployed contract address are currently hard-coded in `app.py`; update them for your own environment.
- The application uses the first account exposed by the connected Web3 provider to submit transactions. Ensure the local account is available and funded in Ganache.
- Keep model and vectorizer files compatible: the vectorizer used at runtime must be the same preprocessing/vectorizer artifact expected by the trained model.
- This project is a development prototype. Before any real-world deployment, add appropriate password hashing, secret management, input validation, upload restrictions, access controls, and production server configuration.

## Project Objective

To support a safer online community by detecting potentially cyberbullying content, responding to repeated abusive behaviour, and preserving records of detected comments through blockchain-backed evidence storage.

## License

No license file was included in the supplied project archive. Add a `LICENSE` file if you intend to distribute this project with a specific open-source license.
