### Setup guide for the respository

## Prerequisites

- python
- pip

## Setup guide for the project

Step 1 - Clone the repository

```bash
git clone -b test-dashboard-backend https://github.com/ixd-ai-hub/financial-document-based-agent-system.git
cd \path\to\root\folder
```

Step 2 - Create a python virtual environment

```bash
python -m venv .venv # Windows
python3 -m venv .venv # Linux
```

Step 3 - Activate the virtual environment

```bash
.\.venv\Scripts\activate # Windows
source .venv/bin/activate # Linux
```

Step 4 - Install uv

```bash
pip install uv
```

Step 5 - Install necessary packages

```bash
uv sync
```

Step 6 - Create the sqlite db

```bash
python3 create_db.py # linux
python create_db.py # windows

Step 6 - Start the development server with uvicorn

```bash
uvicorn main:app --reload
```
