def build_explanation_html_for_anki(explanation_data, gettext_func):
    _ = gettext_func
    definitions = explanation_data.get("definitions", [])
    locutions = explanation_data.get("locutions", [])
    fallback_text = explanation_data.get("fallback_text")

    html_parts = []

    if definitions:
        html_parts.append(
            f"""
            <div style="font-size:18px; font-weight:700; margin-bottom:12px; color:#1f2937;">
                {_('Definitions:')}
            </div>
            """
        )

        for item in definitions:
            number = f"{item['number']}. " if item.get("number") else ""
            html_parts.append(
                f"""
                <div style="margin-bottom:16px; padding:14px; border:1px solid #e5e7eb; border-radius:12px; background:#ffffff;">
                    <div style="font-size:15px; line-height:1.6; color:#1f2937;">
                        <strong>{number}</strong>{item['text']}
                    </div>
                """
            )

            if item.get("examples"):
                examples_html = "".join(
                    [f"<li style='margin-bottom:6px;'>{ex}</li>" for ex in item["examples"]]
                )
                html_parts.append(
                    f"""
                    <div style="margin-top:10px;">
                        <div style="font-weight:700; color:#374151; margin-bottom:6px;">{_('Examples')}</div>
                        <ul style="margin:0; padding-left:18px; color:#4b5563;">
                            {examples_html}
                        </ul>
                    </div>
                    """
                )

            if item.get("synonyms"):
                synonyms = ", ".join(item["synonyms"])
                html_parts.append(
                    f"""
                    <div style="margin-top:10px; color:#4b5563;">
                        <strong>{_('Synonyms')}:</strong> {synonyms}
                    </div>
                    """
                )

            html_parts.append("</div>")

    if locutions:
        html_parts.append(
            f"""
            <div style="font-size:18px; font-weight:700; margin:20px 0 12px; color:#1f2937;">
                {_('Expressions / Locutions')}
            </div>
            """
        )

        for loc in locutions:
            html_parts.append(
                f"""
                <div style="margin-bottom:12px; padding:14px; border:1px solid #e5e7eb; border-radius:12px; background:#ffffff;">
                    <div style="font-weight:700; color:#2563eb; margin-bottom:6px;">{loc['title']}</div>
                    <div style="color:#374151; line-height:1.6;">{loc['text']}</div>
                </div>
                """
            )

    if explanation_data.get("corpus_examples"):
        html_parts.append(
            f"""
            <div style="font-size:18px; font-weight:700; margin:20px 0 12px; color:#1f2937;">
                {_('Example Phrases')}
            </div>
            """
        )
        for ex in explanation_data["corpus_examples"]:
            html_parts.append(
                f"""
                <div style="margin-bottom:10px; padding:12px; border:1px solid #e2e8f0; border-radius:10px; background:#f1f5f9; color:#475569; font-style: italic;">
                    "{ex}"
                </div>
                """
            )

    if not html_parts and fallback_text:
        return f"<div style='color:#374151; line-height:1.6;'>{fallback_text}</div>"

    return "".join(html_parts) or f"<div>{_('Definition not found.')}</div>"
