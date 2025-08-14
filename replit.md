# Overview

An automated job application system that monitors job postings from multiple sources (Lever and Greenhouse APIs), matches them against predefined resume profiles using keyword analysis, and sends notifications through Slack. The system stores matched jobs in Airtable for tracking and runs continuously with configurable scheduling intervals.

# User Preferences

Preferred communication style: Simple, everyday language.

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
- **Slack Integration**: Automated job alerts sent to configured Slack channels
- **Rich Formatting**: Structured messages with job details, match scores, and direct application links
- **Error Handling**: Robust error management for message delivery failures

### Data Storage
- **Airtable Backend**: Cloud-based storage for job records and application tracking
- **Duplicate Prevention**: Local JSON-based tracking to avoid reprocessing the same jobs
- **Data Persistence**: File-based storage with automatic cleanup of old entries

### Scheduling Framework
- **Background Processing**: Thread-based scheduler for continuous operation
- **Configurable Intervals**: Adjustable check frequencies via environment variables
- **Graceful Shutdown**: Clean stop mechanisms with proper resource cleanup

## Configuration Management
- **Environment-Based**: All sensitive data and settings managed through environment variables
- **Validation Layer**: Startup validation to ensure required configuration is present
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
- API keys required for Lever, Greenhouse, Slack, and Airtable services
- Token-based authentication for all external service integrations
- Environment variable configuration for secure credential management