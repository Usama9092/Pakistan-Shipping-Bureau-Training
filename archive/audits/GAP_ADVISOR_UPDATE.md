# Gap Advisor — State-of-the-Art Update

Gap Advisor is now an explainable decision-support layer. It reads authoritative evidence from Training, Training Matrix/records, Development Plans, CPD, Practical/Witness and Competency readiness, then recommends the corrective action in the owning module.

It does not create duplicate training, development, witness, competency, or authorization records. Accepted recommendations are tracked in `gap_advisor_actions` and routed to the authoritative module.

Features: evidence-gap explanation, priority, target module, due date, duplicate recommendation prevention, accepted/in-progress/completed tracking, evidence-source summary, audit events, and scoped access.
