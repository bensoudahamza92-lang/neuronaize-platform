from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import streamlit as st


def inject_premium_css() -> None:
    """Apply a premium banking visual layer over Streamlit defaults."""

    st.markdown(
        """
        <style>
        :root {
            --navy: #071630;
            --navy-2: #0c2347;
            --blue: #0b8ff0;
            --blue-soft: #dcefff;
            --ink: #172033;
            --muted: #667085;
            --line: #e6edf5;
            --surface: #ffffff;
            --surface-soft: #f6f9fc;
            --success: #0f9f6e;
            --warning: #a65f00;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(11, 143, 240, 0.11), transparent 30rem),
                linear-gradient(180deg, #f7fbff 0%, #eef4f9 42%, #f8fafc 100%);
            color: var(--ink);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #071630 0%, #0c2347 100%);
            color: white;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        [data-testid="stSidebar"] * {
            color: white;
        }

        [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div {
            color: white;
        }

        [data-testid="stHeader"] {
            background: rgba(247, 251, 255, 0.86);
            backdrop-filter: blur(12px);
        }

        .block-container {
            max-width: 1380px;
            padding-top: 1.25rem;
            padding-bottom: 3rem;
        }

        .bank-header {
            display: grid;
            grid-template-columns: minmax(170px, 260px) 1fr minmax(180px, 240px);
            gap: 1.5rem;
            align-items: center;
            padding: 1.25rem 1.4rem;
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid var(--line);
            box-shadow: 0 22px 55px rgba(7, 22, 48, 0.08);
            border-radius: 8px;
            margin-bottom: 1.2rem;
        }

        .brand-logo img {
            max-width: 100%;
            height: auto;
            display: block;
        }

        .eyebrow {
            color: var(--blue);
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0;
            margin-bottom: 0.35rem;
        }

        .bank-title {
            color: var(--navy);
            font-size: 2rem;
            line-height: 1.15;
            font-weight: 760;
            margin: 0;
        }

        .bank-subtitle {
            color: var(--muted);
            font-size: 0.98rem;
            margin-top: 0.45rem;
        }

        [data-testid="stSelectbox"] label,
        [data-testid="stSelectbox"] label *,
        [data-testid="stSelectbox"] [data-baseweb="select"] *,
        [data-testid="stSelectbox"] label,
        [data-testid="stSelectbox"] label * {
            color: var(--navy) !important;
        }

        [data-testid="stSelectbox"] [data-baseweb="select"] > div {
            background: #ffffff !important;
            border: 1px solid var(--line) !important;
            border-radius: 8px !important;
        }

        [data-testid="stSelectbox"] [data-baseweb="select"] * {
            color: var(--navy) !important;
            fill: var(--navy) !important;
        }

        section.main [data-testid="stSlider"] label,
        section.main [data-testid="stSlider"] label *,
        section.main [data-testid="stSlider"] [data-testid="stTickBar"] *,
        section.main [data-testid="stSlider"] [data-baseweb="slider"] *,
        section.main [data-testid="stFileUploader"] label,
        section.main [data-testid="stFileUploader"] label *,
        section.main [data-testid="stFileUploader"] small,
        section.main [data-testid="stFileUploader"] small *,
        section.main [data-testid="stTextInput"] label,
        section.main [data-testid="stTextInput"] label *,
        section.main [data-testid="stTextArea"] label,
        section.main [data-testid="stTextArea"] label *,
        section.main [data-testid="stDateInput"] label,
        section.main [data-testid="stDateInput"] label *,
        section.main [data-testid="stTimeInput"] label,
        section.main [data-testid="stTimeInput"] label *,
        section.main [data-testid="stNumberInput"] label,
        section.main [data-testid="stNumberInput"] label *,
        section.main [data-testid="stCheckbox"] label,
        section.main [data-testid="stCheckbox"] label *,
        section.main [data-testid="stCheckbox"] p,
        section.main [data-testid="stCheckbox"] span,
        section.main [data-testid="stToggle"] label,
        section.main [data-testid="stToggle"] label *,
        section.main [data-testid="stToggle"] p,
        section.main [data-testid="stToggle"] span,
        section.main [data-testid="stMultiSelect"] label,
        section.main [data-testid="stMultiSelect"] label *,
        section.main [data-testid="stMultiSelect"] [data-baseweb="select"] * {
            color: var(--navy) !important;
            opacity: 1 !important;
        }

        section.main [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {
            background: #242733 !important;
            border: 1px solid #3f4656 !important;
            border-radius: 8px !important;
        }

        section.main [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] *,
        section.main [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button,
        section.main [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] span,
        section.main [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] div,
        section.main [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] small {
            color: #ffffff !important;
            fill: #d8deea !important;
            opacity: 1 !important;
        }

        section.main [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] button {
            background: #111722 !important;
            border: 1px solid #525a6c !important;
        }

        section.main [data-testid="stAlert"] *,
        section.main [data-testid="stNotification"] *,
        section.main .stAlert *,
        section.main [data-testid="stMarkdownContainer"],
        section.main [data-testid="stMarkdownContainer"] p {
            color: var(--navy) !important;
            opacity: 1 !important;
        }

        section.main [data-testid="stNumberInput"] input,
        section.main [data-testid="stTextInput"] input,
        section.main [data-testid="stTextArea"] textarea,
        section.main [data-testid="stDateInput"] input,
        section.main [data-testid="stTimeInput"] input,
        section.main [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
            background: #ffffff !important;
            color: var(--navy) !important;
            border-color: var(--line) !important;
        }

        .help-card {
            background: #f8fbfe;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.9rem;
            min-height: 100%;
        }

        .help-card-title {
            color: var(--navy);
            font-weight: 760;
            font-size: 0.92rem;
            margin-bottom: 0.3rem;
        }

        .help-card-text {
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.45;
        }

        [data-testid="stSidebar"] [data-testid="stRadio"] label,
        [data-testid="stSidebar"] [data-testid="stRadio"] label *,
        [data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] *,
        [data-testid="stSidebar"] [data-testid="stRadio"] p,
        [data-testid="stSidebar"] [data-testid="stRadio"] span {
            color: #ffffff !important;
            opacity: 1 !important;
        }

        .language-title {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 750;
            margin-bottom: 0.35rem;
        }

        .premium-section {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.25rem;
            box-shadow: 0 18px 42px rgba(7, 22, 48, 0.07);
            margin: 1rem 0;
        }

        .section-title {
            color: var(--navy);
            font-size: 1.15rem;
            font-weight: 760;
            margin: 0 0 0.35rem;
        }

        .section-caption {
            color: var(--muted);
            font-size: 0.92rem;
            margin-bottom: 1rem;
        }

        .metric-card, .product-card, .client-card, .detail-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 10px 24px rgba(7, 22, 48, 0.06);
            min-height: 100%;
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 650;
            text-transform: uppercase;
            letter-spacing: 0;
        }

        .metric-value {
            color: var(--navy);
            font-size: 1.7rem;
            line-height: 1.2;
            font-weight: 780;
            margin-top: 0.25rem;
        }

        .metric-note {
            color: var(--muted);
            font-size: 0.82rem;
            margin-top: 0.2rem;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: 999px;
            background: var(--blue-soft);
            color: #07599b;
            padding: 0.3rem 0.7rem;
            font-weight: 700;
            font-size: 0.8rem;
            margin: 0.15rem 0.2rem 0.15rem 0;
        }

        .badge-success {
            background: #e7f7f0;
            color: #08724f;
        }

        .badge-warning {
            background: #fff4df;
            color: #875000;
        }

        .badge-danger {
            background: #ffe8e8;
            color: #b42318;
        }

        .badge-neutral {
            background: #edf2f7;
            color: var(--navy);
        }

        .security-notice {
            background: linear-gradient(135deg, #071630, #0c2347);
            color: #ffffff;
            border-radius: 8px;
            padding: 1rem 1.15rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 18px 42px rgba(7, 22, 48, 0.18);
        }

        .security-notice-title {
            font-weight: 780;
            margin-bottom: 0.35rem;
        }

        .security-notice-text {
            color: rgba(255, 255, 255, 0.86);
            line-height: 1.45;
            font-size: 0.92rem;
        }

        .timeline {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.65rem;
        }

        .timeline-step {
            border: 1px solid var(--line);
            background: #f8fbfe;
            border-radius: 8px;
            padding: 0.75rem;
            min-height: 5.2rem;
        }

        .timeline-step-active {
            background: #e8f4ff;
            border-color: #b8dcff;
        }

        .timeline-index {
            width: 1.55rem;
            height: 1.55rem;
            border-radius: 999px;
            background: var(--navy);
            color: white;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.78rem;
            font-weight: 800;
            margin-bottom: 0.45rem;
        }

        .timeline-label {
            color: var(--navy);
            font-weight: 740;
            font-size: 0.86rem;
            line-height: 1.25;
        }

        .product-icon {
            width: 2.4rem;
            height: 2.4rem;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #e8f4ff, #f4f8fb);
            border: 1px solid var(--line);
            font-size: 1.35rem;
            margin-bottom: 0.65rem;
        }

        .product-title {
            color: var(--navy);
            font-weight: 760;
            font-size: 1rem;
            margin-bottom: 0.35rem;
        }

        .product-score {
            color: var(--blue);
            font-size: 1.55rem;
            font-weight: 800;
        }

        .product-source {
            color: var(--muted);
            font-size: 0.84rem;
            margin-top: 0.15rem;
        }

        .product-meta {
            color: #07599b;
            font-size: 0.78rem;
            font-weight: 750;
            margin-bottom: 0.35rem;
            text-transform: uppercase;
            letter-spacing: 0;
        }

        .product-description {
            color: var(--muted);
            font-size: 0.86rem;
            line-height: 1.45;
            margin-top: 0.55rem;
        }

        .product-list {
            color: var(--ink);
            font-size: 0.84rem;
            margin: 0.55rem 0 0;
            padding-left: 1rem;
        }

        .client-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
        }

        .client-field {
            background: #f8fbfe;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.85rem;
        }

        .client-field-label {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 700;
        }

        .client-field-value {
            color: var(--navy);
            font-weight: 720;
            margin-top: 0.2rem;
            overflow-wrap: anywhere;
        }

        .chat-row-user, .chat-row-bot {
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin: 0.55rem 0;
            border: 1px solid var(--line);
        }

        .chat-row-user {
            background: #e8f4ff;
            color: var(--navy);
        }

        .chat-row-bot {
            background: #ffffff;
            color: var(--ink);
        }

        .stButton > button {
            border-radius: 8px;
            border: 1px solid #087bd0;
            background: linear-gradient(135deg, #0b8ff0 0%, #075fa8 100%);
            color: white;
            font-weight: 760;
            box-shadow: 0 12px 22px rgba(11, 143, 240, 0.22);
        }

        .stButton > button:hover {
            border-color: #075fa8;
            color: white;
            filter: brightness(0.98);
        }

        .stDataFrame {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
        }

        @media (max-width: 900px) {
            .bank-header {
                grid-template-columns: 1fr;
            }
            .client-grid {
                grid-template-columns: 1fr;
            }
            .timeline {
                grid-template-columns: 1fr;
            }
            .bank-title {
                font-size: 1.5rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(logo_path: Path | None, title: str, subtitle: str, language_options: dict[str, str]) -> str:
    """Render the banking header and return the selected language."""

    st.markdown('<div class="bank-header">', unsafe_allow_html=True)
    logo_col, title_col, language_col = st.columns([1.1, 2.8, 1.1], vertical_alignment="center")

    with logo_col:
        if logo_path and logo_path.exists():
            st.image(str(logo_path), use_column_width=True)

    with title_col:
        st.markdown(
            f"""
            <div class="eyebrow">NeuronAIze</div>
            <h1 class="bank-title">{html.escape(title)}</h1>
            <div class="bank-subtitle">{html.escape(subtitle)}</div>
            """,
            unsafe_allow_html=True,
        )

    with language_col:
        language = st.selectbox(
            "Langue / Language",
            options=list(language_options.keys()),
            format_func=lambda value: language_options[value],
            key="language",
        )

    st.markdown("</div>", unsafe_allow_html=True)
    return language


def section_start(title: str, caption: str | None = None) -> None:
    st.markdown('<div class="premium-section">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="section-caption">{html.escape(caption)}</div>', unsafe_allow_html=True)


def section_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def metric_card(label: str, value: object, note: str | None = None) -> None:
    note_html = f'<div class="metric-note">{html.escape(str(note))}</div>' if note else ""
    st.markdown(
        (
            '<div class="metric-card">'
            f'<div class="metric-label">{html.escape(str(label))}</div>'
            f'<div class="metric-value">{html.escape(str(value))}</div>'
            f"{note_html}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def badge(label: str) -> None:
    st.markdown(f'<span class="badge">{html.escape(label)}</span>', unsafe_allow_html=True)


def status_badge(label: str, css_class: str = "badge-neutral") -> None:
    st.markdown(
        f'<span class="badge {html.escape(css_class)}">{html.escape(label)}</span>',
        unsafe_allow_html=True,
    )


def security_notice(title: str, text: str) -> None:
    st.markdown(
        (
            '<div class="security-notice">'
            f'<div class="security-notice-title">{html.escape(title)}</div>'
            f'<div class="security-notice-text">{html.escape(text)}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def timeline(steps: list[str], active_step: int) -> None:
    content = ['<div class="timeline">']
    for index, label in enumerate(steps, start=1):
        css_class = "timeline-step timeline-step-active" if index == active_step else "timeline-step"
        content.append(
            (
                f'<div class="{css_class}">'
                f'<div class="timeline-index">{index}</div>'
                f'<div class="timeline-label">{html.escape(label)}</div>'
                "</div>"
            )
        )
    content.append("</div>")
    st.markdown("\n".join(content), unsafe_allow_html=True)


def product_card(
    product_name: str,
    icon: str,
    score: float | None = None,
    source: str | None = None,
    category: str | None = None,
    description: str | None = None,
    benefits: list[str] | None = None,
    eligibility: list[str] | None = None,
) -> None:
    score_html = f'<div class="product-score">{score:.1f}%</div>' if score is not None else ""
    source_html = f'<div class="product-source">{html.escape(source)}</div>' if source else ""
    category_html = f'<div class="product-meta">{html.escape(category)}</div>' if category else ""
    description_html = (
        f'<div class="product-description">{html.escape(description)}</div>' if description else ""
    )
    benefit_items = "".join(f"<li>{html.escape(item)}</li>" for item in (benefits or [])[:2])
    benefits_html = f'<ul class="product-list">{benefit_items}</ul>' if benefit_items else ""
    eligibility_items = "".join(f"<li>{html.escape(item)}</li>" for item in (eligibility or [])[:1])
    eligibility_html = f'<ul class="product-list">{eligibility_items}</ul>' if eligibility_items else ""
    st.markdown(
        (
            '<div class="product-card">'
            f'<div class="product-icon">{icon}</div>'
            f"{category_html}"
            f'<div class="product-title">{html.escape(product_name)}</div>'
            f"{score_html}"
            f"{source_html}"
            f"{description_html}"
            f"{benefits_html}"
            f"{eligibility_html}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def client_field_grid(fields: list[tuple[str, object]]) -> None:
    content = ['<div class="client-grid">']
    for label, value in fields:
        shown_value = "-" if pd.isna(value) else str(value)
        content.append(
            (
                '<div class="client-field">'
                f'<div class="client-field-label">{html.escape(label)}</div>'
                f'<div class="client-field-value">{html.escape(shown_value)}</div>'
                "</div>"
            )
        )
    content.append("</div>")
    st.markdown("\n".join(content), unsafe_allow_html=True)


def detail_card(title: str, items: list[str]) -> None:
    list_items = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    st.markdown(
        (
            '<div class="detail-card">'
            f'<div class="product-title">{html.escape(title)}</div>'
            f"<ul>{list_items}</ul>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def chat_message(role: str, message: str) -> None:
    css_class = "chat-row-user" if role == "user" else "chat-row-bot"
    st.markdown(
        f'<div class="{css_class}">{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )
