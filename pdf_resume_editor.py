"""In-place PDF text edits — preserve original layout, fonts, and margins."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None  # type: ignore

_BUILTIN_FONT_MAP = {
    "arial": "helv",
    "arialmt": "helv",
    "arial-bold": "hebo",
    "arial-boldmt": "hebo",
    "helvetica": "helv",
    "helvetica-bold": "hebo",
    "times": "times",
    "timesnewroman": "times",
    "timesnewromanpsmt": "times",
    "times-bold": "tibo",
    "calibri": "helv",
    "calibri-bold": "hebo",
    "cambria": "times",
    "georgia": "times",
}

_SUMMARY_HEADERS = (
    "SUMMARY",
    "PROFESSIONAL SUMMARY",
    "PROFILE",
    "EXECUTIVE SUMMARY",
    "CAREER SUMMARY",
)
_SECTION_ANCHORS = (
    "WORK EXPERIENCE",
    "EXPERIENCE",
    "PROFESSIONAL EXPERIENCE",
    "EMPLOYMENT",
)


def _collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _normalize_pdf_text(text: str) -> str:
    """Strip soft hyphens, NBSP, nulls, and weird punctuation before writing."""
    if not text:
        return ""
    t = text.replace("\x00", "")
    t = t.replace("\u00ad", "")  # soft hyphen
    t = t.replace("\xa0", " ")
    t = t.replace("\u037e", ";")  # Greek question mark used as semicolon
    t = t.replace("\u2010", "-").replace("\u2011", "-")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def _search_variants(text: str) -> List[str]:
    """Build search strings for PDF text that may omit bullet markers or line breaks."""
    t = _normalize_pdf_text(text or "")
    if not t:
        return []
    out: List[str] = []
    seen = set()

    def add(v: str) -> None:
        v = v.strip()
        if len(v) < 8:
            return
        key = _collapse_ws(v).lower()
        if key not in seen:
            seen.add(key)
            out.append(v)

    add(t)
    add(_collapse_ws(t))
    core = re.sub(r"^[\s\-–—•*·●]+\s*", "", t)
    add(core)
    add(_collapse_ws(core))
    if len(core) > 48:
        add(core[:48])
        add(core[:64])
        add(_collapse_ws(core[:48]))
        add(_collapse_ws(core[:64]))
    add(core.replace("- ", ""))
    add(_collapse_ws(core.replace("- ", "")))
    for line in re.split(r"[\n\r]+", t):
        line = line.strip()
        if len(line) >= 12:
            add(line)
            add(_collapse_ws(line))
    return out


def _builtin_for_hint(font_hint: str = "", bold: bool = False) -> str:
    """Return a Base-14 font name available in this PyMuPDF build."""
    hint = (font_hint or "").lower().replace(" ", "")
    prefers_times = any(k in hint for k in ("times", "georgia", "cambria", "serif")) or not hint
    if bold:
        return "tibo" if prefers_times else "hebo"
    return "tiro" if prefers_times else "helv"  # tiro == Times-Roman


def _line_style_at_rect(page: "fitz.Page", rect: "fitz.Rect") -> Dict:
    info = {
        "fontname": "times",
        "fontsize": 11.0,
        "color": 0,
        "x0": float(rect.x0),
        "bullet_prefix": "●     ",
        "text_x0": float(rect.x0),
        "font_hint": "TimesNewRomanPSMT",
        "line_height": 12.65,
    }
    try:
        clip = fitz.Rect(max(0, rect.x0 - 40), max(0, rect.y0 - 4), page.rect.width, rect.y1 + 4)
        for block in page.get_text("dict", clip=clip).get("blocks") or []:
            for line in block.get("lines") or []:
                spans = line.get("spans") or []
                if not spans:
                    continue
                line_text = "".join(s.get("text") or "" for s in spans)
                if not line_text.strip():
                    continue
                info["x0"] = float(line["bbox"][0])
                info["line_height"] = max(11.0, float(line["bbox"][3] - line["bbox"][1]))
                bullet_m = re.match(r"^([●•\-\*·]\s*)", line_text.lstrip())
                if bullet_m or re.match(r"^[\s]*[●•]", line_text):
                    # Preserve original bullet + spacing pattern when present
                    m2 = re.match(r"^([●•\-\*·][ \t]*)", line_text.lstrip())
                    if m2:
                        # Google Docs often uses "●     " (bullet + 5 spaces)
                        prefix = m2.group(1)
                        if len(prefix) < 3:
                            prefix = "●     "
                        info["bullet_prefix"] = prefix
                for span in spans:
                    txt = span.get("text") or ""
                    if not txt.strip() or txt.strip() in ("●", "•", "-", "*", "·"):
                        continue
                    info["fontsize"] = float(span.get("size") or 11.0)
                    info["color"] = span.get("color", 0)
                    info["text_x0"] = float(span["bbox"][0])
                    info["font_hint"] = span.get("font") or "TimesNewRomanPSMT"
                    raw = (span.get("font") or "").lower().replace(" ", "")
                    info["fontname"] = _builtin_for_hint(raw, bold="bold" in raw)
                    return info
    except Exception:
        pass
    return info


def _page_lines(page: "fitz.Page") -> List[Tuple[float, "fitz.Rect", str]]:
    y_ordered: List[Tuple[float, "fitz.Rect", str]] = []
    for block in page.get_text("dict").get("blocks") or []:
        for line in block.get("lines") or []:
            spans = line.get("spans") or []
            raw = "".join(s.get("text") or "" for s in spans)
            if not raw.strip():
                continue
            y_ordered.append((float(line["bbox"][1]), fitz.Rect(line["bbox"]), raw))
    y_ordered.sort(key=lambda x: x[0])
    return y_ordered


def _collect_wrapped_line_rects(page: "fitz.Page", start_y: float, max_lines: int = 10) -> List["fitz.Rect"]:
    """Collect consecutive wrapped lines after a bullet until the next bullet or section."""
    rects: List["fitz.Rect"] = []
    started = False
    for y, rect, raw in _page_lines(page):
        if not started:
            if abs(y - start_y) < 3.0:
                started = True
                rects.append(rect)
            continue
        if len(rects) >= max_lines:
            break
        stripped = raw.strip()
        if re.match(r"^[●•\-\*·]\s*\S", stripped):
            break
        if re.match(
            r"^(WORK EXPERIENCE|EXPERIENCE|EDUCATION|SKILLS|SUMMARY|PROJECTS|PROFESSIONAL)\b",
            stripped,
            re.I,
        ):
            break
        if y - rects[-1].y1 > 22:
            break
        rects.append(rect)
    return rects


def _fuzzy_line_rects(page: "fitz.Page", old_text: str) -> List["fitz.Rect"]:
    target = _collapse_ws(re.sub(r"^[\s\-–—•*·●]+\s*", "", old_text or "")).lower()
    if len(target) < 16:
        return []
    target_prefix = target[:48]
    y_ordered = [(y, rect, _collapse_ws(re.sub(r"^[\s\-–—•*·●]+\s*", "", raw)).lower()) for y, rect, raw in _page_lines(page)]
    start_idx = -1
    for i, (_y, _rect, core) in enumerate(y_ordered):
        if len(core) < 8:
            continue
        if core.startswith(target_prefix[:24]) or target_prefix.startswith(core[:24]) or core in target:
            if len(core) >= 16 or (len(core) >= 10 and core in target):
                start_idx = i
                break
    if start_idx < 0:
        return []
    hits: List["fitz.Rect"] = []
    covered = ""
    for i in range(start_idx, min(start_idx + 8, len(y_ordered))):
        _y, rect, core = y_ordered[i]
        hits.append(rect)
        covered = _collapse_ws(covered + " " + core)
        if len(covered) >= min(len(target), 120) and (
            target.startswith(covered[:60]) or covered.startswith(target[:60]) or target in covered or covered in target
        ):
            break
        if i + 1 < len(y_ordered):
            nxt = y_ordered[i + 1][2]
            if len(covered) > 40 and nxt not in target and nxt[:20] not in target:
                break
    return hits


def _redact_full_width_lines(page: "fitz.Page", rects: List["fitz.Rect"], pad: float = 1.5) -> "fitz.Rect":
    """Redact each line full-width so leftover glyphs cannot remain."""
    if not rects:
        return fitz.Rect(0, 0, 0, 0)
    left = 42.0
    right = page.rect.width - 42.0
    union = rects[0]
    for r in rects:
        union |= r
        page.add_redact_annot(
            fitz.Rect(left, r.y0 - pad, right, r.y1 + pad),
            fill=(1, 1, 1),
        )
    # Also cover any tiny leftover spans on the same y-bands
    for y, rect, raw in _page_lines(page):
        if y < union.y0 - 2 or y > union.y1 + 2:
            continue
        if any(abs(y - r.y0) < 2.5 for r in rects):
            page.add_redact_annot(
                fitz.Rect(left, rect.y0 - pad, right, rect.y1 + pad),
                fill=(1, 1, 1),
            )
            union |= rect
    page.apply_redactions()
    return fitz.Rect(left, union.y0 - pad, right, union.y1 + pad)


def _draw_bullet_dot(page: "fitz.Page", x: float, baseline_y: float, fontsize: float) -> None:
    """Draw a filled circle approximating Google Docs ● (built-in fonts lack the glyph)."""
    r = max(1.35, fontsize * 0.18)
    cy = baseline_y - fontsize * 0.32
    shape = page.new_shape()
    shape.draw_circle((x + r, cy), r)
    shape.finish(color=(0, 0, 0), fill=(0, 0, 0), width=0)
    shape.commit()


def _write_wrapped_bullet(
    page: "fitz.Page",
    rect: "fitz.Rect",
    text: str,
    style: Dict,
) -> None:
    """Write a bullet into cleared footprint using Times-Roman + drawn bullet dot."""
    fontsize = float(style.get("fontsize") or 11.0)
    core = re.sub(r"^[\s•\-\*●·]+\s*", "", _normalize_pdf_text(text))
    # Indent body to leave room for drawn bullet (matches ~● + spaces)
    display = f"      {core}"
    left = 45.3
    right = page.rect.width - 45.0
    line_h = float(style.get("line_height") or (fontsize * 1.15))
    approx_chars = max(1, int((right - left) / (fontsize * 0.48)))
    est_lines = max(1, (len(display) // approx_chars) + 1)
    write_rect = fitz.Rect(left, rect.y0, right, max(rect.y1, rect.y0 + line_h * est_lines + 2))
    if write_rect.y1 > page.rect.height - 36:
        write_rect.y1 = page.rect.height - 36

    fontname = _builtin_for_hint(style.get("font_hint") or "times", bold=False)
    wrote = False
    for fname in (fontname, "tiro", "Times-Roman", "helv"):
        try:
            rc = page.insert_textbox(
                write_rect,
                display,
                fontsize=fontsize,
                fontname=fname,
                color=(0, 0, 0),
                align=fitz.TEXT_ALIGN_LEFT,
            )
            if rc >= 0:
                wrote = True
                break
            write_rect.y1 = min(page.rect.height - 36, write_rect.y0 + line_h * (est_lines + 2))
            rc2 = page.insert_textbox(
                write_rect,
                display,
                fontsize=max(9.0, fontsize - 0.25),
                fontname=fname,
                color=(0, 0, 0),
                align=fitz.TEXT_ALIGN_LEFT,
            )
            if rc2 >= 0:
                wrote = True
                break
        except Exception:
            continue

    if wrote:
        _draw_bullet_dot(page, left + 1.0, write_rect.y0 + fontsize * 0.85, fontsize)


def _replace_on_page(page: "fitz.Page", old_text: str, new_text: str) -> bool:
    old_text = _normalize_pdf_text(old_text)
    new_text = _normalize_pdf_text(new_text)
    if not old_text or not new_text or old_text == new_text:
        return False

    best_variant: Optional[str] = None
    best_rects: List = []
    for variant in _search_variants(old_text):
        rects = page.search_for(variant) or page.search_for(variant, quads=False)
        if rects and (best_variant is None or len(variant) > len(best_variant)):
            best_variant = variant
            best_rects = list(rects)

    if not best_variant or not best_rects:
        best_rects = _fuzzy_line_rects(page, old_text)
        if not best_rects:
            return False

    style = _line_style_at_rect(page, best_rects[0])
    wrapped = _collect_wrapped_line_rects(page, best_rects[0].y0)
    if not wrapped:
        wrapped = list(best_rects)

    # Expand by searching remaining original lines near the hit
    old_lines = [ln for ln in re.split(r"[\n\r]+", old_text) if ln.strip()]
    y_cursor = wrapped[-1].y1 if wrapped else best_rects[0].y1
    for ln in old_lines[1:]:
        core = re.sub(r"^[\s\-–—•*·●]+\s*", "", ln).strip()
        if len(core) < 12:
            continue
        hits = page.search_for(core[:64]) or page.search_for(_collapse_ws(core[:64]))
        nearby = [r for r in hits if abs(r.y0 - y_cursor) < 20]
        if not nearby:
            break
        for r in nearby:
            if all(abs(r.y0 - w.y0) > 1.5 for w in wrapped):
                wrapped.append(r)
            y_cursor = max(y_cursor, r.y1)

    cleared = _redact_full_width_lines(page, wrapped, pad=1.8)
    if cleared.is_empty:
        return False

    write_box = fitz.Rect(cleared.x0, cleared.y0, cleared.x1, cleared.y1)
    # Keep original vertical footprint when possible; extend if new text is longer
    old_h = cleared.height
    style["line_height"] = max(style.get("line_height") or 12.65, old_h / max(1, len(wrapped)))
    _write_wrapped_bullet(page, write_box, new_text, style)
    return True


def _find_header_rect(page: "fitz.Page", labels: Tuple[str, ...]) -> Optional[Tuple[str, "fitz.Rect"]]:
    for label in labels:
        rects = page.search_for(label)
        if rects:
            return label, rects[0]
    return None


def _extract_summary_body_from_text(resume_text: str) -> Optional[str]:
    if not resume_text:
        return None
    m = re.search(
        r"(?ims)^\s*(?:SUMMARY|PROFESSIONAL\s+SUMMARY|PROFILE|EXECUTIVE\s+SUMMARY|CAREER\s+SUMMARY)\s*\n"
        r"(.*?)(?=^\s*(?:WORK\s+EXPERIENCE|EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EMPLOYMENT|SKILLS|EDUCATION|PROJECTS)\s*$)",
        resume_text,
    )
    if not m:
        return None
    body = m.group(1).strip()
    return body or None


def extract_summary_body_for_pdf(original_text: str, final_resume: str) -> Optional[str]:
    """Return SUMMARY body to insert when final resume gained a summary section (no existing summary)."""
    if not final_resume:
        return None
    if re.search(
        r"(?im)^\s*(?:SUMMARY|PROFESSIONAL\s+SUMMARY|PROFILE|EXECUTIVE\s+SUMMARY|CAREER\s+SUMMARY)\b",
        original_text or "",
    ):
        return None
    return _extract_summary_body_from_text(final_resume)


def extract_summary_replacement_for_pdf(original_text: str, final_resume: str) -> Optional[str]:
    """Return new SUMMARY body when original already had a summary that was rewritten."""
    if not final_resume:
        return None
    if not re.search(
        r"(?im)^\s*(?:SUMMARY|PROFESSIONAL\s+SUMMARY|PROFILE|EXECUTIVE\s+SUMMARY|CAREER\s+SUMMARY)\b",
        original_text or "",
    ):
        return None
    new_body = _extract_summary_body_from_text(final_resume)
    old_body = _extract_summary_body_from_text(original_text)
    if not new_body:
        return None
    if old_body and _collapse_ws(old_body) == _collapse_ws(new_body):
        return None
    return new_body


def _split_summary_bullets(body: str) -> List[str]:
    bullets: List[str] = []
    for line in (body or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^[\s•\-\*●·]+\s*\S", stripped):
            bullets.append(re.sub(r"^[\s•\-\*●·]+\s*", "", stripped).strip())
        elif bullets:
            bullets[-1] = f"{bullets[-1]} {stripped}"
        else:
            bullets.append(stripped)
    return [b for b in (_normalize_pdf_text(x) for x in bullets) if b]


def apply_summary_section_replace(pdf_bytes: bytes, summary_body: str) -> Tuple[bytes, Dict]:
    """
    Replace existing SUMMARY body in-place:
    redact everything between SUMMARY header and WORK EXPERIENCE, then rewrite bullets.
    """
    stats: Dict = {"replaced": False, "error": None, "method": "section_redact_rewrite", "bullets": 0}
    if not PYMUPDF_AVAILABLE or not pdf_bytes or not summary_body:
        return pdf_bytes, stats

    bullets = _split_summary_bullets(summary_body)
    if not bullets:
        stats["error"] = "empty summary body"
        return pdf_bytes, stats

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = doc[0]
        header = _find_header_rect(page, _SUMMARY_HEADERS)
        anchor = _find_header_rect(page, _SECTION_ANCHORS)
        if not header or not anchor:
            stats["error"] = "summary or experience header not found"
            return pdf_bytes, stats

        _hlabel, header_rect = header
        _alabel, anchor_rect = anchor
        if anchor_rect.y0 <= header_rect.y1 + 4:
            stats["error"] = "invalid section geometry"
            return pdf_bytes, stats

        # Capture style from first original summary bullet before redacting
        style = {
            "fontname": "times",
            "fontsize": 11.0,
            "bullet_prefix": "●     ",
            "font_hint": "TimesNewRomanPSMT",
            "line_height": 12.65,
        }
        for y, rect, raw in _page_lines(page):
            if y <= header_rect.y1 + 2:
                continue
            if y >= anchor_rect.y0 - 2:
                break
            if re.match(r"^[●•]", raw.strip()):
                style = _line_style_at_rect(page, rect)
                break

        y0 = header_rect.y1 + 2
        y1 = anchor_rect.y0 - 2
        left, right = 42.0, page.rect.width - 42.0
        page.add_redact_annot(fitz.Rect(left, y0, right, y1), fill=(1, 1, 1))
        page.apply_redactions()

        # Rewrite bullets into the cleared band, matching original line height
        line_h = float(style.get("line_height") or 12.65)
        cursor_y = y0 + 2
        fontsize = float(style.get("fontsize") or 11.0)
        for bullet in bullets:
            # Estimate height for this bullet
            display = f"      {re.sub(r'^[\s•\-\*●·]+\s*', '', _normalize_pdf_text(bullet))}"
            approx_chars = max(1, int((right - 45.3) / (fontsize * 0.48)))
            est_lines = max(1, (len(display) // approx_chars) + 1)
            box_h = line_h * est_lines + 2
            if cursor_y + box_h > y1 - 2:
                # Compress slightly rather than overflow into WORK EXPERIENCE
                box_h = max(line_h, y1 - 2 - cursor_y)
            if box_h < fontsize:
                break
            box = fitz.Rect(45.3, cursor_y, right, cursor_y + box_h)
            _write_wrapped_bullet(page, box, bullet, style)
            cursor_y += box_h + 4  # small gap between bullets like original
            stats["bullets"] += 1

        stats["replaced"] = stats["bullets"] > 0
        # #region agent log
        try:
            _dbg = Path(__file__).resolve().parent / ".cursor" / "debug-e8b8c3.log"
            _dbg.parent.mkdir(parents=True, exist_ok=True)
            with open(_dbg, "a", encoding="utf-8") as _f:
                _f.write(
                    json.dumps(
                        {
                            "sessionId": "e8b8c3",
                            "hypothesisId": "PDF-SUM",
                            "location": "pdf_resume_editor.py:apply_summary_section_replace",
                            "message": "summary section replace",
                            "data": {"bullets": stats["bullets"], "y0": y0, "y1": y1},
                            "timestamp": int(__import__("time").time() * 1000),
                        }
                    )
                    + "\n"
                )
        except Exception:
            pass
        # #endregion
        return doc.tobytes(garbage=3, deflate=True), stats
    except Exception as e:
        stats["error"] = str(e)
        return pdf_bytes, stats
    finally:
        doc.close()


def apply_summary_insertion(pdf_bytes: bytes, summary_body: str) -> Tuple[bytes, Dict]:
    """
    Insert SUMMARY above WORK EXPERIENCE while preserving original fonts/layout.
    Used only when the original resume had no summary section.
    """
    stats: Dict = {"inserted": False, "error": None, "method": "show_pdf_page"}
    if not PYMUPDF_AVAILABLE or not pdf_bytes or not summary_body:
        return pdf_bytes, stats

    summary_body = _normalize_pdf_text(summary_body)
    src = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        src_page = src[0]
        anchor = _find_header_rect(src_page, _SECTION_ANCHORS)
        if not anchor:
            stats["error"] = "section anchor not found"
            return pdf_bytes, stats

        _label, anchor_rect = anchor
        y_cut = max(0.0, anchor_rect.y0 - 2.0)
        bullets = _split_summary_bullets(summary_body)
        line_count = max(3, sum(max(1, len(b) // 90 + 1) for b in bullets) + 2)
        dy = min(140.0, max(56.0, line_count * 13.0))

        page_w, page_h = src_page.rect.width, src_page.rect.height
        if y_cut + dy > page_h - 36:
            stats["error"] = "insufficient vertical space for summary"
            return pdf_bytes, stats

        dst = fitz.open()
        try:
            page = dst.new_page(width=page_w, height=page_h)
            header_clip = fitz.Rect(0, 0, page_w, y_cut)
            page.show_pdf_page(header_clip, src, 0, clip=header_clip)
            body_clip = fitz.Rect(0, y_cut, page_w, page_h)
            body_dest = fitz.Rect(0, y_cut + dy, page_w, page_h)
            page.show_pdf_page(body_dest, src, 0, clip=body_clip)

            # Write SUMMARY header + bullets into the gap
            gap = fitz.Rect(45, y_cut + 2, page_w - 45, y_cut + dy - 4)
            try:
                page.insert_text(
                    (gap.x0, gap.y0 + 11),
                    "SUMMARY",
                    fontsize=10.5,
                    fontname="hebo",
                    color=(0, 0, 0),
                )
            except Exception:
                page.insert_text(
                    (gap.x0, gap.y0 + 11),
                    "SUMMARY",
                    fontsize=10.5,
                    fontname="helv",
                    color=(0, 0, 0),
                )
            style = {
                "fontsize": 11.0,
                "bullet_prefix": "●     ",
                "font_hint": "TimesNewRomanPSMT",
                "line_height": 12.65,
            }
            cursor = gap.y0 + 16
            for bullet in bullets:
                box = fitz.Rect(gap.x0, cursor, gap.x1, min(gap.y1, cursor + 40))
                _write_wrapped_bullet(page, box, bullet, style)
                cursor += 28
                if cursor >= gap.y1 - 4:
                    break

            stats["inserted"] = True
            stats["shift_px"] = dy
            return dst.tobytes(garbage=3, deflate=True), stats
        finally:
            dst.close()
    except Exception as e:
        stats["error"] = str(e)
        return pdf_bytes, stats
    finally:
        src.close()


def apply_pdf_text_replacements(
    pdf_bytes: bytes,
    replacements: List[Tuple[str, str]],
) -> Tuple[bytes, Dict]:
    """Apply text replacements on a copy of the original PDF."""
    if not PYMUPDF_AVAILABLE:
        return pdf_bytes, {"error": "PyMuPDF not installed", "applied": 0, "missed": len(replacements)}

    stats = {"applied": 0, "missed": 0, "skipped": 0}
    if not pdf_bytes:
        return pdf_bytes, {**stats, "error": "empty pdf"}

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for old_text, new_text in replacements:
            old_text = _normalize_pdf_text(old_text or "")
            new_text = _normalize_pdf_text(new_text or "")
            if not old_text or not new_text:
                stats["skipped"] += 1
                continue
            if old_text == new_text:
                stats["skipped"] += 1
                continue

            hit = False
            for page in doc:
                if _replace_on_page(page, old_text, new_text):
                    hit = True
                    break
            if hit:
                stats["applied"] += 1
            else:
                stats["missed"] += 1

        return doc.tobytes(garbage=3, deflate=True), stats
    finally:
        doc.close()


def modifications_to_replacements(modifications: List[Dict]) -> List[Tuple[str, str]]:
    """
    Extract (original, new) pairs for experience bullet edits only.
    Summary is handled via apply_summary_section_replace / apply_summary_insertion.
    """
    pairs: List[Tuple[str, str]] = []
    for mod in modifications or []:
        if not isinstance(mod, dict):
            continue
        mtype = mod.get("type")
        # Summary handled as full-section replace to avoid overlap artifacts
        if mtype in ("summary_suggestion", "summary_bullet"):
            continue
        if mtype != "bullet_suggestion":
            continue
        original = _normalize_pdf_text(mod.get("original") or "")
        new = _normalize_pdf_text(mod.get("replaced_with") or mod.get("suggested") or "")
        if mod.get("status") == "skipped":
            continue
        if original and new and original != new:
            pairs.append((original, new))
    return pairs
