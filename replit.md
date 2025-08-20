# Overview

An automated job application system that monitors job postings from multiple sources (Lever and Greenhouse APIs), matches them against predefined resume profiles using keyword analysis, and sends notifications through Slack. The system stores matched jobs in Airtable for tracking and runs continuously with configurable scheduling intervals.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes (August 20, 2025)

## Human-in-the-Loop v0 Implementation - COMPLETED ✅ (August 20, 2025)
- ✅ **ARCHITECTURE ALIGNMENT**: Implemented comprehensive human-in-the-loop system with no Claude/LLM dependencies
- ✅ **FEATURE FLAGS**: Configured USE_CLAUDE_FALLBACK=false, ENABLE_SLACK=false, ENABLE_AIRTABLE=false for minimal operation
- ✅ **API ENDPOINTS**: Built 3 FastAPI endpoints for human analysis input with full validation guardrails
- ✅ **DATA VALIDATION**: Anti-fabrication checks prevent new metrics/skills in resume deltas, operation constraints enforced
- ✅ **DATABASE SAFETY**: Created backup schema, all 19 Rev A tables verified and operational
- ✅ **JOB PROCESSING**: System actively processing 126 PM jobs from multiple companies with comprehensive storage
- ✅ **MINIMAL DEPENDENCIES**: Reduced to core packages only (FastAPI, Supabase, requests, schedule)
- ✅ **READY FOR USE**: Human analysts can now input analysis via API endpoints with full audit trail

# Previous Changes (August 18, 2025)

## Dynamic Job Discovery Implementation - COMPLETED ✅ (August 18, 2025)
- ✅ **GREENHOUSE API FIX**: Resolved job description issue by adding `content=true` parameter, now fetching 4,943-char descriptions
- ✅ **DYNAMIC COMPANY DISCOVERY**: Replaced hardcoded company lists with intelligent discovery of active companies
- ✅ **EXPANDED COVERAGE**: System now discovers 31+ active Greenhouse companies with real job postings (879+ jobs)
- ✅ **LEVER AUTHENTICATION**: Updated Lever client with proper basic auth format per API documentation
- ✅ **API OPTIMIZATION**: System only queries companies that actually have active job postings
- ✅ **SYNTAX FIXES**: Resolved indentation errors in observability tracking with graceful fallbacks
- ⏳ **LEVER API KEY**: Awaiting authentication credentials to enable Lever job fetching

## SmartApply Rev A Complete Implementation - COMPLETED ✅ (August 18, 2025)
- ✅ **DATABASE SCHEMA UPGRADE**: Deployed comprehensive 19-table SmartApply Rev A schema with UUID PKs and RLS
- ✅ **TRANSLATOR SERVICE**: Concept translation with company-specific styling and Claude fallback with LLM caching
- ✅ **OBSERVABILITY TRACKING**: Ingestion runs and API call tracking with comprehensive metrics
- ✅ **RESUME DELTA SERVICE**: Resume optimization through master_bullets delta generation with experience blocking
- ✅ **JOIN TABLE NORMALIZATION**: Replaced arrays with translation_event_mappings join table structure
- ✅ **CALIBRATION VALIDATION**: 85.7% concept match rate across 4 resume profiles with 10% threshold
- ✅ **FEATURE FLAGS**: USE_CLAUDE_FALLBACK with per-company daily throttling and 7-day TTL caching
- ✅ **PERFORMANCE INDEXES**: 8 strategic indexes including lower(raw_term) for fast concept lookups

## Simplified Supabase-Only Architecture - COMPLETED ✓ (August 18, 2025)
- ✅ **ARCHITECTURAL SIMPLIFICATION**: Removed Slack and Airtable dependencies for standalone operation
- ✅ **CONFIGURATION FLAGS**: Added `USE_SLACK = False` and `USE_AIRTABLE = False` in `config.py`
- ✅ **NO-OP API CLIENTS**: Refactored `slack_client.py`, `airtable_client.py`, and `slack_event_handler.py` to safe no-ops
- ✅ **DEPENDENCY MINIMIZATION**: Updated `pyproject.toml` to only include core packages (python-dotenv, requests, schedule, supabase)
- ✅ **OPTIONAL INTEGRATION**: System runs without runtime errors when external API keys are missing
- ✅ **BACKWARD COMPATIBILITY**: All function signatures preserved, methods return safe defaults when services disabled
- ✅ **SUPABASE CORE**: System maintains full semantic vocabulary learning capabilities with 11-table learning database

## Multi-File Supabase + Learning Upgrade - COMPLETED ✓
- ✅ **LEARNING DATABASE**: Comprehensive 11-table schema for semantic vocabulary learning
- ✅ **REPOSITORY LAYER**: Full CRUD operations with `app/db/supabase_repo.py`
- ✅ **CONCEPT EXTRACTION**: Intelligent concept mapping service with confidence scoring  
- ✅ **JOB ANALYSIS**: Automatic job posting analysis and concept extraction
- ✅ **TRANSLATION EVENTS**: ML pipeline for vocabulary association learning
- ✅ **SCHEMA FIX**: Resolved foreign key constraint errors with `schema_fixed.sql`
- ✅ **CORE FUNCTIONALITY**: System operates independently with Supabase PostgreSQL database only

## Previous Supabase Integration (August 16, 2025)
- ✅ Added Supabase database integration for dynamic company management
- ✅ Created comprehensive SupabaseClient with full CRUD operations for companies table
- ✅ Integrated with existing Lever and Greenhouse job fetching clients
- ✅ Fallback system maintains reliability - uses hardcoded company list if Supabase unavailable
- ✅ Database schema supports worldview tags and language patterns for advanced company categorization
- ✅ Successfully tested with 4 companies: Epic Games, Stripe, Slack, Notion
- ✅ Company filtering by worldview tags (gaming-first, creator-ecosystem, fintech, etc.)

## Previous System Status (August 15, 2025)
- ✅ Concept-based matching algorithm with sophisticated concept grouping
- ✅ Four resume profiles powered by concept maps (Platform Infrastructure, Developer Tools, Billing Platform, Internal Tools)
- ✅ React-to-Track feature fully operational with ✅ Slack reactions automatically logging to Airtable
- ✅ Slack Events API server running on port 5000 with working webhook handling
- ✅ System actively monitoring 2,750+ jobs every 15 minutes from Lever and Greenhouse APIs
- ✅ Product Manager role filtering with 15% threshold for concept-based matches
- ✅ Enhanced Slack notification formatting and processed jobs deduplication system

# System Architecture

## Core Components

### Job Fetching Architecture
- **API Clients**: Modular clients for Lever and Greenhouse job board APIs
- **Multi-Source Aggregation**: Unified job fetching from multiple recruitment platforms
- **Company Targeting**: Configurable list of target companies for focused job searching
- **Rate Limiting**: Built-in timeout handling and error management for API calls

### Matching Engine
- **Keyword-Based Matching**: Text processing engine that extracts and matches keywords from job descriptions
- **Resume Profiles**: Predefined skill sets and keyword collections for different career tracks
- **Scoring Algorithm**: Calculates match percentages between job requirements and resume profiles
- **Text Normalization**: Cleans and standardizes text for consistent matching results

### Notification System
- **Optional Slack Integration**: Automated job alerts sent to configured Slack channels (when enabled)
- **Rich Formatting**: Structured messages with job details, match scores, and direct application links
- **Error Handling**: Robust error management for message delivery failures
- **Standalone Operation**: System functions fully without external notification dependencies

### Data Storage
- **Supabase PostgreSQL**: Primary database with 11-table schema for semantic vocabulary learning and job tracking
- **Optional Airtable Backend**: Cloud-based storage for job records and application tracking (when enabled)
- **Duplicate Prevention**: Local JSON-based tracking to avoid reprocessing the same jobs
- **Data Persistence**: File-based storage with automatic cleanup of old entries

### Scheduling Framework
- **Background Processing**: Thread-based scheduler for continuous operation
- **Configurable Intervals**: Adjustable check frequencies via environment variables
- **Graceful Shutdown**: Clean stop mechanisms with proper resource cleanup

## Configuration Management
- **Environment-Based**: All sensitive data and settings managed through environment variables
- **Optional Services**: Configuration flags (`USE_SLACK`, `USE_AIRTABLE`) for enabling external integrations
- **Validation Layer**: Startup validation only for enabled services
- **Flexible Thresholds**: Adjustable matching scores and operational parameters

## Error Handling and Logging
- **Comprehensive Logging**: Multi-level logging with both console and file outputs
- **Exception Management**: Graceful handling of API failures and network issues
- **Monitoring**: Detailed execution logs for debugging and performance tracking

# External Dependencies

## Third-Party APIs
- **Lever API**: Job posting retrieval from Lever-powered company career pages
- **Greenhouse API**: Job posting retrieval from Greenhouse-powered company career pages
- **Slack Web API**: Message delivery for job notifications and alerts
- **Airtable API**: Cloud database for job storage and application tracking
- **Supabase API**: PostgreSQL database for dynamic company management and categorization

## Python Libraries
- **requests**: HTTP client for API communications
- **slack-sdk**: Official Slack SDK for bot interactions
- **threading**: Built-in Python threading for background job scheduling
- **json**: Data serialization for local storage and configuration
- **logging**: Application logging and monitoring
- **os**: Environment variable access and file system operations

## Storage Systems
- **Local JSON Files**: Temporary storage for processed job tracking
- **Airtable Base**: Cloud database for persistent job records and application status
- **Log Files**: File-based logging for system monitoring and debugging

## Authentication Requirements
- API keys required for Lever, Greenhouse, Slack, Airtable, and Supabase services
- Token-based authentication for all external service integrations
- Environment variable configuration for secure credential management