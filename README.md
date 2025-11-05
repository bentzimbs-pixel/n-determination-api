# EN Determination API – Vertical Slice

A minimal FastAPI service demonstrating intake → extraction → rule evaluation → result, ready for deployment on Google Cloud Run.

## Features

- **FastAPI**: Modern, high-performance web framework.
- **Endpoints**: `/v1/determinations`, `/v1/determinations/{id}`, `/health`, and a stub FHIR op `POST /fhir/Patient/{id}/$determine-necessity`.
- **Logic**: A simple rules evaluator and naive NLP for detecting dysphagia & weight-loss.
- **Artifacts**: Generates a PDF summary of the determination and stores it in Google Cloud Storage.
- **CI/CD**: Ready for automated deployment with Google Cloud Build and GitHub Actions.

## Run Locally

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the development server**:
    ```bash
    export API_KEY=dev-key
    uvicorn app.main:app --reload
    ```

3.  **Access the docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

### Example Request

```bash
curl -X POST http://localhost:8000/v1/determinations \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: dev-key' \
  -d '{
    "caseId":"case-123",
    "payerCode":"CMS",
    "policyVersion":"2025.1",
    "bundle":{
      "patient": {"id":"p1"},
      "bmi": 17.9,
      "weights":[{"date":"2025-01-01","kg":70.0},{"date":"2025-06-01","kg":61.0}],
      "notes":[{"id":"n1","text":"SLP note: patient with dysphagia, unable to meet >50% caloric needs orally. Nutrition plan documented. PEG planned."}]
    }
  }'