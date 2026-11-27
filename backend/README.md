# Privacy-Preserving Student Skill Matching

This project implements a privacy-preserving student skill matching system using a combination of:

- Bloom Filters
- Fully Homomorphic Encryption (FHE)
- Threshold Private Set Intersection
- ECDH-based Private Set Intersection
- FastAPI

The goal is to allow two students to determine whether they share enough common skills without revealing their complete private skill lists.

If the number of common skills reaches the required threshold, the shared skills can be revealed. Otherwise, no intersection is revealed.

---

## Project Idea

Assume two students have private skill sets.

Example:

Student A:

```text
Python
AI
Cybersecurity
Embedded Systems
```

Student B:

```text
Python
AI
Web
Databases
```

With a threshold of:

```text
2
```

the system determines whether at least two skills are shared.

In this example:

```text
Common skills = Python, AI
Intersection size = 2
Threshold = 2
```

Since the threshold is satisfied, the common skills may be revealed.

If the number of common skills is smaller than the threshold, the protocol returns no intersection.

---

## Privacy Goal

The system aims to prevent either participant from learning the other participant's complete skill list.

The protocol only allows the intended result to be revealed.

The main privacy-preserving flow is:

```text
Student A Skills
        |
        v
Bloom Filter
        |
        v
Encrypted Bloom Filter
        |
        v
FHE Membership Tests
        |
        v
Encrypted Match Count
        |
        v
Threshold Check
        |
        v
K or K'
        |
        v
ECDH PSI
        |
        v
Common Skills or Empty Result
```

---

## System Components

### 1. Bloom Filter

Student A's skill list is converted into a Bloom Filter.

Current Proof-of-Concept parameters:

```text
Bloom Filter size = 128 bits
Number of hash functions = 5
```

Each skill is normalized and mapped deterministically to five Bloom Filter positions.

The same hashing method is used when checking Student B's skills.

---

### 2. FHE Threshold Evaluation

The project uses Concrete Python for Fully Homomorphic Encryption.

Student A's Bloom Filter is encrypted before the membership computation.

For each skill provided by Student B, the system calculates the same five Bloom Filter positions and checks them against Student A's encrypted Bloom Filter.

The system then homomorphically calculates the number of matching skills.

The current PoC uses a fixed threshold:

```text
Threshold = 2
```

The threshold condition is:

```text
intersection_count >= 2
```

The server generates two tokens:

```text
K  = correct server token
K' = random token
```

If the threshold condition is satisfied, the FHE circuit produces:

```text
K
```

Otherwise, it produces:

```text
K'
```

The current PoC uses a 4-bit token representation for compatibility with the Concrete FHE circuit.

---

### 3. ECDH Private Set Intersection

After the FHE threshold stage, the tokens are passed to the ECDH PSI implementation.

The skills are tagged using the tokens before the PSI operation.

If:

```text
client token == server token
```

then matching skills generate matching PSI values and the intersection can be recovered.

If:

```text
client token != server token
```

then even identical skills produce different tagged values and the PSI result becomes empty.

Therefore:

```text
Threshold satisfied
        ->
K == K'
        ->
Common skills can be revealed
```

and:

```text
Threshold not satisfied
        ->
Tokens differ
        ->
Common skills are not revealed
```

---

## Backend Flow

The backend performs the following steps:

```text
1. Receive Student A skills
2. Receive Student B skills
3. Create Student A Bloom Filter
4. Encrypt the Bloom Filter using FHE
5. Compute Student B membership checks
6. Count the encrypted matches
7. Compare the match count with the threshold
8. Generate the appropriate token
9. Run ECDH PSI
10. Return the final result
```

---

## Project Structure

A simplified structure of the project is:

```text
Privacy-Preserving-Student-Skill-Matching/
│
├── backend/
│   ├── bloom_and_psi.py
│   ├── fhe_threshold.py
│   ├── interfaces.py
│   ├── main.py
│   │
│   └── tests/
│       ├── test_psi.py
│       └── test_fhe_threshold.py
│
├── frontend/
│
├── requirements.txt
└── README.md
```

### Main Backend Files

#### `backend/bloom_and_psi.py`

Contains:

- Skill normalization
- Bloom Filter creation
- Deterministic Bloom Filter indices
- ECDH Private Set Intersection

#### `backend/fhe_threshold.py`

Contains:

- Student B membership mask generation
- FHE Bloom Filter membership evaluation
- Encrypted intersection counting
- Threshold evaluation
- Token generation
- FHE circuit compilation and execution

#### `backend/main.py`

Contains:

- FastAPI application
- API request and response models
- Integration between Bloom Filter, FHE threshold evaluation, and ECDH PSI

---

## Backend Requirements

The FHE component uses Concrete Python.

For the current PoC, the backend should be run using:

```text
Ubuntu/Linux
Python 3.12
```

The project was tested using Python 3.12.

Concrete Python was not run using the system Python 3.14 environment.

---

## Python Environment Setup

The project can be run using a Python 3.12 virtual environment.

Install Python 3.12 using `uv`:

```bash
uv python install 3.12
```

Create a virtual environment:

```bash
uv venv --python 3.12 .venv
```

Activate the environment:

```bash
source .venv/bin/activate
```

Check the Python version:

```bash
python --version
```

Expected version:

```text
Python 3.12.x
```

---

## Install Dependencies

Install the project dependencies using:

```bash
uv pip install -r requirements.txt
```

The main backend dependencies include:

```text
concrete-python
numpy
bitarray
cryptography
fastapi
uvicorn
pydantic
pytest
```

---

## Running the Backend

Activate the virtual environment first:

```bash
source .venv/bin/activate
```

Then start the FastAPI server:

```bash
python -m uvicorn backend.main:app --reload
```

If successful, the server should run at:

```text
http://127.0.0.1:8000
```

---

## Swagger API Documentation

FastAPI automatically provides Swagger documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

The main endpoint is:

```text
POST /match
```

---

## Example API Request

Example request:

```json
{
  "student_a_skills": [
    "Python",
    "AI",
    "Cybersecurity",
    "Embedded Systems"
  ],
  "student_b_skills": [
    "Python",
    "AI",
    "Web",
    "Databases"
  ],
  "threshold": 2
}
```

---

## Example Successful Threshold Response

Since both students share:

```text
Python
AI
```

the threshold is satisfied.

Example response:

```json
{
  "threshold_satisfied": true,
  "common_skills": [
    "python",
    "ai"
  ],
  "fhe_latency_ms": 342.33
}
```

The latency value may differ between executions.

---

## Example Failed Threshold Request

```json
{
  "student_a_skills": [
    "Python",
    "Cybersecurity",
    "Embedded Systems"
  ],
  "student_b_skills": [
    "Python",
    "Web",
    "Databases"
  ],
  "threshold": 2
}
```

Only one skill is shared:

```text
Python
```

Therefore the threshold is not satisfied.

Example response:

```json
{
  "threshold_satisfied": false,
  "common_skills": [],
  "fhe_latency_ms": 320.15
}
```

---

## Testing

The project includes tests for the Bloom Filter, ECDH PSI, and FHE threshold module.

Run all backend tests using:

```bash
python -m pytest backend/tests -v
```

To test only the FHE threshold module:

```bash
python -m pytest backend/tests/test_fhe_threshold.py -v
```

The FHE tests include two important cases.

### Threshold Satisfied

Example:

```text
Student A:
Python
AI
Cybersecurity
Embedded Systems

Student B:
Python
AI
Web
Databases

Threshold = 2
```

Expected result:

```text
Threshold satisfied = True
Common skills = Python, AI
```

### Threshold Not Satisfied

Example:

```text
Student A:
Python
Cybersecurity
Embedded Systems

Student B:
Python
Web
Databases

Threshold = 2
```

Expected result:

```text
Threshold satisfied = False
Common skills = []
```

Both cases were tested successfully.

---

## Current PoC Parameters

The current implementation uses:

```text
Bloom Filter size: 128 bits
Hash functions: 5
Maximum Student B skills: 10
Threshold: 2
Token size: 4 bits
```

These values are selected for the Proof-of-Concept implementation and can be changed in future versions.

---

## Limitations

This project is a Proof-of-Concept and currently has several limitations.

### Fixed Threshold

The FHE circuit currently uses a fixed threshold of:

```text
2
```

Supporting a dynamic threshold would require changes to the compiled Concrete FHE circuit.

### Maximum Number of Server Skills

The current FHE circuit supports at most:

```text
10 Student B skills
```

because Concrete circuits require fixed input shapes.

### Bloom Filter False Positives

Bloom Filters are probabilistic data structures.

Therefore, a Bloom Filter membership test may theoretically produce false positives.

The current PoC uses a 128-bit Bloom Filter and five hash functions.

### Token Size

The current PoC uses a 4-bit token.

This smaller token size is used to maintain compatibility with the current Concrete FHE circuit implementation.

A production implementation would require a stronger token representation.

### Platform Requirement

The FHE backend currently runs on Linux/Ubuntu using Python 3.12.

---

## Technologies Used

```text
Python
Concrete Python
NumPy
Bitarray
Cryptography
FastAPI
Uvicorn
Pytest
```

---

## Summary

The project demonstrates how privacy-preserving technologies can be combined to perform student skill matching.

The system uses:

```text
Bloom Filter
+
Fully Homomorphic Encryption
+
Threshold Evaluation
+
ECDH Private Set Intersection
```

to ensure that students do not need to reveal their complete private skill sets.

The intersection is only revealed when the required number of common skills is reached.