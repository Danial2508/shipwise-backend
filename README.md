\# SHIPWISE AI



\## AI-Powered Shipping Document Intelligence



SHIPWISE is an AI-powered shipping document verification system designed to help shipping teams automate email classification, document information extraction, and Shipping Instruction (SI) versus Draft Bill of Lading (BL) comparison.



The system identifies discrepancies across key shipping fields and provides clear verification results for users.



\## Problem



Shipping teams handle large volumes of emails and documents every day. Manual verification of Shipping Instructions against Draft Bills of Lading is time-consuming and can lead to missed discrepancies.



SHIPWISE helps automate this verification workflow.



\## Key Features



\- AI email classification

\- Shipping document processing

\- Seven-field data extraction

\- SI vs Draft BL comparison

\- Automated verification

\- Human-in-the-loop review

\- Cloud-based dashboard

\- Firestore result storage



\## Seven Comparison Fields



SHIPWISE compares:



1\. Shipper

2\. Consignee

3\. Notify Party

4\. Port of Loading

5\. Port of Discharge

6\. Container Count

7\. Gross Weight (kg)



\## Verification Results



The system produces three main outcomes:



\- \*\*OK\*\* — documents match

\- \*\*MISMATCH\*\* — discrepancies detected

\- \*\*NEEDS REVIEW\*\* — human review required



\## AI Performance



Current validation results:



\- \*\*94.53% Overall Validation Score\*\*

\- \*\*100% Defect Recall\*\*

\- \*\*100% Defect Precision\*\*

\- \*\*100% Field-Level F1\*\*

\- \*\*46/46 Defect Emails Detected\*\*

\- Stage 1 Classification Accuracy: \*\*91.30%\*\*

\- Stage 1 Macro F1: \*\*81.80%\*\*



\## Technology Stack



\### Frontend

\- HTML

\- CSS

\- JavaScript

\- Firebase Hosting



\### Backend

\- Python

\- FastAPI

\- Render



\### Cloud

\- Firebase Firestore



\### Document Processing

\- PDF processing

\- Word document processing

\- OCR/image document handling



\## System Architecture



```text

User

&#x20; ↓

SHIPWISE Web Dashboard

&#x20; ↓

Firebase Hosting

&#x20; ↓

FastAPI Backend

&#x20; ↓

Render

&#x20; ↓

Document Processing \& AI Pipeline

&#x20; ↓

SI vs Draft BL Comparison

&#x20; ↓

Firestore

