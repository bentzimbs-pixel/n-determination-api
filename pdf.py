from __future__ import annotations
import io
import os
from datetime import datetime
from google.cloud import storage
from weasyprint import HTML, CSS

from .models import DeterminationResult

ARTIFACTS_BUCKET = os.getenv("ARTIFACTS_BUCKET")
PUBLIC_ARTIFACTS = os.getenv("PUBLIC_ARTIFACTS", "false").lower() == "true"

HTML_TMPL = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; font-size: 14px; }
    h1 { font-size: 20px; margin: 0 0 8px; }
    h2 { font-size: 16px; margin: 16px 0 4px; border-bottom: 1px solid #eee; padding-bottom: 4px; }
    .pill { padding: 2px 8px; border-radius: 6px; display: inline-block; border: 1px solid #999; background: #f0f0f0; }
    .pill.MEETS { background-color: #e6ffed; border-color: #5cb85c; }
    .pill.NOT_MEETS { background-color: #f8d7da; border-color: #d9534f; }
    .pill.INSUFFICIENT { background-color: #fff3cd; border-color: #f0ad4e; }
    table { border-collapse: collapse; width: 100%; margin-top: 8px; }
    th, td { border: 1px solid #ddd; padding: 8px; font-size: 12px; text-align: left; }
    th { background-color: #f9f9f9; }
  </style>
</head>
<body>
  <h1>Enteral Nutrition Medical Necessity – Determination</h1>
  <p><strong>ID:</strong> {{det.id}} &nbsp; <strong>Case:</strong> {{det.caseId}} &nbsp; <strong>Policy:</strong> {{det.policy}}</p>
  <p><strong>Status:</strong> <span class="pill {{det.status}}">{{det.status}}</span></p>
  <p><strong>Summary:</strong> {{det.summary}}</p>

  <h2>Criteria Evaluation</h2>
  <table>
    <thead><tr><th>ID</th><th>Criterion</th><th>Outcome</th></tr></thead>
    <tbody>
      {% for c in det.criteria %}
      <tr><td>{{c.id}}</td><td>{{c.label}}</td><td>{{c.outcome}}</td></tr>
      {% endfor %}
    </tbody>
  </table>
  <p style="margin-top:24px;font-size:10px;color:#666;text-align:right;">Generated {{ts}} UTC</p>
</body>
</html>
"""


def _upload_bytes(bucket: str, blob_name: str, data: bytes, content_type: str = "application/pdf") -> str:
    client = storage.Client()
    bucket_ref = client.bucket(bucket)
    blob = bucket_ref.blob(blob_name)
    if PUBLIC_ARTIFACTS:
        blob.upload_from_string(data, content_type=content_type, predefined_acl="publicRead")
        return blob.public_url
    else:
        blob.upload_from_string(data, content_type=content_type)
        # For private files, return a gsutil URI or a signed URL
        # Here we return a gsutil URI as a placeholder
        return f"gs://{bucket}/{blob_name}"


def render_and_store_pdf(det: DeterminationResult) -> str:
    if not ARTIFACTS_BUCKET:
        raise RuntimeError("ARTIFACTS_BUCKET env var not set")
    from jinja2 import Template
    html = Template(HTML_TMPL).render(det=det.model_dump(), ts=datetime.utcnow().isoformat(timespec='seconds'))
    
    # Using a CSS object from a string for more complex styles if needed
    # In this case, the styles are in the template, but this is a good pattern.
    css = CSS(string='@page { size: A4; margin: 1in; }')
    pdf_bytes = HTML(string=html).write_pdf(stylesheets=[css])
    
    key = f"determinations/{det.id}.pdf"
    return _upload_bytes(ARTIFACTS_BUCKET, key, pdf_bytes)