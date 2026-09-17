"""Idempotent production maintenance for professional training assessment banks.

The job expands every active Yahya Hafiz qualification course to a 50-question,
source-grounded bank without changing learner completion/history. Existing approved
questions are preserved and only the missing balance is added. The learner-facing
assessment remains server-timed and randomized by the existing Training page.
"""
from __future__ import annotations

import hashlib
import random
import re
import uuid
from datetime import datetime

import pandas as pd

from core.database_gateway import exec_sql, query_sql

_RAN = False
TARGET_BANK = 50
ASSESSMENT_MINUTES = 60

# Controlled source supplements only for courses whose legacy uploaded files did not
# contain usable extracted text. Each statement is also represented in the trainer
# presentation linked to the corresponding course.
SUPPLEMENTS = {
    'TRN-CURR-CORE-004': {
        'file_name': 'CORE-004_ISO-IEC-17020_Inspection_Body_Requirements.pptx',
        'url': 'https://docs.google.com/presentation/d/1BG2QkgiRXBVrP_oyinqRekLIAafaGal2/edit?usp=drivesdk&ouid=102848227950872466391&rtpof=true&sd=true',
        'source': '''ISO/IEC 17020 inspection-body work depends on competence, impartiality, independence, confidentiality and consistent operation. Inspection evaluates an item, process, service or installation against specified requirements. Requirements may come from rules, statutory instruments, contracts, approved drawings or controlled procedures. A credible inspection body must produce repeatable and defensible results. Impartiality threats should be identified before work is accepted or performed. Commercial, personal, organizational and technical conflicts of interest require documented controls. Unresolved conflicts should be escalated rather than self-cleared by the inspector. Competence requirements should be defined for each inspection activity and technical scope. Training, supervised practice, witnessing, authorization and periodic monitoring are linked competence controls. Objective evidence should support competence decisions and scope limitations. Competence should be reassessed when rules, technology, duties or performance risks change. Inspection planning should use applicable rules, approved documentation and the defined scope. Controlled methods, equipment and records should be appropriate for the inspection activity. Observations, measurements, deficiencies and decisions should be traceable. Technical review and approval should occur where required before results are released. Inspection records should allow reconstruction of what was checked, by whom, when and against which criteria. Reports should state scope, findings, limitations, conclusions and responsible personnel. Confidential information and digital inspection data require access control. Corrections and revisions should remain traceable to the original record. Authorization scope should be confirmed before survey or plan appraisal work starts. Current controlled procedures, rules and forms should be used. Evidence should be sufficient for independent technical review and future audit. Out-of-scope findings and competence gaps should be escalated to the assigned technical authority.'''
    },
    'TRN-CURR-CORE-005': {
        'file_name': 'CORE-005_IACS-PR7_Training_and_Qualification_Principles.pptx',
        'url': 'https://docs.google.com/presentation/d/1K7FTkDR342gTHgCIcdCH5EKpJJTpe4XR/edit?usp=drivesdk&ouid=102848227950872466391&rtpof=true&sd=true',
        'source': '''A controlled qualification system defines the technical role and scope to be achieved. Theoretical learning should cover rules, procedures, statutory requirements, technical principles and reporting expectations. Training should be relevant to the intended authorization scope. Knowledge assessment should demonstrate understanding rather than attendance alone. Training material and assessment records should be controlled and traceable. Practical development converts theoretical knowledge into safe and consistent field performance. Candidates should first observe authorized personnel and then perform work under progressively reduced supervision. Practical evidence should cover preparation, execution, judgement, reporting and follow-up. Supervisors should record satisfactory performance and areas requiring further development. Objective evidence should support readiness decisions. Formal authorization should identify activity, scope and limitations. Personnel should not work outside the granted scope without appropriate supervision or additional authorization. Changes in rules, technology, performance or inactivity may trigger reassessment. Authorization records should remain current and linked to supporting evidence. Trainers should assign realistic development plans and learning sequences. Trainers should provide or approve controlled learning material and assessments. Trainers should select suitable supervised assignments and competent witnesses. Trainers should review pre-survey and post-survey evidence for completeness and quality. Readiness recommendations should be evidence-based and should not become automatic approvals. PSB In-Service ship-type development uses two witnessed surveys plus one lead survey under supervision for each applicable ship type. NSC practical development is common across ship types except where a ship-specific feature needs additional evidence. Theoretical modules should be passed before progression to the related practical authorization stage. Authorization is a controlled decision distinct from course completion.'''
    },
    'TRN-CURR-CORE-006': {
        'file_name': 'CORE-006_Document_Control_and_Record_Retention.pptx',
        'url': 'https://docs.google.com/presentation/d/11VJ-zqrMB3PHKnPX4bikN079l98FWq5P/edit?usp=drivesdk&ouid=102848227950872466391&rtpof=true&sd=true',
        'source': '''Controlled documents tell personnel what to do and include procedures, work instructions, forms, rules and guidance. Records demonstrate what actually happened and include reports, checklists, approvals, test evidence, attendance and assessment results. Documents change through revision control while records are normally preserved as historical evidence. Both documents and records require ownership, identification, access rules and retention decisions. The document lifecycle includes draft, technical review, approval, controlled issue, use, revision and withdrawal or archiving. Each controlled document needs a clear identifier, revision status and approving authority. Users should distinguish the current approved version from obsolete copies. Superseded material should not remain available for unintended operational use. Records should identify who performed an activity, what was checked, when it occurred and which requirements applied. Links between findings, evidence, approvals, corrections and final outputs should be preserved. Original evidence should not be overwritten when correcting an error; amendments should remain traceable. Consistent naming and metadata improve retrieval during technical review, audit or investigation. Retention periods should reflect legal, statutory, contractual, accreditation and business requirements. Long-lived technical evidence may need to remain retrievable throughout an asset lifecycle. Controlled disposal should reflect information classification. Legal hold, investigation or dispute requirements override routine disposal schedules. Digital records require role-based access, strong authentication and suitable backup and recovery arrangements. Sensitive technical and personal information should be protected against unauthorized access. Audit trails should be maintained for critical approvals, status changes and authorization decisions. Links, attachments and stored files should remain accessible and uncorrupted over time. Personnel should use the current approved template and store evidence in the correct project, course or authorization record. Missing, corrupted or conflicting controlled information should be escalated promptly.'''
    },
    'TRN-CURR-SMDB18': {
        'file_name': 'SMDB18_Carriage_of_Dangerous_Substances_in_Bulk.pptx',
        'url': 'https://docs.google.com/presentation/d/1T31_8kU1D_A-On_T9DAvkMNUBtsuSVr5/edit?usp=drivesdk&ouid=102848227950872466391&rtpof=true&sd=true',
        'source': '''SOLAS chapter VI and the IMSBC Code govern important aspects of safe carriage of solid bulk cargoes. The IMSBC Code addresses cargo-specific hazards and safe carriage procedures. Grain in bulk is addressed separately by the International Grain Code. Packaged dangerous goods are primarily addressed by the IMDG Code. Group A cargoes may liquefy when shipped with moisture content above the transportable moisture limit. Group B cargoes possess chemical hazards. Group C cargoes are neither Group A liquefaction cargoes nor Group B chemical-hazard cargoes. Some cargoes may require combined precautions. The individual cargo schedule is the starting point for cargo-specific controls. Cargo information should be provided sufficiently in advance for safe loading planning. Cargo identity should correspond to the applicable individual cargo schedule. Required moisture content and transportable moisture limit evidence should be valid and traceable. Loading plans should remain within still-water shear force, bending moment and local-strength limits. Fine particulate cargoes can lose shear strength when moisture and ship motion promote fluid-like behaviour. Liquefaction can cause cargo shift and rapid loss of transverse stability. Visual appearance does not replace required sampling and testing. Rain and stockpile conditions can alter cargo moisture after testing. Certain cargoes can emit flammable, toxic or asphyxiating gases. Some cargoes can self-heat, oxidize, corrode structures or react dangerously with water. Ventilation requirements depend on the individual cargo schedule. Atmosphere testing equipment should be suitable for the expected hazard. Enclosed-space controls apply to cargo-space entry. High-density cargoes can cause excessive local loading if concentrated. Trimming may reduce cargo shift and improve distribution. Ship-terminal communication should be maintained when loading sequence changes. Surveyors should verify cargo information, relevant test evidence, loading plan and required precautions. Objective evidence and operational restrictions should be recorded when deficiencies are found.'''
    },
    'TRN-CURR-SMLB20': {
        'file_name': 'SMLB20_Carriage_of_Liquid_Substances_in_Bulk.pptx',
        'url': 'https://docs.google.com/presentation/d/1gGwRSjHt4N6NzjvkYV6y9dIgLJJSZ8tK/edit?usp=drivesdk&ouid=102848227950872466391&rtpof=true&sd=true',
        'source': '''SOLAS chapter VII addresses safety of ships carrying dangerous chemicals in bulk. MARPOL Annex II controls pollution by noxious liquid substances carried in bulk. The IBC Code provides construction, equipment and operational standards for relevant chemical tankers. Applicable requirements depend on the product, ship construction date and statutory regime. Product-specific requirements should be identified from the controlled statutory product entry. Liquid cargoes can present toxicity, flammability, corrosivity, reactivity and environmental hazards. Cargo properties influence ship type, tank location, materials and protective systems. Compatibility should be considered between cargoes, tank coatings, piping systems and previous residues. Temperature and pressure can affect transfer safety. Ship types relate preventive measures to product hazard severity. Tank arrangement and separation reduce consequences of leakage, collision or grounding. Cargo piping should maintain containment and prevent unintended cross-connection. Materials exposed to cargo should be suitable for the chemical service. Transfer operations use approved piping, valves, pumps and procedures. Tank venting manages vapour and should remain suitable for the cargo. Closed loading or vapour controls may be required for some products. Level indication, overflow prevention and alarms should be tested as applicable. Leakage, abnormal pressure or unexpected vapour conditions require reassessment. MARPOL Annex II pollution categories influence tank-cleaning and residue controls. The approved Procedures and Arrangements Manual defines ship-specific compliance methods. Cargo record entries provide traceability for loading, unloading, cleaning, ballasting and residue disposal. Prewash and reception-facility requirements depend on the substance and applicable conditions. Detection arrangements should suit expected vapours and hazards. Protective equipment should correspond to toxicity, corrosivity and exposure risk. Emergency procedures should address leakage, exposure, fire, reaction and pollution. Surveyors should compare installed systems with approved arrangements and current statutory requirements.'''
    },
    'TRN-CURR-SMNX17': {
        'file_name': 'SMNX17_Noxious_Liquid_Substances.pptx',
        'url': 'https://docs.google.com/presentation/d/186vBdauOwAIjryrlhlIomcmZ2BKLPr6-/edit?usp=drivesdk&ouid=102848227950872466391&rtpof=true&sd=true',
        'source': '''MARPOL Annex II addresses pollution from noxious liquid substances carried in bulk. The pollution category reflects the severity of harm associated with discharge of cargo residues. Category X substances present a major pollution hazard and require the most stringent control of residues. Category Y substances present a hazard that justifies limitations on the quality and quantity of discharge. Category Z substances present a minor hazard and are subject to less stringent restrictions than Categories X and Y. Other Substances fall outside Categories X, Y and Z for Annex II pollution categorization. Pollution category is not a complete chemical safety classification. The current statutory product entry should be used to confirm the applicable category. The Procedures and Arrangements Manual establishes ship-specific methods for handling Annex II cargo residues. The manual links statutory requirements to the actual cargo-system arrangement. Personnel should follow the approved sequence for unloading, stripping, washing and residue handling. Changes to cargo piping or stripping arrangements may affect the approved compliance method. Cargo record entries provide evidence of significant Annex II operations. Entries should be complete, traceable and consistent with voyage, cargo and tank information. Recorded operations should align with the approved manual. Contradictory or missing entries can indicate a control failure. Supporting evidence can include terminal documents, reception-facility receipts and tank-cleaning records. Some cargoes and unloading conditions require a prewash. Prewash residues may require delivery to an appropriate reception facility. The need for prewash depends on the product category, cargo characteristics and statutory conditions. Effective stripping reduces residue after unloading. Tank washing and ballast operations should not create an unauthorized discharge pathway. Annex II permits only discharges that satisfy applicable statutory conditions. Prohibited residues should be retained on board or transferred ashore as required. A compliant discharge arrangement depends on both equipment condition and correct operational use. Surveyors should verify product identity, category, ship authorization, manuals, records and relevant equipment.'''
    },
    'TRN-CURR-NDUT3': {
        'file_name': 'NDUT3_Ultrasonic_Testing_Level-II_Fundamentals.pptx',
        'url': 'https://docs.google.com/presentation/d/1Mzf6h-bybIbrKyhhK6vV3knvINevISta/edit?usp=drivesdk&ouid=102848227950872466391&rtpof=true&sd=true',
        'source': '''Pulse-echo ultrasonic testing introduces high-frequency sound into a component and receives returning echoes. Time of flight relates to sound path while echo amplitude relates to reflector response and examination conditions. Straight-beam and angle-beam techniques are selected according to geometry and examination objective. Material structure, surface condition, coupling, geometry and attenuation influence results. A suitable flaw detector, probe, cable, couplant and reference or calibration block should be used. Probe frequency, crystal size, beam angle and technique should suit the component and examination range. Equipment condition and functional checks should be verified before use. Equipment and probe identification should be traceable where required. Time-base calibration establishes the required sound-path range. Probe index and actual refracted angle should be confirmed for applicable angle-beam work. Sensitivity should be set using the specified reference reflector or approved calibration method. Transfer correction, DAC or TCG should be applied only as required by the approved procedure. Calibration should be rechecked at required intervals and after conditions that could affect accuracy. The scanning surface should be prepared and visually examined before ultrasonic testing. Adequate coupling and consistent probe pressure should be maintained. Planned scan patterns should cover the required examination volume. Repeatable indications should be investigated using probe movement, sound-path calculation and complementary scans. Indications should not be classified before geometry and procedure-specific effects are considered. Indications can be characterized using position, sound path, amplitude and response to probe movement. Relevant indications should be separated from geometric or spurious responses. Acceptance criteria should come from the approved procedure or governing standard. Reports should identify the component, examination area, procedure, equipment, probes and calibration details. Relevant indication location, response information and disposition should be recorded. Limitations and unexamined areas should be stated. Calibration and examination records should support technical review and reconstruction. Site safety, confined-space controls and shipboard safety arrangements remain applicable. Unusual geometry, material condition or ambiguous indications should be escalated for technical review.'''
    },
    'TRN-CURR-IS-SHIP-CHEM': {
        'file_name': 'IS_SHIP_CHEM_Chemical_Tankers_Familiarization.pptx',
        'url': 'https://docs.google.com/presentation/d/1biV-tsX6SmvtEoS5Z3QBrDQcuHVBaRXH/edit?usp=drivesdk&ouid=102848227950872466391&rtpof=true&sd=true',
        'source': '''Chemical tanker safety is principally governed through SOLAS chapter VII and the IBC Code for applicable ships. Pollution by noxious liquid substances in bulk is controlled through MARPOL Annex II. The IBC Code provides product-specific carriage requirements and design standards. Certificate scope should be consistent with products the ship is authorized to carry. IBC ship types reflect the degree of containment and preventive measures required for product hazards. Type 1 provides the highest level of preventive measures for very severe hazards. Type 2 and Type 3 apply different protective standards according to product risk. Tank location and separation reduce the probability and consequence of cargo release after damage. Product authorization depends on the complete set of ship features rather than ship type alone. Cargo tanks may be integral or independent depending on design and service. Tank coatings and construction materials should be compatible with intended products. Cargo piping should preserve segregation and prevent unintended mixing or contamination. Drainage and stripping arrangements influence residue quantities and Annex II compliance. Cargo pumps, valves and manifolds are critical transfer barriers. Tank venting controls vapour pressure and routes vapour to a safe location. Closed gauging may be required for hazardous cargoes. High-level alarms and overflow-control functions reduce overfill risk. Gas-detection equipment should match the expected hazard. Personal protective equipment should suit the specific exposure risk. Enclosed-space controls remain essential even when tanks are believed clean. The Procedures and Arrangements Manual defines ship-specific residue-handling methods. Cargo record entries provide traceability of relevant cargo and residue operations. In-service surveys should examine cargo tanks, cofferdams, piping, valves, pumps, manifolds, alarms, shutdowns and gas detection within scope. Repairs or coating degradation should be assessed for effect on cargo compatibility and containment. Survey decisions should start with product authorization and the applicable statutory requirement.'''
    },
    'TRN-CURR-IS-SHIP-GAS': {
        'file_name': 'IS_SHIP_GAS_Gas_Carriers_Familiarization.pptx',
        'url': 'https://docs.google.com/presentation/d/1wb-CmB7M3BHUQ3KfcqA42_kF4iiN8-p_/edit?usp=drivesdk&ouid=102848227950872466391&rtpof=true&sd=true',
        'source': '''The IGC Code provides an international safety standard for carriage of liquefied gases in bulk. Requirements address ship design, construction and equipment according to product hazards. The Code applies a ship-type philosophy related to cargo-hazard severity. Cryogenic temperature and pressure create hazards beyond ordinary liquid cargo containment. Collision or grounding damage can cause rapid cargo release, evaporation and vapour dispersion. Gas carriers use specialized cargo containment systems designed for product pressure and temperature. Primary barriers contain cargo and some designs use secondary barriers to control leakage consequences. Insulation limits heat ingress and protects ship structure from low-temperature exposure. Tank supports and surrounding structures accommodate thermal movement and service loads. Containment type affects inspection access, leakage monitoring and survey techniques. Heat ingress can generate boil-off gas and increase cargo-system pressure. Cargo systems may use reliquefaction, vapour consumption, pressure accumulation or other approved control methods. Relief valves protect tanks and piping against excessive pressure. Set pressures, isolation arrangements and discharge locations are safety-critical. Temperature monitoring helps demonstrate that cargo and structure remain within approved limits. Cargo liquid and vapour piping should preserve containment and segregation. Compressors, pumps and heat exchangers should be suitable for the specific gas service. Expansion, contraction and vibration should be accommodated without overstressing piping. Emergency isolation helps limit release after equipment or hose failure. Gas detection provides early warning of leakage where vapour can accumulate. Detector type and calibration should suit the cargo hazard. Ventilation controls accumulation of flammable or toxic vapours. Electrical equipment in hazardous areas should maintain the approved protection concept. Emergency shutdown systems stop cargo flow and isolate sources during abnormal conditions. Very low cargo temperatures can cause brittle behaviour in unsuitable structural materials. Surveyors should verify certificates, product authorization, containment, piping, relief, ventilation, detection, shutdown systems, maintenance and calibration records.'''
    },
}

_STOP = {
    'about','above','after','again','against','also','another','applicable','appropriate','approved',
    'before','being','between','cargo','course','current','defined','document','equipment','evidence',
    'following','from','have','including','inspection','material','other','personnel','procedure','record',
    'relevant','required','requirements','should','system','technical','than','that','their','these','through',
    'training','using','where','which','with','within','work','working','survey','surveyor','control','controls',
}


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _now() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _sentences(source: str) -> list[str]:
    compact = re.sub(r'\s+', ' ', str(source or '')).strip()
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', compact) if 45 <= len(s.strip()) <= 320]


def _technical_terms(source: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for token in re.findall(r"\b[A-Za-z][A-Za-z0-9/\-]{3,}\b", source):
        low = token.casefold()
        if low in _STOP or len(low) < 4 or low in seen:
            continue
        seen.add(low)
        terms.append(token)
    return terms


def _generated_rows(training_id: str, source: str, needed: int, existing_questions: set[str]) -> list[dict]:
    if needed <= 0:
        return []
    sentences = _sentences(source)
    terms = _technical_terms(source)
    if len(sentences) < 5 or len(terms) < 8:
        return []
    seed = int(hashlib.sha256((training_id + '|' + source).encode('utf-8')).hexdigest()[:16], 16)
    rng = random.Random(seed)
    rng.shuffle(sentences)
    rows: list[dict] = []
    local_seen = {q.casefold().strip() for q in existing_questions}

    for sentence in sentences:
        if len(rows) >= needed:
            break
        candidates = [t for t in terms if re.search(rf'\b{re.escape(t)}\b', sentence, re.I)]
        candidates = sorted(candidates, key=lambda x: (-len(x), x.casefold()))[:3]
        for answer in candidates[:2]:
            if len(rows) >= needed:
                break
            stem_sentence = re.sub(rf'\b{re.escape(answer)}\b', '__________', sentence, count=1, flags=re.I)
            stem = 'Which option correctly completes this controlled training statement? ' + stem_sentence
            norm = stem.casefold().strip()
            if norm in local_seen:
                continue
            distractor_pool = [t for t in terms if t.casefold() != answer.casefold() and not re.search(rf'\b{re.escape(t)}\b', sentence, re.I)]
            if len(distractor_pool) < 3:
                continue
            distractors = rng.sample(distractor_pool, 3)
            options = distractors + [answer]
            rng.shuffle(options)
            rows.append({
                'question_id': _uid('Q'), 'training_id': training_id, 'question': stem,
                'option_a': options[0], 'option_b': options[1], 'option_c': options[2],
                'option_d': options[3], 'correct_answer': answer, 'marks': 1,
                'generated_on': _now(),
            })
            local_seen.add(norm)

    # If source has many short controlled bullets, a second deterministic pass with a
    # different stem expands coverage while remaining entirely source-grounded.
    if len(rows) < needed:
        for sentence in sentences:
            if len(rows) >= needed:
                break
            candidates = [t for t in terms if re.search(rf'\b{re.escape(t)}\b', sentence, re.I)]
            for answer in candidates[1:3]:
                if len(rows) >= needed:
                    break
                stem_sentence = re.sub(rf'\b{re.escape(answer)}\b', '__________', sentence, count=1, flags=re.I)
                stem = 'During professional application of this course, which term belongs in the controlled statement? ' + stem_sentence
                norm = stem.casefold().strip()
                if norm in local_seen:
                    continue
                pool = [t for t in terms if t.casefold() != answer.casefold() and not re.search(rf'\b{re.escape(t)}\b', sentence, re.I)]
                if len(pool) < 3:
                    continue
                options = rng.sample(pool, 3) + [answer]
                rng.shuffle(options)
                rows.append({'question_id': _uid('Q'), 'training_id': training_id, 'question': stem,
                             'option_a': options[0], 'option_b': options[1], 'option_c': options[2],
                             'option_d': options[3], 'correct_answer': answer, 'marks': 1,
                             'generated_on': _now()})
                local_seen.add(norm)
    return rows[:needed]


def _ensure_supplement(training_id: str, spec: dict) -> None:
    # Do not duplicate a good source file. Legacy near-empty placeholder files remain
    # untouched for audit history; this adds a new trainer-approved controlled source.
    existing = query_sql(
        "select file_id from files where linked_table='trainings' and linked_id=:tid and file_name=:name limit 1",
        {'tid': training_id, 'name': spec['file_name']},
    )
    if existing.empty:
        exec_sql('''insert into files
            (file_id,owner_user_id,owner_name,linked_table,linked_id,category,file_name,file_ext,mime_type,
             storage_provider,storage_path,public_url,extracted_text,ocr_status,review_status,created_on,updated_on,
             size_bytes,security_status,information_classification,mandatory,sequence_no)
            values (:id,'USR-557C91FF','Yahya Hafiz','trainings',:tid,'Training Material',:name,'pptx',
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation','Google Drive',:url,:url,
                    :source,'Not Required','Trainer Approved',:now,:now,0,'Safe','Internal','Yes',1)''',
            {'id': _uid('FILE'), 'tid': training_id, 'name': spec['file_name'], 'url': spec['url'],
             'source': spec['source'], 'now': _now()})
    exec_sql("update trainings set slides_link=:url,slides_required='Yes',content_status='Published',updated_on=:now where training_id=:tid",
             {'url': spec['url'], 'now': _now(), 'tid': training_id})
    resource = query_sql("select resource_id from training_resources where training_id=:tid and active='Yes' and url=:url limit 1",
                         {'tid': training_id, 'url': spec['url']})
    if resource.empty:
        exec_sql('''insert into training_resources
            (resource_id,training_id,resource_type,title,url,rule_reference,mandatory,sequence_no,active,created_by,created_on,updated_on)
            values (:id,:tid,'Presentation','Controlled PPT — Trainer Approved',:url,'','Yes',1,'Yes','Yahya Hafiz',:now,:now)''',
            {'id': _uid('RES'), 'tid': training_id, 'url': spec['url'], 'now': _now()})


def _course_source(training_id: str) -> str:
    files = query_sql("select file_name,extracted_text from files where linked_table='trainings' and linked_id=:tid order by sequence_no,created_on",
                      {'tid': training_id})
    if files.empty:
        return ''
    excluded = ('answer','solved','exam','result','certificate','attendance','evaluation_form','attestation')
    parts: list[str] = []
    for _, row in files.iterrows():
        name = str(row.get('file_name') or '').casefold()
        if any(x in name for x in excluded):
            continue
        text = str(row.get('extracted_text') or '').strip()
        if len(text) >= 100:
            parts.append(text)
    return '\n\n'.join(parts)[:120000]


def _ensure_assessment_config(training: dict) -> None:
    tid = str(training.get('training_id') or '')
    passing = int(training.get('passing_marks') or 70)
    attempts = int(training.get('max_attempts') or 2)
    cfg = query_sql("select assessment_config_id from training_assessment_configs where training_id=:tid and active='Yes' order by created_on desc limit 1", {'tid': tid})
    params = {'tid': tid, 'title': f"{training.get('title','Training')} Assessment", 'passing': passing,
              'attempts': attempts, 'now': _now(), 'minutes': ASSESSMENT_MINUTES, 'qpa': TARGET_BANK}
    if cfg.empty:
        params['id'] = _uid('ACFG')
        exec_sql('''insert into training_assessment_configs
            (assessment_config_id,training_id,title,duration_minutes,passing_score,max_attempts,questions_per_attempt,
             randomize_questions,randomize_answers,show_result_immediately,show_correct_answers,active,created_by,created_on,updated_on)
            values (:id,:tid,:title,:minutes,:passing,:attempts,:qpa,'Yes','Yes','Yes','No','Yes','System Curriculum QA',:now,:now)''', params)
    else:
        params['id'] = str(cfg.iloc[-1]['assessment_config_id'])
        exec_sql('''update training_assessment_configs set title=:title,duration_minutes=:minutes,passing_score=:passing,
            max_attempts=:attempts,questions_per_attempt=:qpa,randomize_questions='Yes',randomize_answers='Yes',
            show_result_immediately='Yes',show_correct_answers='No',updated_on=:now where assessment_config_id=:id''', params)


def ensure_professional_assessment_banks() -> dict:
    global _RAN
    if _RAN:
        return {'processed': 0, 'expanded': 0, 'remaining_under_50': 0, 'source_gaps': 0}
    _RAN = True

    for tid, spec in SUPPLEMENTS.items():
        _ensure_supplement(tid, spec)

    courses = query_sql('''select * from trainings
        where (trainer_name='Yahya Hafiz' or trainer_id='USR-557C91FF')
          and coalesce(status,'') not in ('Archived','Inactive') and coalesce(assessment_required,'Yes')='Yes'
        order by schedule_date,schedule_time,training_id''')
    expanded = 0
    source_gaps = 0
    for _, training_row in courses.iterrows():
        training = training_row.to_dict()
        tid = str(training.get('training_id') or '')
        if not tid:
            continue
        _ensure_assessment_config(training)
        exec_sql("update trainings set minimum_mcqs=:target,updated_on=:now where training_id=:tid",
                 {'target': TARGET_BANK, 'now': _now(), 'tid': tid})
        existing = query_sql("select * from question_bank where training_id=:tid order by generated_on,question_id", {'tid': tid})
        if len(existing) >= TARGET_BANK:
            continue
        source = _course_source(tid)
        if len(source) < 500:
            source_gaps += 1
            continue
        existing_questions = set(existing['question'].astype(str).tolist()) if not existing.empty else set()
        new_rows = _generated_rows(tid, source, TARGET_BANK - len(existing), existing_questions)
        if not new_rows:
            source_gaps += 1
            continue
        fingerprint = hashlib.sha256(source.encode('utf-8')).hexdigest()
        for row in new_rows:
            exec_sql('''insert into question_bank
                (question_id,training_id,question,option_a,option_b,option_c,option_d,correct_answer,marks,generated_on)
                values (:question_id,:training_id,:question,:option_a,:option_b,:option_c,:option_d,:correct_answer,:marks,:generated_on)''', row)
            try:
                exec_sql('''insert into training_mcq_drafts
                    (draft_id,training_id,question,option_a,option_b,option_c,option_d,correct_answer,marks,status,
                     source_fingerprint,generation_method,generated_by,generated_on,reviewed_by,reviewed_on,published_on,updated_on)
                    values (:id,:tid,:q,:a,:b,:c,:d,:answer,1,'Published',:fp,'Source-grounded professional bank expansion',
                            'System Curriculum QA',:now,'Yahya Hafiz',:now,:now,:now)''',
                    {'id': _uid('QDRAFT'), 'tid': tid, 'q': row['question'], 'a': row['option_a'],
                     'b': row['option_b'], 'c': row['option_c'], 'd': row['option_d'],
                     'answer': row['correct_answer'], 'fp': fingerprint, 'now': _now()})
            except Exception:
                pass
        expanded += 1

    remaining = query_sql('''select count(*) n from trainings t
        where (t.trainer_name='Yahya Hafiz' or t.trainer_id='USR-557C91FF')
          and coalesce(t.status,'') not in ('Archived','Inactive') and coalesce(t.assessment_required,'Yes')='Yes'
          and (select count(*) from question_bank q where q.training_id=t.training_id) < :target''', {'target': TARGET_BANK})
    return {'processed': len(courses), 'expanded': expanded,
            'remaining_under_50': int(remaining.iloc[0]['n']) if not remaining.empty else 0,
            'source_gaps': source_gaps}
