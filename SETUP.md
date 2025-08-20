# SmartApply Architecture - Setup Instructions

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn jupyter
   ```

2. **Run the API:**
   ```bash
   uvicorn app.main:app --reload
   ```
   Visit `http://localhost:8000/docs` for interactive API documentation.

3. **Try the demo notebook:**
   ```bash
   jupyter notebook demo/matching_demo.ipynb
   ```

## Project Structure

```
smartapply-architecture/
├── README.md                    # Main project documentation
├── sql/schema.sql              # 19-table PostgreSQL schema
├── app/
│   ├── main.py                 # FastAPI application
│   └── services/               # Service layer
│       ├── translator.py       # Vocabulary translation
│       ├── observability.py    # Metrics & monitoring
│       └── resume_delta.py     # Resume change validation
├── demo/
│   ├── data/                   # Synthetic demo data
│   └── matching_demo.ipynb     # Interactive demo
├── docs/
│   ├── architecture.md         # Detailed architecture docs
│   └── diagrams/system.mmd     # Mermaid system diagram
└── tests/
    └── test_schema.py          # Basic validation tests
```

## API Endpoints

- `GET /` - Health check and endpoint list
- `POST /human/role-analysis/validate` - Validate job analysis
- `POST /human/resume-optimization/validate` - Validate resume changes  
- `POST /human/translation-event/validate` - Log translation events
- `GET /demo/schema-info` - Database schema information

## GitHub Setup Instructions

To push this repository to GitHub:

1. **Create GitHub repository:**
   - Go to github.com and create a new **public** repository
   - Name it `smartapply-architecture`
   - Don't initialize with README (already exists)

2. **Connect and push:**
   ```bash
   cd smartapply-architecture
   git remote add origin https://github.com/YOUR_USERNAME/smartapply-architecture.git
   git branch -M main
   git push -u origin main
   ```

3. **Verify CI/CD:**
   - GitHub Actions will run automatically
   - Check the "Actions" tab for build status
   - All tests should pass with green checkmarks

## Verification Checklist

✅ **Security**: No secrets or API keys in repository  
✅ **Data Safety**: Only synthetic demo data included  
✅ **Schema**: Production-ready 19-table PostgreSQL schema  
✅ **Services**: Stubbed implementations with production patterns  
✅ **Documentation**: Comprehensive README and architecture docs  
✅ **Demo**: Working Jupyter notebook with synthetic matching  
✅ **API**: FastAPI application with validation endpoints  
✅ **CI/CD**: GitHub Actions workflow with security scanning  

## Portfolio Context

This repository demonstrates:
- **Systems Design**: 19-table normalized schema with RLS policies
- **API Architecture**: FastAPI with Pydantic validation models
- **Service Patterns**: Clean architecture with dependency injection
- **Data Validation**: Anti-fabrication checks and business rule enforcement
- **Observability**: Comprehensive metrics and audit trail design
- **Documentation**: Production-ready documentation standards

**What's NOT included (intentionally):**
- Proprietary vocabulary mapping algorithms
- Real job posting data or user resumes
- Production LLM integration logic
- Company-specific business rules
- Live API credentials or secrets

This showcases the **architecture and execution patterns** without exposing competitive advantages or sensitive data.