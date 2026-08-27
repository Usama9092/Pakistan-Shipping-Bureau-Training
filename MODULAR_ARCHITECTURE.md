# Modular architecture

`app.py` is now a bootstrap only. Application code is split into `psb_app/common.py` plus domain page modules under `psb_app/pages/` (admin, people, training, competency, authorization, quality, operations, authentication/UI, public verification).

Future development must add new domain logic to these modules rather than expanding the bootstrap.
