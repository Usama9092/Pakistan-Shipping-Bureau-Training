"""Digital PSB certificate rendering based on controlled PSB templates.

The visual layout and wording follow PSB-PTQ20-F03 (Training Course Attestation)
and PSB-PTQ20-F02 (Authorization Certificate). Certificates are generated as
print-ready HTML, carry a verification QR, and are backed by immutable database
records. The left signature block is the PSB Chief Executive Officer; the right
signature block is the assigned Trainer.
"""
from __future__ import annotations

import base64
import html as _html
from pathlib import Path

from psb_app.legacy_runtime import (
    LOGO_PATH,
    STANDARDS,
    VERIFY_PUBLIC_URL,
    clean,
    make_qr_data_uri,
    pd,
    uid,
)

CEO_NAME_ATTESTATION = "Cdre Dr. M Saeed Khalid SI(M)"
CEO_NAME_AUTHORIZATION = "Cdre (R) Dr. M Saeed Khalid"
CEO_TITLE = "Chief Executive Officer"
ATTESTATION_DOCUMENT = "PSB-PTQ20-F03"
AUTHORIZATION_DOCUMENT = "PSB-PTQ20-F02"
INITIAL_ISSUE_DATE = "25-05-2022"
REVISION_NO = "01"
REVISION_DATE = "11-02-2026"

# Transparent vector traces prepared from the signatures supplied by PSB.
# The CEO specimen is always used for the CEO block. The Trainer specimen is
# used only when the recorded Trainer is Yahya Hafiz, so another Trainer's
# certificate can never accidentally carry Yahya Hafiz's handwritten signature.
CEO_SIGNATURE_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1236 1015' preserveAspectRatio='xMidYMid meet'><g fill='#182A8A' fill-rule='evenodd'><path d='M 668 244 L 658 240 L 635 240 L 595 254 L 512 293 L 509 296 L 453 325 L 312 412 L 206 488 L 163 523 L 115 568 L 83 601 L 68 624 L 66 636 L 68 641 L 75 646 L 99 656 L 177 640 L 228 633 L 308 617 L 317 617 L 215 731 L 124 845 L 34 953 L 25 970 L 1 1000 L 0 1009 L 3 1014 L 7 1014 L 12 1010 L 13 1007 L 11 1004 L 30 986 L 48 976 L 53 971 L 57 971 L 74 964 L 82 958 L 84 954 L 82 949 L 59 956 L 52 956 L 51 954 L 214 749 L 317 633 L 338 612 L 382 604 L 440 599 L 483 599 L 530 604 L 570 613 L 613 633 L 624 646 L 629 658 L 629 665 L 626 677 L 612 704 L 597 725 L 577 748 L 521 803 L 485 834 L 446 863 L 400 890 L 369 902 L 361 902 L 356 905 L 342 904 L 340 901 L 337 877 L 333 867 L 329 865 L 324 878 L 326 898 L 332 913 L 337 918 L 351 918 L 386 908 L 414 895 L 460 867 L 498 837 L 532 807 L 572 769 L 603 736 L 622 711 L 634 691 L 640 677 L 643 659 L 639 644 L 632 632 L 612 615 L 593 605 L 579 604 L 525 591 L 490 588 L 426 588 L 389 591 L 356 596 L 352 595 L 361 587 L 365 587 L 405 542 L 429 562 L 451 576 L 460 579 L 465 577 L 465 571 L 459 565 L 428 544 L 416 533 L 417 529 L 464 483 L 522 433 L 589 370 L 638 319 L 661 289 L 671 271 L 674 258 Z'/><path d='M 1125 230 L 1121 227 L 1108 230 L 1064 249 L 1055 251 L 1034 264 L 999 281 L 990 281 L 957 296 L 943 306 L 940 314 L 941 318 L 920 332 L 863 363 L 809 385 L 805 390 L 805 396 L 808 401 L 814 404 L 780 425 L 745 442 L 738 434 L 715 424 L 706 424 L 685 429 L 672 439 L 666 450 L 666 458 L 669 464 L 676 472 L 683 476 L 711 470 L 712 471 L 673 500 L 631 523 L 628 523 L 624 519 L 620 502 L 613 492 L 601 485 L 583 486 L 551 505 L 541 515 L 532 527 L 524 542 L 524 551 L 526 555 L 531 559 L 543 561 L 563 561 L 601 551 L 628 539 L 701 496 L 719 483 L 743 455 L 794 430 L 835 407 L 844 399 L 876 379 L 888 363 L 960 321 L 987 301 L 993 299 L 1027 278 L 1049 267 L 1052 267 L 1065 259 L 1092 247 L 1121 237 L 1125 233 Z'/><path d='M 1142 0 L 1137 8 L 1135 18 L 1136 35 L 1141 58 L 1157 104 L 1176 147 L 1142 161 L 1132 167 L 1121 178 L 1116 187 L 1115 202 L 1118 209 L 1122 213 L 1129 216 L 1139 215 L 1160 201 L 1178 182 L 1187 169 L 1208 201 L 1216 209 L 1228 215 L 1175 246 L 1172 250 L 1173 259 L 1180 260 L 1195 247 L 1233 222 L 1235 217 L 1226 209 L 1216 187 L 1202 168 L 1198 159 L 1199 157 L 1211 159 L 1211 171 L 1216 170 L 1220 166 L 1222 160 L 1217 150 L 1202 145 L 1207 124 L 1206 108 L 1193 65 L 1182 42 L 1168 19 L 1154 4 L 1147 0 Z'/></g></svg>"""

YAHYA_HAFIZ_SIGNATURE_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1026 826' preserveAspectRatio='xMidYMid meet'><g fill='#182A8A' fill-rule='evenodd'><path d='M 238 1 L 231 9 L 225 28 L 225 37 L 182 156 L 143 276 L 119 367 L 119 373 L 115 383 L 109 419 L 105 432 L 103 454 L 91 522 L 90 539 L 88 542 L 85 566 L 73 620 L 69 629 L 68 638 L 57 672 L 55 684 L 51 691 L 43 719 L 11 799 L 0 816 L 2 823 L 5 825 L 10 825 L 18 819 L 32 793 L 39 773 L 43 767 L 78 665 L 96 590 L 98 588 L 100 589 L 104 603 L 108 609 L 119 617 L 128 617 L 140 609 L 159 586 L 188 538 L 209 495 L 228 465 L 232 467 L 247 497 L 270 556 L 276 566 L 286 574 L 294 573 L 300 569 L 309 557 L 319 536 L 327 510 L 333 498 L 348 520 L 355 527 L 367 535 L 381 536 L 395 529 L 406 519 L 418 504 L 438 470 L 454 489 L 470 497 L 482 496 L 492 490 L 499 483 L 500 497 L 493 555 L 491 559 L 489 585 L 486 590 L 469 597 L 467 604 L 471 609 L 481 607 L 485 608 L 480 644 L 472 682 L 468 691 L 468 699 L 472 703 L 482 701 L 486 692 L 497 641 L 503 600 L 507 597 L 543 584 L 570 571 L 571 587 L 569 595 L 567 645 L 572 650 L 576 650 L 582 643 L 583 618 L 590 561 L 625 539 L 652 516 L 654 517 L 649 559 L 649 582 L 651 587 L 657 591 L 663 590 L 669 584 L 683 549 L 688 545 L 698 547 L 742 569 L 764 576 L 781 576 L 791 573 L 801 568 L 816 553 L 817 569 L 814 604 L 812 610 L 804 724 L 803 785 L 805 794 L 811 801 L 822 801 L 836 785 L 842 772 L 848 764 L 864 727 L 882 668 L 886 639 L 885 596 L 877 571 L 864 550 L 851 537 L 838 528 L 838 519 L 840 515 L 838 505 L 841 470 L 928 408 L 930 410 L 934 437 L 943 454 L 954 462 L 961 465 L 966 465 L 987 492 L 998 511 L 1004 530 L 1006 547 L 1006 582 L 1003 600 L 999 609 L 1004 616 L 1010 617 L 1017 611 L 1022 600 L 1025 581 L 1023 532 L 1013 499 L 995 472 L 978 453 L 959 447 L 953 440 L 949 426 L 952 395 L 949 386 L 945 384 L 937 385 L 869 436 L 845 452 L 843 451 L 848 387 L 847 347 L 850 326 L 847 319 L 841 316 L 832 321 L 828 334 L 824 465 L 794 489 L 787 503 L 788 509 L 795 519 L 817 532 L 814 540 L 806 550 L 791 561 L 781 564 L 767 563 L 745 555 L 728 545 L 696 532 L 684 533 L 676 537 L 671 543 L 670 535 L 676 499 L 675 495 L 669 490 L 660 492 L 624 524 L 593 544 L 592 539 L 598 497 L 614 423 L 625 409 L 627 402 L 627 394 L 623 386 L 616 382 L 609 382 L 601 387 L 596 398 L 596 406 L 599 416 L 584 479 L 574 552 L 571 556 L 551 566 L 508 583 L 506 582 L 522 442 L 516 435 L 510 435 L 505 439 L 502 450 L 490 471 L 477 483 L 471 482 L 462 474 L 441 446 L 437 444 L 432 445 L 427 451 L 428 457 L 413 488 L 396 510 L 387 518 L 378 522 L 371 520 L 365 514 L 343 485 L 335 480 L 328 481 L 322 488 L 303 539 L 293 554 L 289 557 L 266 499 L 249 463 L 240 450 L 236 448 L 228 448 L 219 455 L 207 472 L 181 523 L 150 574 L 129 599 L 123 601 L 119 597 L 115 587 L 112 566 L 112 524 L 116 485 L 123 448 L 142 376 L 142 370 L 158 307 L 161 288 L 171 250 L 174 245 L 179 222 L 232 66 L 250 23 L 252 14 L 251 4 L 245 0 Z'/></g></svg>"""


def _e(value) -> str:
    return _html.escape(clean(value), quote=True)


def _logo_data_uri() -> str:
    try:
        p = Path(LOGO_PATH)
        if p.exists():
            encoded = base64.b64encode(p.read_bytes()).decode("ascii")
            return f"data:image/png;base64,{encoded}"
    except Exception:
        pass
    return ""


def _trainer_signature_art(trainer_name: str) -> str:
    normalized = clean(trainer_name).strip().casefold()
    if 'yahya hafiz' in normalized:
        return YAHYA_HAFIZ_SIGNATURE_SVG
    return ""


def _signature_block(name: str, title: str, signature_svg: str) -> str:
    art = f"<div class='signature-art'>{signature_svg}</div>" if signature_svg else "<div class='signature-art signature-placeholder'></div>"
    return f"{art}<div class='signature-rule'></div><div class='signed'>DIGITALLY SIGNED</div><b>{name}</b><br>{title}"


def _template_css() -> str:
    return """
    @page { size: A4 portrait; margin: 0; }
    * { box-sizing: border-box; }
    body { margin: 0; background: #eef1f3; font-family: Arial, Helvetica, sans-serif; color:#111; }
    .sheet { position: relative; width: 210mm; min-height: 297mm; margin: 0 auto; overflow:hidden; background:#fff; padding: 18mm 18mm 24mm; }
    .watermark { position:absolute; inset:0; opacity:.14; z-index:0; overflow:hidden; font:700 12px/18px Arial; color:#667085; word-spacing:8px; letter-spacing:.5px; }
    .watermark span { display:block; transform: rotate(0deg); width:220mm; }
    .band-top-navy { position:absolute; top:0; right:0; width:58%; height:13mm; background:#020735; clip-path:polygon(18% 0,100% 0,100% 100%,38% 100%); z-index:1; }
    .band-top-green { position:absolute; top:0; left:0; width:55%; height:11mm; background:#005c23; clip-path:polygon(0 0,82% 0,100% 100%,0 100%); z-index:1; }
    .band-bottom-navy { position:absolute; left:0; bottom:16mm; width:69%; height:14mm; background:#020735; clip-path:polygon(0 0,82% 0,100% 100%,0 100%); z-index:1; }
    .band-bottom-green { position:absolute; right:0; bottom:16mm; width:42%; height:14mm; background:#005c23; clip-path:polygon(22% 0,100% 0,100% 100%,0 100%); z-index:1; }
    .footer-tag { position:absolute; bottom:4mm; left:50%; transform:translateX(-50%); background:#07123f; color:white; padding:2.4mm 7mm; font-weight:700; font-size:10pt; z-index:3; }
    .meta-left,.meta-right { position:absolute; top:18mm; z-index:3; font-size:9.5pt; line-height:1.35; }
    .meta-left { left:13mm; } .meta-right { right:13mm; text-align:left; }
    .content { position:relative; z-index:2; text-align:center; padding-top:35mm; }
    .logo { width:31mm; max-height:38mm; object-fit:contain; margin-bottom:5mm; }
    .org { color:#06396f; font-size:23pt; font-weight:800; letter-spacing:.5px; margin:0 0 4mm; }
    .title { font-family: Georgia, 'Times New Roman', serif; font-size:36pt; font-weight:700; line-height:1.05; margin:2mm 0 7mm; }
    .lead { font-size:12pt; margin:2mm auto; max-width:165mm; }
    .candidate { display:inline-block; font-size:18pt; font-weight:800; border-bottom:1.5px solid #222; padding:0 7mm 1.5mm; margin:5mm 0 4mm; min-width:115mm; }
    .qualification { font-size:18pt; font-weight:800; margin:4mm auto; max-width:165mm; }
    .module-list { width:168mm; margin:4mm auto 2mm; text-align:left; font-size:9.7pt; line-height:1.35; columns:2; column-gap:10mm; }
    .module-list div { break-inside:avoid; margin-bottom:1.2mm; }
    .signatures { position:absolute; z-index:3; left:16mm; right:16mm; bottom:31mm; display:grid; grid-template-columns:1fr 1fr; gap:30mm; text-align:left; align-items:end; }
    .signature { padding-top:0; font-size:10pt; line-height:1.35; min-height:34mm; }
    .signature.right { text-align:left; }
    .signature-art { width:54mm; height:21mm; display:flex; align-items:flex-end; justify-content:flex-start; overflow:visible; margin-bottom:1mm; }
    .signature-art svg { width:52mm; height:20mm; display:block; overflow:visible; }
    .signature-placeholder { height:21mm; }
    .signature-rule { width:58mm; border-top:1px solid #222; margin:0 0 1.5mm; }
    .signed { color:#0b6b35; font-size:8.2pt; font-weight:700; letter-spacing:.03em; }
    .qr { position:absolute; z-index:3; right:15mm; bottom:3.5mm; display:flex; gap:2mm; align-items:center; font-size:7pt; color:#334155; }
    .qr img { width:15mm; height:15mm; }
    .serial { position:absolute; z-index:3; left:13mm; bottom:5mm; font-size:7.5pt; color:#475467; }
    @media print { body { background:white; } .sheet { margin:0; box-shadow:none; page-break-after:always; } }
    """


def _watermark_html() -> str:
    line = " ".join(["PSB"] * 22)
    return "<div class='watermark'>" + "".join(f"<span>{line}</span>" for _ in range(48)) + "</div>"


def _shell(meta_left: str, meta_right: str, inner: str, cert_id: str, verification_url: str, qr: str) -> str:
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>Pakistan Shipping Bureau Certificate</title>
    <style>{_template_css()}</style></head><body><section class='sheet'>
    {_watermark_html()}<div class='band-top-green'></div><div class='band-top-navy'></div>
    <div class='band-bottom-navy'></div><div class='band-bottom-green'></div>
    <div class='meta-left'>{meta_left}</div><div class='meta-right'>{meta_right}</div>
    {inner}
    <div class='serial'>Digital Certificate ID: {_e(cert_id)}</div>
    <div class='qr'><img src='{qr}' alt='Verification QR'><span>Verify<br>{_e(verification_url)}</span></div>
    <div class='footer-tag'>PAKISTAN SHIPPING BUREAU</div>
    </section></body></html>"""


def build_training_attestation(cert: pd.Series | dict) -> tuple[str, str]:
    cert_id = clean(cert.get('certificate_id')) or uid('ATT')
    verification_url = clean(cert.get('verification_url')) or f'{VERIFY_PUBLIC_URL}/?verify={cert_id}'
    qr = make_qr_data_uri(verification_url)
    logo = _logo_data_uri()
    candidate = _e(cert.get('name'))
    module_code = _e(cert.get('module_code'))
    module_name = _e(cert.get('module_name') or cert.get('training_title'))
    conducted_on = _e(cert.get('conducted_on') or cert.get('completed_on') or cert.get('issue_date'))
    issued_on = _e(cert.get('issue_date'))
    trainer_raw = clean(cert.get('trainer_name') or 'Assigned Trainer')
    trainer = _e(trainer_raw)
    ceo = _e(cert.get('ceo_name') or CEO_NAME_ATTESTATION)
    meta_left = f"Issued at: PSB Head Office<br>Issued on: {issued_on}"
    meta_right = f"Document: {ATTESTATION_DOCUMENT}<br>Initial Issue Date: {INITIAL_ISSUE_DATE}<br>Revision No: {REVISION_NO}<br>Revision Date: {REVISION_DATE}"
    inner = f"""<div class='content'>
      {f"<img class='logo' src='{logo}' alt='PSB Logo'>" if logo else ''}
      <div class='org'>PAKISTAN SHIPPING BUREAU</div>
      <div class='title'>Training Course<br>Attestation</div>
      <div class='lead'>This is to attest that,</div>
      <div class='candidate'>{candidate}</div>
      <div class='lead'>has successfully completed the Theoretical training of</div>
      <div class='qualification'>{module_code}{' – ' if module_code and module_name else ''}{module_name}</div>
      <div class='lead'>Conducted on: <b>{conducted_on}</b></div>
    </div>
    <div class='signatures'>
      <div class='signature'>{_signature_block(ceo, CEO_TITLE, CEO_SIGNATURE_SVG)}</div>
      <div class='signature right'>{_signature_block(trainer, 'Trainer', _trainer_signature_art(trainer_raw))}</div>
    </div>"""
    return _shell(meta_left, meta_right, inner, cert_id, verification_url, qr), qr


def _module_items(auth) -> list[str]:
    raw = auth.get('completed_modules', [])
    if isinstance(raw, (list, tuple)):
        return [clean(x) for x in raw if clean(x)]
    text = clean(raw)
    if not text:
        return []
    return [x.strip(' •-\t') for x in text.replace(';', '\n').splitlines() if x.strip()]


def build_certificate(auth: pd.Series) -> tuple[str, str, str]:
    cert_id = clean(auth.get('certificate_id')) or uid('CERT')
    verification_url = clean(auth.get('verification_url')) or f'{VERIFY_PUBLIC_URL}/?verify={cert_id}'
    qr = make_qr_data_uri(verification_url)
    logo = _logo_data_uri()
    candidate = _e(auth.get('name'))
    qualification = _e(auth.get('trainee_path') or auth.get('scope') or auth.get('job_type'))
    issue_date = _e(auth.get('decision_date') or auth.get('issue_date'))
    modules = _module_items(auth)
    trainer_raw = clean(auth.get('trainer_name') or auth.get('tutor_signature') or 'Assigned Trainer')
    trainer = _e(trainer_raw)
    ceo = _e(auth.get('ceo_name') or CEO_NAME_AUTHORIZATION)
    module_html = ''.join(f"<div>• {_e(m)}</div>" for m in modules) or '<div>• Completed mandatory theoretical and practical modules as per PSB Training Plan.</div>'
    meta_left = f"Issued at: PSB Head Office<br>Issued on: {issue_date}"
    meta_right = f"Document: {AUTHORIZATION_DOCUMENT}<br>Initial Issue Date: {INITIAL_ISSUE_DATE}<br>Revision No: {REVISION_NO}<br>Revision Date: {REVISION_DATE}"
    inner = f"""<div class='content'>
      {f"<img class='logo' src='{logo}' alt='PSB Logo'>" if logo else ''}
      <div class='title'>Authorization<br>Certificate</div>
      <div class='lead'>This is to certify that</div>
      <div class='candidate'>{candidate}</div>
      <div class='lead'>has successfully completed the Theoretical &amp; Practical training of</div>
      <div class='qualification'>{qualification}</div>
      <div class='lead'>Authorization Date: <b>{issue_date}</b></div>
      <div class='lead' style='margin-top:4mm'>Completed Theoretical and Practical modules as per PSB Training Plan are listed below;</div>
      <div class='module-list'>{module_html}</div>
    </div>
    <div class='signatures'>
      <div class='signature'>{_signature_block(ceo, CEO_TITLE, CEO_SIGNATURE_SVG)}</div>
      <div class='signature right'>{_signature_block(trainer, 'Trainer', _trainer_signature_art(trainer_raw))}</div>
    </div>"""
    html = _shell(meta_left, meta_right, inner, cert_id, verification_url, qr)
    return cert_id, html, qr


def record_certificate_history(db_insert, uid, now, actor, certificate_id: str, authorization_id: str, user_id: str, from_status: str, to_status: str, event_type: str, reason: str=''):
    db_insert('authorization_certificate_history', {
        'history_id': uid('CHG'), 'certificate_id': certificate_id, 'authorization_id': authorization_id, 'user_id': user_id,
        'from_status': from_status, 'to_status': to_status, 'event_type': event_type, 'reason': reason,
        'actor_id': str((actor or {}).get('user_id','')), 'actor_name': str((actor or {}).get('name','')), 'event_on': now(), 'metadata': ''
    })
