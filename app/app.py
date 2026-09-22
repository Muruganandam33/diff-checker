"""Diff Checker - a tiny Flask app that compares two texts."""
import difflib
import os

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


def get_config():
    """Read configuration from environment variables (with defaults)."""
    return {
        "env": os.environ.get("APP_ENV", "development"),
        "message": os.environ.get("APP_MESSAGE", "Diff Checker"),
        "version": os.environ.get("APP_VERSION", "1.0"),
    }


def compute_diff(text_a, text_b):
    """Return a list of (css_class, line) tuples describing the differences."""
    result = []
    for line in difflib.ndiff(text_a.splitlines(), text_b.splitlines()):
        if line.startswith("- "):
            result.append(("removed", line))    # only in Text A
        elif line.startswith("+ "):
            result.append(("added", line))      # only in Text B
        elif line.startswith("  "):
            result.append(("same", line))       # in both
        # lines starting with "? " are hints from difflib - we skip them
    return result


@app.route("/", methods=["GET", "POST"])
def index():
    text_a = text_b = ""
    compared = identical = False
    diff_lines = []

    if request.method == "POST":
        # Browsers send new lines as \r\n, so normalise them first
        text_a = request.form.get("text_a", "").replace("\r\n", "\n")
        text_b = request.form.get("text_b", "").replace("\r\n", "\n")
        compared = True
        identical = text_a == text_b
        if not identical:
            diff_lines = compute_diff(text_a, text_b)

    return render_template(
        "index.html",
        config=get_config(),
        text_a=text_a,
        text_b=text_b,
        compared=compared,
        identical=identical,
        diff_lines=diff_lines,
        has_line_changes=any(k != "same" for k, _ in diff_lines),
    )


@app.route("/health")
def health():
    return jsonify(status="ok", version=get_config()["version"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
