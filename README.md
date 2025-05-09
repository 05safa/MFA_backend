# MFA Backend – Quick Start

This is an **ultra-short** setup guide.  
Follow the two steps below and you’re ready to run the FastAPI app.

---

## 1  Create & activate a virtual environment

```bash
python3 -m venv .venv          # Windows:  py -m venv .venv
source .venv/bin/activate      # Windows (PS):  .venv\Scripts\Activate.ps1

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8001
