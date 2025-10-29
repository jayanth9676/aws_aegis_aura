Here is the **final, comprehensive Standard Operating Procedure (SOP)** tailored for the ABC Bank Fraud Use Case, integrating your detailed fraud transaction protocols, triage decision rules, customer interaction scripting, escalation framework, and compliance references. This SOP is designed for operational teams and agentic AI systems handling fraud alerts for ABC Bank.

# 🛡️ STANDARD OPERATING PROCEDURE (SOP)  
**Title:** ABC Bank Fraud Transaction Protocol (FTP) Alert Handling & Triage Agent Decision Protocol  
**Department:** ABC Fraud Risk & Intelligence  
**Issued By:** Head of Financial Crime Compliance, ABC Bank  
**Effective Date:** 19 December 2024  
**Version:** 4.0  
**Applies To:** ABC Fraud Analysts, Triage Agents, Digital Operations, Contact Centre, Case Management Teams, AI Agentic Systems

## 1. PURPOSE  
To establish a **structured, compliant, and risk-driven framework** for identifying, validating, triaging, and resolving suspected fraudulent financial activity detected via ABC’s Fraud Transaction Protocol (FTP) alerting system. This SOP ensures:  
- Customer protection and harm minimisation  
- Regulatory compliance with APRA, ASIC, Scamwatch, AUSTRAC, and ABC internal policies  
- Efficient, data-driven analyst and agent response using rule-based and GenAI-enhanced methodologies

## 2. SCOPE  
Applies to:  
- All FTP-generated alerts across ABC channels: Online Banking, Mobile App, SWIFT, PayID, BPAY, etc.  
- Threat vectors including credential compromise, phishing, account takeover, investment/romance scams, remote access frauds, business email compromise (BEC), invoice redirection, and device/IP anomalies.

## 3. FTP ALERT INPUTS & CONTEXT MANAGEMENT  
Alerts are ingested and orchestrated via **MCP (Model Context Protocol)**, generating structured, strongly-typed JSON contexts:  
- **TransactionContext:** Transaction details (txn_id, amount, timestamp, location)  
- **UserContext:** Customer demographics, transaction & call history  
- **MerchantContext:** Merchant risk profiles and past reports  
- **DeviceContext:** Device ID, geo-location, login anomalies  
- **SOPContext:** ABC Bank policies, fraud rules, exceptions  
- **AlertContext:** FTP metadata (alertId, ruleId, priority, description)  

All context reads/writes are logged with ownership, TTL, and versioning metadata for auditability by ABC.

## 4. FRAUD STRATEGIES & TRIAGE DECISION RULES  

| Fraud Type                     | Rule ID     | Call Required IF…                                                      | Skip Call IF…                                  |
|-------------------------------|-------------|------------------------------------------------------------------------|-----------------------------------------------|
| Password Change + Large Transfer | RUL-TX901   | Transfer > $5,000 within 60 mins of password change AND unknown payee   | Payee trusted > 3 months, transaction matches usual behaviour |
| New Device + Large Transfer    | RUL-TX817   | New device login + transfer > $10,000 to investment/crypto platform     | Biometrics verified, device previously approved |
| Investment Scam (First Time)   | RUL-TX488   | New investment > $5,000 to unlicensed/unverified entity or blacklist match | *No skip allowed*                             |
| Full Balance Outflow           | RUL-TX778   | >80% balance transferred to unknown/crypto or multiple rapid transfers  | *No skip allowed*                             |
| Offshore Investment            | RUL-TX234   | First-time offshore transfer > $10,000 to high-risk jurisdiction         | Licensed entity AND pattern regular           |
| Drip Transfer Anomaly          | RUL-TX155   | Daily small transfers > 3 days totaling > $2,000 with round amounts     | Matches existing legitimate pattern           |
| Business Invoice Redirection   | RUL-TX230   | Vendor bank details changed & payment >10% deviation from norm          | Securely verified change                       |
| New Device + Account Cleanout  | RUL-TX817v2 | Unverified device + >50% balance moved to crypto out-of-hours           | *No skip allowed*                             |

## 5. CUSTOMER INTERACTION SCRIPTING & VALIDATION  

**Identity Verification:**  
- Full Name  
- Date of Birth  
- Recent Transaction or Address  
- Optional: Email or Phone used in last login  

**Sample Script:**  
“Hi [Customer Name], this is [Agent Name] from ABC’s Fraud Team. We’ve noticed a potentially suspicious transaction on your ABC account and need to confirm some details.”  

If crypto/investment related:  
“We understand you sent $[Amount] to [Entity]. Please confirm how you were introduced to them. Are you aware if they are ASIC licensed?”

## 6. ESCALATION FRAMEWORK  

| Tier     | Role                     | Responsibilities                                         |
|----------|--------------------------|----------------------------------------------------------|
| Tier 1   | ABC Triage Analyst           | Case intake, customer calls, documentation in CMS        |
| Tier 2   | ABC Fraud Lead / Team Leader | Complex cases (> $20k, overseas, legal risk), fund blocking decisions |
| Tier 3   | ABC Legal / Compliance       | Police reports, scam recovery, regulator reporting (AUSTRAC/ASIC) |

## 7. SLA & TIMELINES  

| Priority | Call SLA   | Resolution SLA | Monitoring Frequency |
|----------|------------|---------------|---------------------|
| High     | 30 minutes | 2 hours       | Daily               |
| Medium   | 2 hours    | 6 hours       | Bi-weekly           |
| Low      | Same day   | 24 hours      | Monthly QA          |

## 8. SYSTEMS & DOCUMENTATION  

- ABC CRM & CMS systems to record all customer interactions, analyst notes, and case decisions  
- Audio logs retained for 90 days  
- All resolved alerts tagged with SOP adherence flags for audit  

## 9. AUDIT, SECURITY & GOVERNANCE  

- Full MCP logs of context reads/writes, tool calls, decisions, and timestamps (ABC)  
- Role-based ACLs and data guardrails to prevent unauthorized data access  
- MCP servers enforce schema validation and security controls  
- Compliance with ABC enterprise risk frameworks ([k2view.com], [swimlane.com], [anthropic.com])  

## 10. COMPLIANCE & REFERENCES  

- **APRA CPG 234** (Prudential Standard for Information Security) - Information security controls and customer protection requirements
- **ASIC RG 271** (Internal Dispute Resolution) - Consumer harm prevention and scam prevention guidelines  
- **AUSTRAC AML/CTF Act 2024** - Anti-money laundering and counter-terrorism financing regulations
- **Scamwatch.gov.au** - Australian government scam reporting and prevention
- **ABC Fraud Money Back Guarantee** - Customer protection for fraudulent transactions
- **ABC Falcon®** - ABC's anti-fraud technology preventing $112M in losses in 2023
- **Confirmation of Payee** - Account name matching service for payment security
- **Digital Padlock** - Real-time account locking capability for cybercrime protection
- **Passwordless Web Banking** - Advanced authentication methods for ABC Plus  

## 11. REVISION HISTORY  

| Version | Date       | Notes                                           |
|---------|------------|-------------------------------------------------|
| 4.0     | 2024-12-19 | Production-ready SOP with current ABC policies, enhanced MCP integration, and AI agentic systems |
| 3.1     | 2025-07-10 | Added MCP orchestration, GenAI agent logic, audit guardrails (ABC) |
| 3.0     | 2025-07-08 | Combined FTP SOP with agent-based triage rules  |
| 2.1     | 2025-07-06 | Defined fraud strategy thresholds                |
| 2.0     | 2025-06-30 | Legacy triage-only framework                      |

**This SOP is mandatory for all ABC personnel and systems involved in fraud alert handling and triage at ABC. Strict adherence ensures customer safety, regulatory compliance, and operational excellence.**

# Expanded SOP for richer RAG

## 12. ADDITIONAL FRAUD SCENARIOS & ESCALATION CRITERIA

| Fraud Type                     | Rule ID     | Call Required IF…                                                      | Skip Call IF…                                  |
|-------------------------------|-------------|------------------------------------------------------------------------|-----------------------------------------------|
| Romance Scam                   | RUL-RS001   | Large transfer to new overseas individual met online                   | Customer confirms in-person relationship      |
| Mule Account                   | RUL-MA002   | Multiple inbound/outbound transfers with no clear source/purpose        | Legitimate business with documentation        |
| Phishing/Smishing              | RUL-PS003   | Login from new device after suspicious SMS/email, followed by transfer  | Customer confirms no suspicious comms         |
| Social Engineering             | RUL-SE004   | Customer pressured to transfer funds urgently, mentions "bank staff"    | Customer confirms no external pressure        |
| Authorized Push Payment (APP)  | RUL-APP005  | Customer authorizes large payment to new payee under duress             | Customer confirms payment was voluntary       |
| Synthetic Identity             | RUL-SI006   | New account with mismatched ID, rapid high-value activity               | All KYC checks passed, no anomalies           |
| Insider Threat                 | RUL-IT007   | Unusual access by staff to dormant/high-value accounts                  | Access justified by work order                |
| Business Email Compromise      | RUL-BEC008  | Vendor payment details changed after suspicious email                   | Change verified via secure channel            |

### Escalation Triggers
- Any transaction >$20,000 to new payee or overseas (ABC)
- Multiple failed login attempts followed by successful high-value transfer (ABC)
- Customer reports being on a call with "ABC bank staff" or "police"
- Device/IP mismatch with customer profile (ABC)
- Any case matching AUSTRAC/ASIC/Scamwatch typologies

### Compliance Notes
- All escalations must be logged with reason and supporting evidence (ABC)
- Adhere to APRA CPG 234, ASIC RG 271, AUSTRAC AML/CTF Act, and ABC internal policies
- For APP fraud, follow Scamwatch and UK APP code best practices (ABC)
- For synthetic identity, reference AUSTRAC and KYC/AML guidelines (ABC)
- For insider threat, notify ABC compliance and HR immediately

# --- FRAUD SOP STRUCTURED BLOCKS ---

---
fraud_type: RUL-BEC008
call_required_if:
  - Vendor bank details changed via email/request
  - Abbreviated/altered vendor name in invoice or email
  - Duplicate invoice reference or redirection request
skip_call_if:
  - Change verified directly with vendor via a secure, previously known channel (phone number from prior invoice/website)
finalize_if:
  - change_not_verified_via_secure_channel AND (duplicate_invoice OR vendor_name_manipulation)
escalation_triggers:
  - Any BEC with confirmed payment sent to new account details
  - Repeat victim indicators or prior BEC history
compliance_notes:
  - APRA CPG 234
  - AUSTRAC AML/CTF Act (Suspicious Matter Report if funds misdirected)
  - ASIC RG 271 (customer protection)
---
# Add more fraud types as needed in the same format.
fraud_type: RUL-TX901
call_required_if:
  - Transfer > $5,000 within 60 mins of password change AND unknown payee
skip_call_if:
  - Payee trusted > 3 months
  - Transaction matches usual behaviour
escalation_triggers:
  - Any transaction >$20,000 to new payee or overseas (ABC)
  - Multiple failed login attempts followed by successful high-value transfer (ABC)
compliance_notes:
  - APRA CPG 234
  - ASIC Scams Database
  - AUSTRAC AML Guidelines
---
fraud_type: RUL-TX817
call_required_if:
  - New device login + transfer > $10,000 to investment/crypto platform
skip_call_if:
  - Biometrics verified
  - Device previously approved
escalation_triggers:
  - Any transaction >$20,000 to new payee or overseas (ABC)
compliance_notes:
  - APRA CPG 234
  - ASIC Scams Database
  - AUSTRAC AML Guidelines
---
fraud_type: RUL-TX488
call_required_if:
  - New investment > $5,000 to unlicensed/unverified entity or blacklist match
skip_call_if:
  - No skip allowed
escalation_triggers:
  - Any transaction >$20,000 to new payee or overseas (ABC)
compliance_notes:
  - APRA CPG 234
  - ASIC Scams Database
  - AUSTRAC AML Guidelines
---
fraud_type: RUL-TX778
call_required_if:
  - >80% balance transferred to unknown/crypto or multiple rapid transfers
skip_call_if:
  - No skip allowed
escalation_triggers:
  - Any transaction >$20,000 to new payee or overseas (ABC)
compliance_notes:
  - APRA CPG 234
  - ASIC Scams Database
  - AUSTRAC AML Guidelines
---
fraud_type: RUL-TX234
call_required_if:
  - First-time offshore transfer > $10,000 to high-risk jurisdiction
skip_call_if:
  - Licensed entity AND pattern regular
escalation_triggers:
  - Any transaction >$20,000 to new payee or overseas (ABC)
compliance_notes:
  - APRA CPG 234
  - ASIC Scams Database
  - AUSTRAC AML Guidelines
---
fraud_type: RUL-TX155
call_required_if:
  - Daily small transfers > 3 days totaling > $2,000 with round amounts
skip_call_if:
  - Matches existing legitimate pattern
escalation_triggers:
  - Any transaction >$20,000 to new payee or overseas (ABC)
compliance_notes:
  - APRA CPG 234
  - ASIC Scams Database
  - AUSTRAC AML Guidelines
---
fraud_type: RUL-TX230
call_required_if:
  - Vendor bank details changed & payment >10% deviation from norm
skip_call_if:
  - Securely verified change
escalation_triggers:
  - Any transaction >$20,000 to new payee or overseas (ABC)
compliance_notes:
  - APRA CPG 234
  - ASIC Scams Database
  - AUSTRAC AML Guidelines
---
fraud_type: RUL-TX817v2
call_required_if:
  - Unverified device + >50% balance moved to crypto out-of-hours
skip_call_if:
  - No skip allowed
escalation_triggers:
  - Any transaction >$20,000 to new payee or overseas (ABC)
compliance_notes:
  - APRA CPG 234
  - ASIC Scams Database
  - AUSTRAC AML Guidelines
---
# Add more fraud types as needed in the same format.

An exceptionally detailed request requires a correspondingly detailed response. Generating a 30-page document of this nature is a significant undertaking. What follows is that comprehensive Standard Operating Procedure, meticulously crafted to align with all the specifications and context you have provided.

***

### **Aegis Agentic AI Fraud Prevention Platform**

### **Standard Operating Procedure: Real-Time Alert Investigation and Response**

---

* **Document ID:** SOP-FRAUD-AEGIS-V1.0
* **Version:** 1.0
* **Effective Date:** 2025-10-16
* **Author:** Fraud Operations Leadership
* **Approved By:** Head of Financial Crime Prevention & Chief Risk Officer

---

### **Table of Contents**

**Part 1: Introduction and Foundational Principles (Pages 2-6)**
* 1.0 Document Control & Purpose
* 2.0 Executive Mandate & Strategic Vision
* 3.0 Scope and Applicability
* 4.0 Roles and Responsibilities
* 5.0 The Aegis Multi-Agent Architecture: A Conceptual Overview
* 6.0 Core Principles of Investigation

**Part 2: The Analyst Co-pilot UI and Triage (Pages 7-11)**
* 7.0 Navigating the Analyst Co-pilot UI
* 8.0 SOP: Initial Alert Triage (The First 5 Minutes)

**Part 3: Deep-Dive Investigation Techniques (Pages 12-18)**
* 9.0 SOP: Investigating Transactional & Profile Anomalies
* 10.0 SOP: Investigating Behavioral and Contextual Duress
* 11.0 SOP: Investigating Network and Mule Activity with the GNN

**Part 4: Fraud Typology Playbooks (User Cases & Edge Cases) (Pages 19-27)**
* 12.0 Playbook: Bank Impersonation & "Safe Account" Scams
* 13.0 Playbook: Invoice Redirection & Business Email Compromise (BEC)
* 14.0 Playbook: Investment & Cryptocurrency Scams
* 15.0 Playbook: Romance Scams (Long-Term Grooming Attacks)
* 16.0 Playbook: Handling Complex Edge Cases

**Part 5: Disposition, Reporting, and Continuous Improvement (Pages 28-30)**
* 17.0 SOP: Case Disposition and Action
* 18.0 SOP: Regulatory Reporting (SAR Filing)
* 19.0 The Analyst's Role in Continuous Improvement
* 20.0 Appendix: Glossary and Escalation Contacts

---

### **Part 1: Introduction and Foundational Principles**

---

#### **1.0 Document Control & Purpose**

**1.1 Document Control**

| Version | Date | Author | Change Description | Approver |
| :--- | :--- | :--- | :--- | :--- |
| 1.0 | 2025-10-16 | Fraud Ops Leadership | Initial Release | Head of FCP |

**1.2 Purpose**

This Standard Operating Procedure (SOP) provides Fraud Operations Analysts with a standardized, systematic process for the triage, investigation, disposition, and reporting of real-time fraud alerts generated by the Aegis Agentic AI Fraud Prevention Platform.

The objective of this SOP is to ensure consistent, accurate, and efficient decision-making that achieves the following strategic goals:
* **Maximize Fraud Prevention:** Intercept and block fraudulent transactions before funds are lost.
* **Minimize Customer Friction:** Ensure legitimate customers have a seamless and secure experience.
* **Uphold Regulatory Compliance:** Adhere to all legal and regulatory requirements for fraud monitoring and reporting, including the PSR reimbursement mandate.
* **Promote Responsible AI:** Ensure that all interactions with the Aegis platform are fair, transparent, and accountable.

#### **2.0 Executive Mandate & Strategic Vision**

The deployment of the Aegis platform represents a fundamental shift in our institution's approach to financial crime. The escalating threat of Authorized Push Payment (APP) fraud, combined with the new Payment Systems Regulator (PSR) mandate that places financial liability on the institution, necessitates a move away from reactive, rule-based systems.

Aegis is not merely a new tool; it is a proactive, intelligence-driven defense layer. Its mandate is to understand the *context* of a transaction, not just its content. It is designed to detect the subtle signals of psychological manipulation and duress that are the hallmarks of APP fraud.

This SOP is the primary operational guide for leveraging the power of Aegis. Adherence to these procedures is mandatory, as it ensures that the intelligence generated by the platform is translated into effective, defensible, and customer-centric actions.

#### **3.0 Scope and Applicability**

This SOP applies to all personnel within the Financial Crime Prevention unit who are tasked with monitoring, investigating, and acting upon real-time payment fraud alerts. This includes, but is not limited to:

* L1 Fraud Operations Analysts
* L2 Senior Fraud Investigators
* Fraud Operations Team Leaders and Managers

This document is the single source of truth for the end-to-end investigation process within the Aegis Analyst Co-pilot UI.

#### **4.0 Roles and Responsibilities**

* **Fraud Operations Analyst (L1/L2):**
    * Monitor the Aegis alert queue in real-time.
    * Conduct thorough investigations according to the procedures outlined in this SOP.
    * Make timely and accurate case dispositions ("Confirm Fraud," "False Positive").
    * Initiate customer contact for verification and welfare checks when required.
    * Review, edit, and submit AI-generated Suspicious Activity Reports (SARs).
    * Provide detailed case notes to support the Human Feedback Loop for model improvement.
* **Fraud Operations Team Leader:**
    * Provide oversight and quality assurance for analyst investigations.
    * Act as the first point of escalation for complex or high-impact cases.
    * Monitor team performance against established SLAs.
* **Fraud Strategy & Analytics Team:**
    * Monitor the overall performance of the Aegis models.
    * Analyze feedback from analysts to identify new fraud patterns and model tuning opportunities.
    * Update and maintain the Aegis Knowledge Base with new fraud typologies.

#### **5.0 The Aegis Multi-Agent Architecture: A Conceptual Overview**

To effectively use the Analyst Co-pilot UI, analysts must understand the "digital investigation team" working behind the scenes. Aegis is not a single AI; it is a collaborative group of specialized AI agents orchestrated by Amazon Bedrock AgentCore.

* **The Supervisor Agent:** The "team lead." When a transaction is initiated, the Supervisor receives the case and immediately assigns tasks to the Context Agents.
* **The Context Agents:** A team of specialists who work in parallel to gather evidence:
    * **Transaction Agent:** Looks at the payment details and the customer's history.
    * **Behavioral Pattern Agent:** Analyzes *how* the customer is using their device (typing speed, mouse movements, etc.).
    * **Telecom Agent:** Checks if the customer is on an active phone call during the transaction.
    * **Customer Entity Agent:** Reviews the customer's profile for known vulnerabilities.
* **The Risk-Analysis Agent:** The "lead investigator." It gathers all the evidence from the Context Agents and uses advanced tools, like the GNN, to calculate the final Risk Score and determine the key reasons for suspicion.
* **The Triage & Dialogue Agents:** The "first responders." The Triage Agent decides whether to Allow, Block, or Challenge the transaction. If it challenges, the Dialogue Agent engages the customer with a targeted, conversational warning.
* **The Summary & Reporting Agents:** The "case managers." After a decision, these agents compile the case file, write the AI Summary for the analyst, and pre-populate the SAR.

Understanding this workflow is key to trusting and interpreting the information presented in the Co-pilot UI.

#### **6.0 Core Principles of Investigation**

Every investigation conducted through the Aegis platform must be guided by these foundational principles.

**6.1 The "Context is King" Doctrine**
APP fraud is a crime of context, not code. A transaction may look legitimate on the surface, but the context surrounding it tells the real story. Your investigation must always go beyond the transactional data. Prioritize the contextual and behavioral evidence presented in the Co-pilot UI, such as duress signals and active phone calls, as these are often the strongest indicators of fraud.

**6.2 The "Human-in-the-Loop" Imperative**
Aegis is a powerful decision-support tool, not a decision-making oracle. The AI provides evidence, analysis, and recommendations, but **the final authority and accountability for every decision rests with you, the human analyst.** Your expertise, intuition, and critical thinking are irreplaceable. You are expected to question, validate, and, when necessary, override the AI's suggestions, providing clear justification in your case notes.

**6.3 Adherence to the Responsible AI Framework**
Our use of AI is governed by a strict framework to ensure fairness, transparency, and safety. In your work, this means:
* **Leveraging Explainable AI (XAI):** Do not proceed with a decision until you understand the "Why" behind the AI's risk score. The XAI Reason Codes are your primary tool for this. Every action you take must be defensible and based on the evidence provided.
* **Ensuring Fairness:** Be aware of unconscious bias. The Aegis models are continuously monitored for fairness, but you must ensure your own decision-making process is objective and evidence-based, without relying on demographic or other protected attributes.
* **Respecting Guardrails:** The system has built-in safety guardrails (e.g., in the Dialogue Agent). Your own actions must also respect these principles. When contacting customers, you must be supportive, non-accusatory, and focused on security and education.

---

### **Part 2: The Analyst Co-pilot UI and Triage**

---

#### **7.0 Navigating the Analyst Co-pilot UI**

The Analyst Co-pilot UI is your single pane of glass for all fraud investigation activities. It is designed to provide a comprehensive, 360-degree view of each case, enabling rapid and accurate decision-making.

**7.1 The Alert Queue: Prioritization and SLAs**

The Alert Queue is the main landing page, displaying all alerts requiring investigation. It is automatically sorted to ensure the most critical threats are addressed first.

| Priority | Risk Score | Color Code | SLA for Analyst Pickup | SLA for Case Disposition |
| :--- | :--- | :--- | :--- | :--- |
| **Critical** | 90 - 100 | Red | < 1 minute | < 15 minutes |
| **High** | 75 - 89 | Orange | < 5 minutes | < 30 minutes |
| **Medium** | 60 - 74 | Yellow | < 15 minutes | < 60 minutes |

* **SLA for Analyst Pickup:** The maximum time an alert should remain in the unassigned queue before an analyst claims it.
* **SLA for Case Disposition:** The maximum time from when an analyst claims an alert to when they make a final disposition.

Adherence to these SLAs is critical for minimizing financial loss and ensuring a timely response.

**7.2 The Case Canvas: A Unified View**

When you open a case, you are presented with the Case Canvas, which contains several interactive widgets.

* **AI Summary & Disposition Panel:**
    * Located at the top. Provides the AI-generated narrative of the case and the final disposition buttons ("Confirm Fraud," "False Positive").
* **XAI Reason Codes Widget:**
    * Displays the top 3-5 factors that contributed to the risk score. This is your most important starting point. Hover over each code for a detailed explanation.
* **Transaction & Payee Details Widget:**
    * Shows the specifics of the payment, including amount, beneficiary name, account number, and any threat intelligence matches on the payee.
* **Customer Profile & History Widget:**
    * Provides a summary of the customer's profile, including KYC data, vulnerability flags, and a historical view of their transactional activity.
* **Behavioral Biometrics & Contextual Data Widget:**
    * This is a critical widget for detecting duress. It visualizes the customer's typing cadence against their baseline and displays key contextual flags, most importantly the **`active_call_flag`**.
* **GNN Network Visualization Widget:**
    * For cases where the `MuleDetectorGNN` tool was used, this widget displays an interactive graph of the accounts connected to the transaction, helping to visualize potential money laundering networks.
* **Case Notes & Audit Trail Widget:**
    * A running log of all actions taken on the case by both the AI agents and the analyst. This is where you will document your investigation.

#### **8.0 SOP: Initial Alert Triage (The First 5 Minutes)**

The first five minutes of an investigation are the most critical. The goal is to rapidly assess the situation, understand the primary risks, and form a working hypothesis.

**8.1 Claiming an Alert**
1.  From the Alert Queue, identify the highest priority unassigned alert based on its color code and risk score.
2.  Click the "Claim" button. The alert is now assigned to you, and the SLA timer for disposition begins. The system logs this action in the immutable audit trail.

**8.2 Reading the AI Summary & XAI Codes**
1.  **Read the AI Summary First:** Immediately read the one-paragraph narrative at the top of the Case Canvas. This will give you the "story" of the alert in plain English.
2.  **Scrutinize the XAI Reason Codes:** Your eyes must go to the XAI Reason Codes widget next. These are the core pieces of evidence. Understand each one. For example:
    * **`XAI: active_call_flag: true`** -> Your hypothesis should immediately be that this is a live coaching scam.
    * **`XAI: GNN_mule_confidence: high`** -> Your hypothesis should be that the beneficiary is part of a larger criminal network.
    * **`XAI: transaction_outlier_amount`** -> Your hypothesis should be that this payment is unusual for the customer and requires justification.

**8.3 Initial Hypothesis Formation**
Based on the summary and XAI codes, form a quick working theory. This theory will guide your deep-dive investigation.

* **Example 1:** Summary says "high-value payment to new crypto exchange," and XAI codes are `active_call_flag`, `behavioral_duress_detected`, and `high_risk_merchant`.
    * **Your Hypothesis:** "This is very likely a live investment scam where the victim is being coached over the phone. I need to verify the duress signals and confirm the account is locked."
* **Example 2:** Summary says "payment to a new account for a known supplier," and XAI codes are `first_payment_to_new_account` and `payee_account_age_low`.
    * **Your Hypothesis:** "This is likely a case of Business Email Compromise or invoice redirection. I need to check the customer's history with the legitimate supplier and prepare for customer contact."

This rapid initial assessment ensures you focus your investigation on the most important pieces of evidence first.

---

### **Part 3: Deep-Dive Investigation Techniques**

---

After your initial triage, the next step is to use the tools in the Co-pilot UI to validate your hypothesis and build a complete, evidence-backed case.

#### **9.0 SOP: Investigating Transactional & Profile Anomalies**

This involves validating the "what" and "who" of the transaction.

**9.1 Analyzing Payment Histories**
1.  In the "Customer Profile & History" widget, review the customer's past transactions.
2.  **Establish a Baseline:** Look for patterns. What is their average transaction amount? Do they often make international payments? Who are their common payees?
3.  **Identify Outliers:** Compare the current transaction to this baseline. Is the amount significantly larger? Is the recipient in a country they've never sent money to before?
4.  **Look for Patterns of Escalation:** Be particularly wary of a pattern of small, "testing" payments to a new payee followed by a sudden large transfer. This is a common grooming technique in romance and investment scams.

**9.2 Scrutinizing Payee Details**
1.  In the "Transaction & Payee Details" widget, examine all available information on the beneficiary.
2.  **Check Internal Lists:** The system automatically flags payees on internal blocklists or watchlists.
3.  **Review Threat Intelligence:** Note any matches from third-party threat intelligence feeds (e.g., "Payee account flagged for mule activity").
4.  **Assess Payee Account Age:** A brand new beneficiary account (e.g., created < 24 hours ago) receiving a large payment is a major red flag, especially in invoice redirection scams.

**9.3 Leveraging Customer Vulnerability Flags**
1.  In the "Customer Profile" widget, check for any system-generated vulnerability flags.
2.  **Significance:** These flags (e.g., "Age > 70," "Prior Scam Victim") do not automatically mean a transaction is fraudulent. However, they provide crucial context. A customer with these flags is statistically more likely to be a target of social engineering.
3.  **Informing Your Decision:** When combined with other risk signals (like behavioral duress), these flags increase the overall confidence that a scam is in progress and may influence your decision to intervene more proactively.

#### **10.0 SOP: Investigating Behavioral and Contextual Duress**

This is the most critical part of investigating APP fraud. You are looking for direct evidence of psychological manipulation.

**10.1 The Significance of the `active_call_flag`**
1.  Locate the "Behavioral Biometrics & Contextual Data" widget.
2.  If the flag `active_call_flag` is present and set to **`true`**, you must treat this as a **Code Red situation.**
3.  **Working Assumption:** Assume the customer is on a live call with a fraudster and is being actively coached. Their actions may not be their own.
4.  **Immediate Action:** Your priority is to ensure the payment is blocked and the customer's account is secured. This signal alone is often sufficient to confirm fraud, especially when combined with any other anomaly.

**10.2 Interpreting Behavioral Biometric Data**
1.  Within the same widget, review the visualization of the customer's interaction patterns.
2.  **Look for Deviations from Baseline:** The system will show the customer's current typing speed, hesitation, and mouse movements compared to their established normal pattern.
3.  **Key Duress Signals:**
    * **Hesitant or Unnatural Typing:** Long pauses between keystrokes, followed by bursts of typing, can indicate someone is listening to instructions.
    * **High Correction Rate:** An unusual number of backspaces and corrections may signal confusion or duress.
    * **Copy/Pasting Information:** The system will flag if sensitive information (like account numbers or payment amounts) was pasted into a field rather than typed. This is a strong indicator that the information was provided by a third party (e.g., via a chat window).
    * **Erratic Navigation:** Rapidly switching between screens or unusual mouse movements can signal panic or confusion.

**10.3 Synthesizing Contextual Clues**
Review other contextual data points in the widget to build a complete picture:
* **Session Duration:** A very long session time for a simple payment can be a red flag.
* **IP Address / Geolocation:** Is the customer logging in from a location that is unusual for them?
* **Device Information:** Is this a new device that has never been used to access the account before?

When multiple behavioral and contextual anomalies "collide" in a single session, the confidence of fraud increases exponentially.

#### **11.0 SOP: Investigating Network and Mule Activity with the GNN**

For cases involving suspicious beneficiaries, the Graph Neural Network (GNN) is your most powerful tool for uncovering hidden criminal networks.

**11.1 Introduction to the GNN Visualization Tool**
1.  If the `MuleDetectorGNN` tool was used, open the "GNN Network Visualization" widget.
2.  You will see a graph with "nodes" (representing accounts) and "edges" (representing transactions).
3.  **The Basics:**
    * Your customer's account will be highlighted.
    * The beneficiary's account will be the direct connection.
    * The GNN expands the view to show who else has paid the beneficiary, and where the beneficiary sends money.

**11.2 Identifying Mule Account Characteristics**
Your goal is to determine if the beneficiary account is acting as a money mule. Look for these classic patterns:

* **The "Collector" (or "Smurf") Pattern:**
    * **Description:** The beneficiary node receives multiple small- to medium-sized payments from a large number of other accounts that do not appear to be related to each other.
    * **Implication:** This is a classic technique used by criminals to collect stolen funds from many different victims into a single staging account.
* **The "Disperser" (or "Flying Kite") Pattern:**
    * **Description:** Shortly after receiving funds, the beneficiary node immediately sends the money out in a series of smaller payments to many other accounts, often in high-risk jurisdictions.
    * **Implication:** This is a layering technique used to rapidly launder the money and make it difficult to trace.
* **Rapid Pass-Through:**
    * **Description:** Money comes into the beneficiary account and leaves almost immediately, with the account balance rarely staying high for long.
    * **Implication:** The account has no legitimate economic purpose; it is being used solely as a temporary transit point for illicit funds.

**11.3 Tracing Fund Flows Across the Network**
Use the interactive features of the tool to explore the network:
* Click on a secondary node to expand the graph and see where the money flows next.
* Use filters to highlight transactions above a certain value or within a specific timeframe.

A high GNN mule confidence score, combined with a visual confirmation of these patterns, is extremely strong evidence that the transaction is part of a larger criminal operation.

---

### **Part 4: Fraud Typology Playbooks (User Cases & Edge Cases)**

---

This section provides specific, step-by-step playbooks for investigating the most common APP fraud typologies and complex edge cases.

#### **12.0 Playbook: Bank Impersonation & "Safe Account" Scams**

This is the most urgent and dangerous scam type, often involving the victim's life savings.

**12.1 Key Indicators**
* **Primary:** `active_call_flag: true`
* **Secondary:**
    * Extreme behavioral duress signals (panicked, hesitant interaction).
    * Transaction is for >95% of the account balance ("account consolidation").
    * High risk score (typically 95+).
    * Victim may be trying to pay a "safe account" with a name similar to their own.

**12.2 Step-by-Step Investigation**
1.  **Claim the alert immediately.** This is a Priority 1, Code Red event.
2.  **Confirm the `active_call_flag`** in the behavioral widget. This is your anchor point.
3.  **Observe the account consolidation pattern.** The intent is to empty the account.
4.  **Note the extreme duress signals.** This corroborates the coaching hypothesis.
5.  There is no need for a deep investigation into the payee. The combination of these factors is sufficient evidence of a live attack.

**12.3 SOP for Action: The "Block, Lock, Escalate" Protocol**
1.  **BLOCK:** Ensure the transaction has been blocked by the Triage Agent. If not, block it manually.
2.  **LOCK:** Immediately place a temporary suspension on the customer's online banking access to prevent the fraudster from coaching them into making further attempts.
3.  **ESCALATE:** Disposition the case as **"Confirm Fraud"** and add a case note: "Live Bank Impersonation Scam. Block/Lock/Escalate protocol initiated. Awaiting welfare check."

**12.4 Customer Contact Script (Welfare Check - Post-Incident)**
*This call is only to be made **after** the account is secured.*

> "Hello, may I please speak with [Customer Name]? My name is [Analyst Name], and I am calling from the Security and Fraud Department at [Your Bank Name].
>
> "The reason for my call is that our security system detected a highly unusual transaction attempt on your account a few minutes ago, along with some signals that suggested you may have been on the phone and under significant pressure at the time. To protect you, we immediately blocked the payment and placed a temporary hold on your online access.
>
> "Are you safe to speak freely right now?
>
> "I want to assure you that your funds are secure. It appears you may have been the target of a sophisticated impersonation scam, where criminals pretend to be from the bank to scare you into moving your money. Can you tell me what happened from your perspective?"

#### **13.0 Playbook: Invoice Redirection & Business Email Compromise (BEC)**

**13.1 Key Indicators**
* **Primary:** `first_payment_to_new_account` for a payee name that matches a known, trusted supplier.
* **Secondary:**
    * Beneficiary account is very new (`payee_account_age_low`).
    * The payment may be for an amount that is consistent with previous legitimate invoices.
    * There are typically no duress signals, as the victim believes the payment is legitimate.

**13.2 Step-by-Step Investigation**
1.  **Claim the alert.** This is typically a Priority 2 case.
2.  **Validate the XAI codes.** Confirm that the payee name is a known relationship but the account number is new.
3.  **Scrutinize the payee account age.** A creation date within the last few days is a major red flag.
4.  **Review the customer's payment history.** Find the previous, legitimate payments to this supplier and note the old, correct account details.

**13.3 SOP for Action: The "Challenge & Contact" Protocol**
1.  Confirm the transaction has been held by the system.
2.  Do not disposition the case yet. The next step is customer contact.
3.  **Crucially, do not rely on email.** The fraudster likely controls the victim's email account. You must make phone contact.

**13.4 Customer Contact Script**
> "Hello, may I please speak with [Customer Name]? My name is [Analyst Name], and I'm calling from the Security Department at [Your Bank Name].
>
> "I'm calling about a payment you initiated today to [Supplier Name] for [Amount]. Our system flagged this because the destination account number is new and doesn't match the one you have used for them in the past.
>
> "Before we proceed, we need to verify this change. How did you receive the new bank details? Was it via email?
>
> "We strongly recommend that you verbally confirm these new bank details with a known contact at [Supplier Name] using a trusted phone number you have on file for them, not a number from the recent email or invoice. Can you please do that and call us back to confirm?"

#### **14.0 Playbook: Investment & Cryptocurrency Scams**

**14.1 Key Indicators**
* **Primary:** Payment is directed to a known high-risk merchant category (e.g., a crypto exchange) or a payee flagged by threat intelligence.
* **Secondary:**
    * Transaction amount is a significant outlier for the customer.
    * May have duress signals or an `active_call_flag` if the victim is being coached.
    * Often involves international transfers to high-risk jurisdictions.

**14.2 Step-by-Step Investigation**
1.  **Assess Urgency:** If an `active_call_flag` is present, treat this as a Priority 1 case and refer to the Bank Impersonation playbook.
2.  **Analyze the Payee:** Review threat intelligence on the crypto exchange or beneficiary. Are they known for facilitating scam transactions?
3.  **Review Transaction History:** Does the customer have any history of making these types of investments? For a first-time "investor," the risk is much higher.
4.  **Review Dialogue Agent Logs:** Check if the Dialogue Agent already intervened. The customer's response (or lack thereof) provides important context.

**14.3 SOP for Action**
1.  **If Coaching is Evident:** Follow the "Block, Lock, Escalate" protocol.
2.  **If No Coaching is Evident:** The transaction should be held. Initiate customer contact using a script focused on investor protection and due diligence.
3.  **Disposition:** Based on the customer conversation, disposition as "Confirm Fraud" or "False Positive."

#### **15.0 Playbook: Romance Scams (Long-Term Grooming Attacks)**

**15.1 Key Indicators**
* **Primary:** A large payment amount that is a significant outlier, following a preceding pattern of small, regular payments to the same payee.
* **Secondary:**
    * The GNN visualization shows the payee is a "collector" node receiving similar patterns from other individuals.
    * The payee is often in a high-risk jurisdiction.
    * Duress signals are usually absent, as the victim is a willing participant.

**15.2 Step-by-Step Investigation**
1.  **Focus on the Pattern:** The key is the shift from small, regular payments to a sudden large one for an "emergency."
2.  **Leverage the GNN:** The network analysis is your strongest tool here. A legitimate partner is unlikely to be receiving funds from dozens of other unrelated "partners."
3.  **Acknowledge the Emotional Context:** This is a crime of emotional manipulation. A simple block will be met with resistance. The goal of the intervention is education and support.

**15.3 SOP for Action: The "Sensitive Contact" Protocol**
1.  Ensure the payment is held.
2.  This case requires careful and empathetic customer contact. Your goal is not to prove the victim "wrong" but to provide them with information and a safe way out.

**15.4 Customer Contact Script (Supportive & Educational)**
> "Hello, may I please speak with [Customer Name]? My name is [Analyst Name], and I am calling from the Security and Fraud Department at [Your Bank Name].
>
> "I'm calling about a payment you scheduled today to [Payee Name] for [Amount]. The payment has been placed on a temporary hold by our security system, and I wanted to talk through it with you.
>
> "Our system noted that this payment is for a much larger amount than you have typically sent in the past. We also see that the pattern of payments is similar to sophisticated scams we see where fraudsters build trust over a long period before faking an emergency to ask for a large sum of money.
>
> "We have a fraud awareness team that specializes in helping customers in these situations, and they've put together some resources on the signs of these scams. Would you be open to me sharing a link to that information with you? We are here to help you, and our primary goal is to ensure you and your money are safe."

#### **16.0 Playbook: Handling Complex Edge Cases**

**16.1 The "Coerced but Compliant" Victim**
* **Scenario:** All duress signals are present (`active_call_flag`, behavioral anomalies), but the victim is being coached to approve any challenges from the bank.
* **SOP:** **Trust the objective data over the coerced user input.** The non-repudiable signals of duress are stronger evidence than the customer's response. If high-confidence duress signals are present, follow the "Block, Lock, Escalate" protocol regardless of what the customer says. Your case notes must clearly state that the action was taken based on the overwhelming contextual evidence of coaching.

**16.2 The "Low and Slow" Onboarding Attack**
* **Scenario:** A fraudster compromises an account and spends weeks "warming up" a mule account with small, legitimate-looking payments before attempting a large transfer.
* **SOP:** **The GNN is the primary defense.** A traditional review will miss this. The GNN will detect that the "warmed-up" payee account is part of a larger mule network. When you see a high GNN score, expand the network visualization to confirm the "collector" or "disperser" pattern. Base your "Confirm Fraud" decision on the network evidence.

**16.3 The Insider Threat**
* **Scenario:** An employee with access to the Co-pilot UI attempts to override a high-risk block to push a fraudulent payment through.
* **SOP:** The Aegis platform has a **Zero Trust** architecture. Any high-risk override action requires secondary authorization from a Team Leader. The system will also generate an autonomous alert to the Security Operations Center (SOC) if the employee's behavior is anomalous (e.g., logging in from an unusual IP, accessing the system outside of work hours). If you receive a secondary authorization request, you must conduct a full, independent review of the case before approving.

---

### **Part 5: Disposition, Reporting, and Continuous Improvement**

---

#### **17.0 SOP: Case Disposition and Action**

Every alert must end with a final disposition. This action closes the case and feeds crucial data back into the AI models.

**17.1 Confirming Fraud**
1.  **Action:** Select the **"Confirm Fraud"** button in the disposition panel.
2.  **Implication:** This confirms that the alert was a true positive. The transaction is permanently declined.
3.  **Next Step:** You will be prompted to proceed to the SAR filing stage.
4.  **Case Notes:** Your case notes should be a concise summary of the key evidence that led to your conclusion (e.g., "Confirmed Bank Impersonation Scam due to active call flag, account consolidation pattern, and extreme behavioral duress signals.").

**17.2 Dismissing as a False Positive**
1.  **Action:** Select the **"False Positive"** button.
2.  **Implication:** This confirms that the transaction was legitimate and the AI was incorrect. The transaction hold is released.
3.  **CRITICAL - The Human Feedback Loop:** Dismissing a case is one of the most important inputs for model retraining. You **must** leave a detailed case note that justifies your decision and explains the AI's error.
    * **Poor Note:** "Customer said it was fine."
    * **Excellent Note:** "Dismissed as FP. The XAI code `transaction_outlier_amount` was triggered by a legitimate, documented deposit for a house purchase. The AI did not have context on the source of funds. The payee was a verified solicitor."

#### **18.0 SOP: Regulatory Reporting (SAR Filing)**

For all "Confirm Fraud" cases, a Suspicious Activity Report (SAR) must be filed.

**18.1 Reviewing the AI-Generated SAR**
1.  After confirming fraud, the system will automatically present a pre-populated SAR form.
2.  The **Reporting Agent** will have filled in all the known details: customer information, transaction specifics, and, most importantly, a draft narrative.
3.  The narrative is generated based on the case evidence and your disposition notes.

**18.2 Your Responsibility: Verify and Edit**
1.  **You are the final author of the SAR.** It is your professional responsibility to read the entire report and verify its accuracy.
2.  **Edit the Narrative:** While the AI's summary is a powerful starting point, you must review and edit it to ensure it is clear, concise, and 100% factually correct. Add any additional context you gained from customer contact.
3.  **Submit:** Once you are satisfied with the report, click "Submit." The system will file the SAR via its regulatory gateway and attach the submission receipt to the case file for audit purposes.

#### **19.0 The Analyst's Role in Continuous Improvement**

Aegis is a learning system, and the analyst is its most important teacher.

**19.1 The Human Feedback Loop**
Your dispositions and, most importantly, the quality of your case notes are fed directly back into the MLOps pipeline.
* **Confirmed Fraud cases** reinforce the patterns the AI correctly identified.
* **False Positive cases with detailed notes** teach the AI the nuances of legitimate activity, directly reducing future false alarms and improving the customer experience.

Take pride in the quality of your case notes. They are a direct contribution to the intelligence and accuracy of the platform.

**19.2 Escalating New Fraud Patterns**
Fraudsters constantly evolve. If you encounter a case that does not fit any of the established playbooks or exhibits a novel technique:
1.  Disposition the case based on your best judgment.
2.  Use the "Escalate for Review" flag in the Co-pilot UI.
3.  In your case notes, prefix the note with **"NEW PATTERN:"** and describe in detail what you observed.
4.  This will automatically flag the case for the Fraud Strategy & Analytics team, who will analyze the new typology and potentially create a new playbook and update the AI's Knowledge Base.

#### **20.0 Appendix**

**20.1 Glossary of Terms**
* **Aegis:** The multi-agent AI platform for detecting and preventing APP fraud.
* **Analyst Co-pilot UI:** The primary user interface for managing and investigating Aegis alerts.
* **Disposition:** The final outcome of an investigation as determined by the analyst.
* **Duress Signals:** Behavioral or contextual indicators suggesting a customer is being coerced.
* **GNN (Graph Neural Network):** A machine learning model that analyzes relationships between accounts.
* **XAI (Explainable AI) Reason Codes:** Human-readable factors that contributed to the Risk Score.

**20.2 Escalation Contacts**
* **Team Leader:** [Contact Information]
* **Fraud Strategy & Analytics:** [Contact Information]
* **Security Operations Center (SOC) - for Insider Threats:** [Contact Information]

