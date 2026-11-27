# Privacy-Preserving Student Skill Matching

A student skill-matching Proof of Concept (PoC) combining **Bloom Filters, Fully Homomorphic Encryption (FHE), and ECDH-based Private Set Intersection (PSI)**.

The system allows two students to identify common skills without revealing their complete profiles to each other. Shared skills are revealed only when the matching threshold is satisfied.

> **Privacy assumption:** The backend is trusted and receives both students' plaintext skill lists. Privacy is enforced between participants, not against the server.

## 1. Project Overview

Two students join a matching session and submit their skills.

For example:

- **Student A:** Python, AI, Cybersecurity
- **Student B:** Python, AI, Web
- **Threshold:** 2

**Result:**
```text
Threshold satisfied: Yes
Common skills: Python, AI
```

If fewer than two skills overlap:

```text
Threshold satisfied: No
No common skills were revealed.
```

## 2. Privacy Goal & Adversary Model

**Privacy Goal**
- Reveal common skills only when the threshold is satisfied.
- Hide non-matching skills from the other participant.
- Reveal no intersection below the threshold.

**Adversary Model**
- **Adversary:** A semi-honest participating student.
- **Capabilities:** Submit skills, join sessions, and observe matching results.
- **Objective:** Infer another student's undisclosed skills.
- **Trust assumption:** The backend is trusted and processes plaintext inputs.

The PoC does not protect against malicious participants or repeated-query inference attacks.

## 3. System Architecture

```text
Student A                  Student B
    |                          |
    +---- Create/Join Session -+
                 |
          Submit Skills
                 |
          Trusted Backend
                 |
          Bloom Filter
                 |
       FHE Threshold Check
                 |
        Token Generation
                 |
            ECDH PSI
                 |
          Matching Result
                 |
          Student A & B
```

### Privacy-Enhancing Techniques

| Technique | Purpose |
|---|---|
| Bloom Filter | Encodes skills for membership testing |
| FHE (Concrete-Python) | Performs encrypted membership and threshold computations |
| ECDH-based PSI | Computes shared skills using threshold-dependent tokens |

The current PoC uses a fixed threshold of **2 shared skills**.

## 4. Project Structure

```text
Privacy-Preserving-Student-Skill-Matching/
├── backend/
│   ├── bloom_and_psi.py
│   ├── fhe_threshold.py
│   ├── interfaces.py
│   ├── main.py
│   └── tests/
│       ├── test_psi.py
│       └── test_fhe_threshold.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── App.css
│   └── package.json
├── requirements.txt
├── .gitignore
└── README.md
```

## 5. Technologies

- **Backend:** Python 3.12, FastAPI, Uvicorn
- **Cryptography:** Concrete-Python, cryptography
- **Data structures:** bitarray, NumPy
- **Frontend:** React, Vite, JavaScript, CSS
- **Testing:** Pytest
- **Environment:** Ubuntu/Linux or WSL2

## 6. Installation & Setup

### Prerequisites

- Ubuntu/Linux or WSL2
- Python 3.12
- Node.js and npm
- Git

**Important:** Keep the project and virtual environment inside the Ubuntu filesystem rather than Windows/OneDrive to avoid Concrete-Python compilation issues.

### Clone the Repository

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/DenaAlharbi/Privacy-Preserving-Student-Skill-Matching.git skill-matching
cd skill-matching
```

### Set Up the Backend

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Run Backend Tests

```bash
python -m pytest backend/tests -v
```

Expected result for the tested version:

```text
5 passed
```

### Start the Backend

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Backend URL: http://127.0.0.1:8000

### Start the Frontend

Open a second terminal:

```bash
cd ~/projects/skill-matching/frontend
npm install
npm run dev
```

Frontend URL: http://localhost:5173

## 7. Demo Workflow

1. Student A creates a matching session.
2. Student B joins using the session code.
3. Both students select and submit their skills.
4. The backend performs Bloom Filter encoding, FHE threshold evaluation, and ECDH-based PSI.
5. Both students can check the matching result.

### Test Cases

| Scenario | Shared Skills | Expected Result |
|---|---|---|
| Threshold satisfied | Python, AI | Reveal Python and AI |
| Threshold not satisfied | Python | No common skills revealed |

Both scenarios were successfully demonstrated in the tested PoC.

## 8. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/sessions` | Create a session |
| `POST` | `/sessions/{id}/student-a` | Submit Student A's skills |
| `POST` | `/sessions/{id}/student-b` | Submit Student B's skills |
| `GET` | `/sessions/{id}/result` | Retrieve matching result |
| `POST` | `/match` | Single-request matching |

## 9. Limitations

**Limitations:**
- The trusted backend receives plaintext skill lists.
- Sessions are stored temporarily in memory.
- Bloom Filters may produce false positives.
- The threshold and FHE input shape are fixed.
- The 4-bit token space is not suitable for production security.
- Repeated queries may allow participants to infer private information.
- The implementation is an educational PoC, not a production-secure PSI protocol.

## 10. Research Inspiration

This project is inspired by Hu et al. (2024), who proposed an FHE-based threshold PSI framework using encrypted Bloom Filters, threshold-dependent secret tokens, and standard PSI.

Our implementation adapts the general workflow to a student matching application with a trusted backend. It does not reproduce the paper's full distributed protocol or equivalent security guarantees.

**Reference:**

[1] J. Hu, Y. Zhao, B. H. M. Tan, K. M. M. Aung, and H. Wang, "Enabling threshold functionality for private set intersection protocols in cloud computing," *IEEE Transactions on Information Forensics and Security*, vol. 19, pp. 6184–6196, 2024.

DOI: https://doi.org/10.1109/TIFS.2024.3402355
