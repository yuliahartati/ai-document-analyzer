import json


def parse_response(content):
    """
    Parse JSON returned by the model.
    """

    return json.loads(content)


def build_markdown_report(result):
    """
    Convert analysis result into a Markdown report.
    """

    report = "# AI Document Analysis Report\n\n"

    report += "## Executive Summary\n\n"
    report += f"{result['summary']}\n\n"

    report += "---\n\n"

    report += "## Key Insights\n\n"

    if result["key_insights"]:
        for item in result["key_insights"]:
            report += f"- {item}\n"
    else:
        report += "- None\n"

    report += "\n## Facts\n\n"

    if result["facts"]:
        for item in result["facts"]:
            report += f"- {item}\n"
    else:
        report += "- None\n"

    report += "\n## Claims\n\n"

    if result["claims"]:
        for item in result["claims"]:
            report += f"- {item}\n"
    else:
        report += "- None\n"

    report += "\n## Action Items\n\n"

    if result["action_items"]:
        for item in result["action_items"]:
            report += f"- {item}\n"
    else:
        report += "- None\n"

    return report


def item_count(items):
    """
    Return the number of items in a list.
    """

    return len(items) if items else 0


def has_content(items):
    """
    Check whether a section contains content.
    """

    return bool(items)
