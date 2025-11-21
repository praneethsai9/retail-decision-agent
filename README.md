# Retail Decision Agent

Multi-agent AI system for automated competitive pricing decisions using Google ADK and BigQuery.

## Overview

This project automates retail pricing strategy responses by orchestrating specialized AI agents that simulate executive decision-making. When competitors undercut product prices, the system automatically generates coordinated recommendations from marketing, finance, and operations perspectives, synthesizes them into a final strategic decision, and logs everything for audit purposes.

**Key Features:**
- 🤖 Seven specialized AI agents working in sequence (DataFinder, CMO, CFO, Operations, CEO, Logger, Reporter)
- ⚡ 25-30 second end-to-end decision generation
- 📊 Full audit trail in BigQuery for compliance and analysis
- 🔄 Automated hourly analysis of competitor pricing threats
- 🎯 Production-ready FastAPI application 
- 🐳 Containerized deployment with Docker

## Architecture

```
Competitor Data (Web Scraping Service)
    ↓
BigQuery: market_signals table
    ↓
Scheduled Trigger (hourly)
    ↓
Multi-Agent Workflow:
  1. DataFinder → Detects undercut products
  2. CMO → Proposes marketing strategy
  3. CFO → Analyzes financial impact
  4. Operations → Assesses feasibility
  5. CEO → Makes final decision
  6. Logger → Records to database
  7. Reporter → Generates summary
    ↓
BigQuery: council_debates table
    ↓
Business Intelligence Dashboard
```

## Technology Stack

- **AI Framework:** Google ADK (Agent Development Kit)
- **LLM:** Gemini 2.0 Flash Exp
- **Database:** Google BigQuery
- **API Framework:** FastAPI
- **Deployment:** Docker, Google Cloud Run
- **Language:** Python 3.12

## Prerequisites

### Google Cloud Setup
- GCP project with billing enabled
- BigQuery API enabled
- Gemini API access configured
- Application Default Credentials or service account key

### Required BigQuery Tables

**1. products table:**
```sql
CREATE TABLE retail_db.products (
  product_id STRING,
  name STRING,
  cost_price FLOAT64,
  current_stock INT64
);
```

**2. market_signals table:**
```sql
CREATE TABLE retail_db.market_signals (
  product_id STRING,
  competitor_name STRING,
  detected_price FLOAT64,
  signal_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

**3. council_debates table:**
```sql
CREATE TABLE retail_db.council_debates (
  debate_id STRING,
  product_signals JSON,
  cmo_proposal STRING,
  cfo_rebuttal STRING,
  ops_input STRING,
  ceo_verdict STRING,
  decision_status STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

### Software Requirements
- Python 3.10+
- Docker Desktop
- Google Cloud SDK (`gcloud` CLI)

## Project Structure

```
retail-decision-agent/
├── agent/
│   ├── __init__.py          # Package initialization
│   └── agent.py             # Agent definitions and orchestration
├── app.py                   # FastAPI application
├── Dockerfile               # Container configuration
├── pyproject.toml          # Python dependencies
└── README.md               # This file
```

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd retail-decision-agent
```

### 2. Set Up Google Cloud Authentication

**Option A: Application Default Credentials (for local development)**
```bash
gcloud auth application-default login
```

**Option B: Service Account Key (for production)**
```bash
# Create service account
gcloud iam service-accounts create retail-decision-agent

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:retail-decision-agent@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:retail-decision-agent@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account=retail-decision-agent@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 3. Update Configuration

Edit `agent/agent.py` and replace:
```python
CLOUD_PROJECT_ID = "cr-ai-nov-2025"  # Replace with your GCP project ID
```

### 4. Install Dependencies

**Using pip:**
```bash
pip install -e .
```

**Using uv (faster):**
```bash
pip install uv
uv pip install --system --requirement pyproject.toml
```

## Usage

### Local Development

**Run the FastAPI server:**
```bash
python app.py
```

**Access the application:**
- Web UI: http://localhost:8080
- API Docs: http://localhost:8080/docs
- Health Check: http://localhost:8080/health

**Test the workflow:**

In the web UI, enter:
```
Analyze current competitor pricing threats and provide executive recommendations.
```

### Docker Deployment

**Build the image:**
```bash
docker build -t retail-decision-agent .
```

**Run with Application Default Credentials:**
```bash
docker run -p 8080:8080 \
  -v ~/.config/gcloud:/root/.config/gcloud \
  -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
  retail-decision-agent
```

**Run with service account key:**
```bash
docker run -p 8080:8080 \
  -v $(pwd)/key.json:/app/key.json \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/key.json \
  retail-decision-agent
```

### Cloud Run Deployment

**Deploy to Google Cloud Run:**
```bash
gcloud run deploy retail-decision-agent \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account=retail-decision-agent@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

**Set up hourly scheduling:**
```bash
gcloud scheduler jobs create http competitive-pricing-check \
  --schedule="0 * * * *" \
  --uri="https://retail-decision-agent-xxx.run.app/agents/ExecutiveDecisionWorkflow_V2/run" \
  --http-method=POST \
  --message-body='{"query":"Analyze competitor pricing threats"}' \
  --oidc-service-account-email=retail-decision-agent@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## How It Works

### Agent Workflow

1. **DataFinder Agent**
   - Queries BigQuery to find products where competitor prices < your cost price
   - Joins `products` and `market_signals` tables
   - Outputs JSON array of undercut products

2. **CMO Agent**
   - Receives undercut product data
   - Proposes marketing counterstrategy (bundles, campaigns, positioning)
   - Outputs marketing proposal text

3. **CFO Agent**
   - Reviews undercut data and CMO proposal
   - Analyzes financial impact, margin calculations, budget needs
   - Outputs financial analysis and recommendations

4. **Operations Agent**
   - Reviews all previous inputs
   - Assesses inventory levels, fulfillment capacity, timeline feasibility
   - Outputs operational feasibility assessment

5. **CEO Agent**
   - Synthesizes all four perspectives
   - Makes final strategic decision with clear rationale
   - Outputs JSON with verdict and status (APPROVED/DEFERRED/REJECTED)

6. **Logger Agent**
   - Writes complete decision record to `council_debates` table
   - Creates audit trail for compliance

7. **Reporter Agent**
   - Generates clean markdown summary for end users
   - Formats all agent outputs into executive report

### State Management

Agents communicate via ADK's automatic state management:
- Each agent saves output to a named key (e.g., `cmo_proposal`)
- Subsequent agents reference these keys in their instructions: `{cmo_proposal}`
- ADK handles all data passing automatically

## Sample Output

```markdown
# Executive Decision Report

## Undercut Products Detected
- **PROD-12345: Premium Wireless Headphones**
  - Our cost: $45.00
  - TechRival Inc. price: $39.99

## Marketing Strategy (CMO)
Launch "Premium Sound Promise" campaign emphasizing 3-year warranty...

## Financial Analysis (CFO)
Bundle maintains 12.7% margin, requires $40K budget...

## Operational Assessment (COO)
1,250 units in stock, 10-day launch timeline feasible...

## CEO Final Decision
**Status:** APPROVED
**Verdict:** Proceed with bundling strategy...
```

## Configuration

### Environment Variables

```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
CLOUD_PROJECT_ID=your-project-id
DATASET_ID=retail_db
```

### Agent Model Selection

To change the LLM model, edit `agent/agent.py`:
```python
data_finder = LlmAgent(
    name="DataFinder",
    model="gemini-2.0-flash-exp",  # Change model here
    ...
)
```

Available models:
- `gemini-2.0-flash-exp` (recommended - fast and cost-effective)
- `gemini-1.5-pro`
- `gemini-1.5-flash`

## Monitoring

### View Decision Logs

```sql
SELECT 
  debate_id,
  decision_status,
  created_at,
  ceo_verdict
FROM retail_db.council_debates
ORDER BY created_at DESC
LIMIT 10;
```

### Check Application Health

```bash
curl http://localhost:8080/health
```

### View Logs (Cloud Run)

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=retail-decision-agent" \
  --limit 50 \
  --format json
```

## Troubleshooting

### Issue: "DefaultCredentialsError"
**Solution:** Ensure Google Cloud credentials are properly configured:
```bash
gcloud auth application-default login
```

### Issue: "BigQuery permission denied"
**Solution:** Grant required roles to your service account:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SA@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

### Issue: "Agent output_key not found"
**Solution:** Check that:
1. Previous agent completed successfully
2. `output_key` name matches exactly in subsequent agent instructions
3. Agent instructions explicitly save to the output_key

### Issue: Slow response times (>60 seconds)
**Solution:** 
- Check BigQuery query performance
- Consider caching DataFinder results
- Evaluate parallel execution for independent agents (CMO, CFO, Ops)

## Performance

- **Average workflow time:** 25-30 seconds (7 sequential LLM calls)
- **Cost per decision:** ~$0.08 (using Gemini 2.0 Flash)
- **Concurrency:** Handles multiple simultaneous requests via FastAPI async

## Security Considerations

- Never commit service account keys to version control
- Use `.env` files for local development (add to `.gitignore`)
- Disable web UI in production (`web=False` in `app.py`)
- Implement authentication for API endpoints in production
- Restrict BigQuery access using IAM roles (principle of least privilege)

## Contributing

Contributions welcome! Areas for improvement:
- Add unit tests for agent instructions
- Implement human-in-the-loop approval gates
- Add performance tracking and feedback loops
- Support for multiple retail categories
- Integration with pricing execution systems

## License

[Specify your license here]

## Contact

[Your contact information or team information]

## Acknowledgments

- Built with [Google Agent Development Kit (ADK)](https://cloud.google.com/adk)
- Uses [Gemini AI](https://ai.google.dev/) for agent intelligence
- Powered by [Google BigQuery](https://cloud.google.com/bigquery)

## Related Resources

- [Project Blog Post](link-to-your-medium-article)
- [Google ADK Documentation](https://cloud.google.com/adk/docs)
- [BigQuery Best Practices](https://cloud.google.com/bigquery/docs/best-practices)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
