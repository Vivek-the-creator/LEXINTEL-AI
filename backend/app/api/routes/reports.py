"""
Reports API

POST   /api/reports/             — save a report from a case
GET    /api/reports/             — list user's saved reports
GET    /api/reports/{id}         — get a single report
DELETE /api/reports/{id}         — delete a report
GET    /api/reports/{id}/pdf     — download report as PDF
GET    /api/cases/{case_id}/export/pdf  — export case report as PDF (also registered here)
"""
import io
from datetime import datetime, timezone
from typing import Optional, List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.ai.logging.logger import AILogger

router = APIRouter()
logger = AILogger("api.reports")


# ── Schemas ───────────────────────────────────────────────────────────────────

class SaveReportRequest(BaseModel):
    case_id: str
    case_name: str
    report_data: dict = Field(default_factory=dict)
    outcome_prediction: Optional[dict] = None
    legal_strategy: Optional[dict] = None
    legal_drafts: List[dict] = Field(default_factory=list)
    document_intelligence: Optional[dict] = None
    legal_research: Optional[dict] = None
    similar_cases: List[dict] = Field(default_factory=list)
    evidence_analysis: Optional[dict] = None
    evidence_timeline: List[dict] = Field(default_factory=list)
    missing_evidence_hints: List[str] = Field(default_factory=list)


# ── PDF builder (pure Python, no external deps) ───────────────────────────────

def _build_pdf_bytes(case_name: str, report: dict, prediction: dict, strategy: dict) -> bytes:
    """
    Build a PDF report using reportlab if available, else fall back to plain text PDF.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle("title", parent=styles["Title"],
                                     fontSize=18, spaceAfter=6, textColor=colors.HexColor("#1e40af"))
        h2_style = ParagraphStyle("h2", parent=styles["Heading2"],
                                  fontSize=13, spaceBefore=14, spaceAfter=4,
                                  textColor=colors.HexColor("#1e3a8a"))
        body_style = ParagraphStyle("body", parent=styles["Normal"],
                                    fontSize=10, leading=15, spaceAfter=4)
        disclaimer_style = ParagraphStyle("disc", parent=styles["Normal"],
                                          fontSize=8, textColor=colors.HexColor("#b45309"),
                                          backColor=colors.HexColor("#fffbeb"),
                                          borderPadding=6, spaceAfter=10)
        bullet_style = ParagraphStyle("bullet", parent=styles["Normal"],
                                      fontSize=10, leading=14, leftIndent=14, spaceAfter=2)

        def h2(text): story.append(Paragraph(text, h2_style))
        def body(text): story.append(Paragraph(str(text), body_style))
        def bullet(text): story.append(Paragraph(f"• {text}", bullet_style))
        def space(): story.append(Spacer(1, 8))
        def hr(): story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))

        # Header
        story.append(Paragraph(f"LexIntel AI — Case Intelligence Report", title_style))
        story.append(Paragraph(f"<b>{case_name}</b>", ParagraphStyle("cn", parent=styles["Normal"],
                                                                       fontSize=14, spaceAfter=4)))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            ParagraphStyle("date", parent=styles["Normal"], fontSize=9, textColor=colors.grey)
        ))
        space()
        story.append(Paragraph(
            "⚠ AI GENERATED REPORT — FOR INFORMATIONAL PURPOSES ONLY. "
            "This report does NOT constitute legal advice. "
            "Consult a qualified lawyer before taking any legal action.",
            disclaimer_style
        ))
        hr()

        # Executive Summary
        exec_summary = report.get("executive_summary", "")
        if exec_summary:
            h2("Executive Summary")
            body(exec_summary)
            space()

        # Outcome Prediction
        if prediction:
            h2("Outcome Prediction")
            prob = prediction.get("probability_of_success", "N/A")
            strength = prediction.get("case_strength_score", "N/A")
            confidence = prediction.get("confidence_level", "N/A")
            risk = prediction.get("risk_level", "N/A")
            data = [
                ["Probability of Success", str(prob)],
                ["Case Strength Score", str(strength)],
                ["Confidence Level", str(confidence)],
                ["Risk Level", str(risk)],
            ]
            t = Table(data, colWidths=[8*cm, 8*cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eff6ff")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bfdbfe")),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            space()

            for label, key in [("Key Strengths", "key_strengths"), ("Key Weaknesses", "key_weaknesses")]:
                items = prediction.get(key) or []
                if items:
                    h2(label)
                    for item in items:
                        bullet(item)
                    space()

            disclaimer_pred = prediction.get("disclaimer", "")
            if disclaimer_pred:
                story.append(Paragraph(disclaimer_pred, disclaimer_style))

        # Strategy
        if strategy:
            strategies = strategy.get("strategies") or []
            if strategies:
                h2("Recommended Legal Strategies")
                for s in strategies[:4]:
                    story.append(Paragraph(f"<b>{s.get('name', '')}</b>", body_style))
                    body(s.get("description", ""))
                    effort = s.get("effort", "")
                    risk_s = s.get("risk_level", "")
                    timeline = s.get("estimated_timeline", "")
                    body(f"Effort: {effort} | Risk: {risk_s} | Timeline: {timeline}")
                    pros = s.get("pros") or []
                    cons = s.get("cons") or []
                    if pros:
                        body("Pros:")
                        for p in pros: bullet(p)
                    if cons:
                        body("Cons:")
                        for c in cons: bullet(c)
                    space()

            steps = strategy.get("immediate_next_steps") or []
            if steps:
                h2("Immediate Next Steps")
                for i, step in enumerate(steps, 1):
                    bullet(f"{i}. {step}")
                space()

            deadlines = strategy.get("important_deadlines") or []
            if deadlines:
                h2("Important Deadlines")
                for d in deadlines: bullet(d)
                space()

        # Applicable Laws
        laws_summary = report.get("applicable_laws_summary") or []
        if laws_summary:
            h2("Applicable Laws")
            for law in laws_summary:
                bullet(f"{law.get('act', '')}: {law.get('relevance', '')}")
            space()

        # Similar Judgments
        similar = report.get("similar_judgments_summary") or []
        if similar:
            h2("Similar Judgments")
            for j in similar:
                bullet(f"{j.get('case', '')}: {j.get('influence', '')}")
            space()

        # Recommendations
        recs = report.get("recommendations") or []
        if recs:
            h2("Recommendations")
            for i, r in enumerate(recs, 1):
                bullet(f"{i}. {r}")
            space()

        # Legal Risks
        risks = report.get("legal_risks") or []
        if risks:
            h2("Legal Risks")
            for r in risks: bullet(r)
            space()

        # Explainability
        explain = report.get("explainability") or []
        if explain:
            h2("AI Explainability")
            for item in explain[:3]:
                story.append(Paragraph(f"<b>Conclusion:</b> {item.get('conclusion', '')}", body_style))
                body(f"Reasoning: {item.get('reasoning_chain', '')}")
                refs = item.get("legal_references") or []
                if refs: body(f"Legal References: {', '.join(refs)}")
                conf = item.get("confidence_score")
                if conf: body(f"Confidence: {round(float(conf)*100)}%")
                space()

        # Footer disclaimer
        hr()
        story.append(Paragraph(
            "This report was generated by LexIntel AI. It is NOT legal advice. "
            "All AI predictions are probabilistic estimates. "
            "Always consult a qualified lawyer before taking legal action.",
            disclaimer_style
        ))

        doc.build(story)
        return buf.getvalue()

    except ImportError:
        # Fallback: minimal valid PDF as plain text wrapped in PDF structure
        return _build_text_pdf(case_name, report, prediction, strategy)


def _build_text_pdf(case_name: str, report: dict, prediction: dict, strategy: dict) -> bytes:
    """Minimal PDF fallback when reportlab is not installed."""
    lines = [
        f"LexIntel AI — Case Intelligence Report",
        f"Case: {case_name}",
        f"Generated: {datetime.now().strftime('%d %B %Y')}",
        "",
        "DISCLAIMER: AI GENERATED — NOT LEGAL ADVICE",
        "=" * 60,
        "",
        "EXECUTIVE SUMMARY",
        report.get("executive_summary", "N/A"),
        "",
        "OUTCOME PREDICTION",
        f"Probability of Success: {(prediction or {}).get('probability_of_success', 'N/A')}",
        f"Case Strength: {(prediction or {}).get('case_strength_score', 'N/A')}",
        f"Confidence: {(prediction or {}).get('confidence_level', 'N/A')}",
        f"Risk Level: {(prediction or {}).get('risk_level', 'N/A')}",
        "",
        "IMMEDIATE NEXT STEPS",
    ]
    for step in ((strategy or {}).get("immediate_next_steps") or []):
        lines.append(f"  - {step}")
    lines += ["", "RECOMMENDATIONS"]
    for rec in (report.get("recommendations") or []):
        lines.append(f"  - {rec}")
    lines += ["", "=" * 60, "Consult a qualified lawyer before taking any legal action."]

    text = "\n".join(lines)
    # Wrap in a minimal valid PDF
    content = text.encode("latin-1", errors="replace")
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842]\n"
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(len(content) + 200).encode() + b" >>\nstream\n"
        b"BT /F1 10 Tf 50 800 Td 12 TL\n"
    )
    for line in lines[:60]:
        safe = line.encode("latin-1", errors="replace").replace(b"(", b"\\(").replace(b")", b"\\)")
        pdf += b"(" + safe + b") Tj T*\n"
    pdf += b"ET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    pdf += b"xref\n0 6\n0000000000 65535 f\ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n"
    return pdf


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", status_code=status.HTTP_201_CREATED)
async def save_report(
    req: SaveReportRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": current_user["id"],
        "case_id": req.case_id,
        "case_name": req.case_name,
        "report_data": req.report_data,
        "outcome_prediction": req.outcome_prediction,
        "legal_strategy": req.legal_strategy,
        "legal_drafts": req.legal_drafts,
        "document_intelligence": req.document_intelligence,
        "legal_research": req.legal_research,
        "similar_cases": req.similar_cases,
        "evidence_analysis": req.evidence_analysis,
        "evidence_timeline": req.evidence_timeline,
        "missing_evidence_hints": req.missing_evidence_hints,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["reports"].insert_one(doc)
    return {"id": str(result.inserted_id), "case_name": req.case_name, "created_at": now.isoformat()}


@router.get("/")
async def list_reports(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db["reports"].find(
        {"user_id": current_user["id"]},
        {"report_data": 0, "legal_drafts": 0}  # exclude heavy fields from list
    ).sort("created_at", -1).limit(50)
    items = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)
    return {"items": items, "total": len(items)}


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        doc = await db["reports"].find_one({"_id": ObjectId(report_id), "user_id": current_user["id"]})
    except Exception:
        raise HTTPException(status_code=404, detail="Report not found")
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    doc["id"] = str(doc.pop("_id"))
    return doc


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        result = await db["reports"].delete_one({"_id": ObjectId(report_id), "user_id": current_user["id"]})
    except Exception:
        raise HTTPException(status_code=404, detail="Report not found")
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"success": True}


@router.get("/{report_id}/pdf")
async def download_report_pdf(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        doc = await db["reports"].find_one({"_id": ObjectId(report_id), "user_id": current_user["id"]})
    except Exception:
        raise HTTPException(status_code=404, detail="Report not found")
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")

    pdf_bytes = _build_pdf_bytes(
        case_name=doc.get("case_name", "Case"),
        report=doc.get("report_data") or {},
        prediction=doc.get("outcome_prediction") or {},
        strategy=doc.get("legal_strategy") or {},
    )
    filename = f"{doc.get('case_name', 'report').replace(' ', '_')}_AI_Report.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
