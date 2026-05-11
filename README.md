# VoteSecure – Secure Electronic Voting System

## Overview

VoteSecure is a distributed electronic voting system built using cryptographic techniques to ensure:

- Voter anonymity
- Vote integrity
- Eligibility verification

The system simulates a real-world secure voting protocol using RSA encryption, blind signatures, and hashing.

---

## Features

- Blind signature voting (Chaum protocol)
- RSA encryption/decryption
- Secure voter authentication (N1 codes)
- Anonymous vote submission
- Hash-based verification of voter identity (N2)
- Distributed microservice architecture
- REST API communication between services

---

## System Architecture

The system is composed of 5 independent services:

| Entity        | Role |
|---------------|------|
| Commissioner  | Manages voter eligibility (N1, N2 hashes) |
| Administrator | Signs blinded ballots |
| Anonymiser    | Removes voter identity and stores votes |
| Decompteur    | Decrypts and counts votes |
| Website       | User interface |

---

## Project Structure

```
VoteSecure/
│── config.py
│── run.py
│── requirements.txt
│
├── crypto/          # Cryptographic primitives
├── entities/        # Server logic (Flask apps)
├── website/         # Backend web app
├── frontend/        # React frontend
├── tests/           # Test suite
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/1sma31L/VoteSecure
cd VoteSecure
```

### 2. Install dependencies

```bash
cd frontend && npm run install build && npm run build
cd ..
pip install -r requirements.txt
```

---

## Running the Project

### Option 1: Run full simulation

```bash
python run.py
```

---

### Option 2: Run services manually

Start each service in a separate terminal:

```bash
python entities/commissioner.py
python entities/administrator.py
python entities/anonymiser.py
python entities/decompteur.py
python website/app.py
```

---

## Configuration

All service URLs and ports are defined in:

```
config.py
```

You can modify IPs and ports depending on your setup.

---

## Voting Process

### 1. Setup Phase
- RSA keys are generated
- Voter codes (N1, N2) are created
- N2 hashes are stored

### 2. Voting Phase
- Voter logs in using N1
- Vote is encoded and blinded
- Administrator signs blinded vote
- Vote is encrypted and sent anonymously

### 3. Counting Phase
- Votes are decrypted
- Signatures are verified
- N2 hashes are checked
- Votes are counted

---

## Running Tests

Run all tests:

```bash
pytest tests/crypto_tests/ -v
```

Run a specific test file:

```bash
pytest tests/crypto_tests/test_rsa_core.py -v
```

---

## Technologies Used

- Python
- Flask
- RSA Cryptography
- Blind Signatures
- SHA-256 Hashing
- Pytest

---

## Security Concepts

- Blind signatures ensure anonymity
- RSA ensures confidentiality
- Hashing ensures integrity
- Separation of services prevents data correlation

---

## Notes

- This project is for educational purposes
- TTH hash is a simplified pedagogical hash
- Not intended for real-world elections
