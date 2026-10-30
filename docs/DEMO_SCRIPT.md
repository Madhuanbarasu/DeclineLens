# Demo Script (about 3 minutes)

**0:00 Hook.** "Every lender declines people. Almost none can tell them why, or what to change. DeclineLens does both, for every applicant, inside the database."

**0:20 Run it.** `python -m declinelens --backend exasol run --rows 200000`. Point at the recourse stage: "That one statement just re-scored every declined applicant under about 200 what-if plans: millions of scenarios."

**1:00 One person.** Dashboard, tab "Explain a decision". Show a declined applicant: top reasons, then the options ranked by effort, then the letter. "Reasons plus a tested path to yes."

**1:50 The fairness angle.** Tab "Fairness audit". "Gender is not a model input and the gap is small. But applicants under 30 fall below the four-fifths screen and are almost twice as likely to have no path to approval. Auditing recourse, not just approvals, shows it."

**2:30 Proof.** `pytest -q tests`. "SQL scores match an independent Python version, and a brute-force search confirms the plan the database picks really is the cheapest."

**2:50 Close.** "Open source, MIT, all SQL, reproducible in minutes."
