# Automated Job Application System

An intelligent job application automation system that monitors job postings from multiple sources, matches them against resume profiles using keyword analysis, and sends notifications through Slack.

## Features

- **Multi-Source Job Fetching**: Automatically retrieves job postings from Lever and Greenhouse APIs
- **Intelligent Matching**: Uses keyword analysis to match jobs against predefined resume profiles
- **Smart Notifications**: Sends detailed Slack notifications for jobs with 80%+ match scores
- **Airtable Integration**: Stores matched jobs for tracking and application management
- **Duplicate Prevention**: Avoids reprocessing the same jobs using local storage
- **Automated Scheduling**: Runs every 15 minutes with configurable intervals
- **Comprehensive Logging**: Detailed logging for monitoring and debugging

## Quick Start

1. **Set up your environment variables** (see Configuration section below)
2. **Run the system**: `python main.py`
3. **Monitor notifications** in your configured Slack channel

The system will automatically:
- Check for new jobs every 15 minutes
- Match jobs against your resume profiles
- Send Slack notifications for good matches (80%+ score)
- Store matched jobs in Airtable for tracking

## Configuration

Set these environment variables in your Replit Secrets:

### Required
- `SLACK_BOT_TOKEN`: Your Slack bot token
- `SLACK_CHANNEL_ID`: Slack channel ID for notifications
- `AIRTABLE_API_KEY`: Your Airtable API key
- `AIRTABLE_BASE_ID`: Your Airtable base ID

### Optional
- `TARGET_COMPANIES`: No longer required - system now fetches all available jobs
- `MATCH_THRESHOLD`: Minimum match score for notifications (default: 80.0)
- `CHECK_INTERVAL_MINUTES`: How often to check for jobs (default: 15)
- `AIRTABLE_TABLE_NAME`: Airtable table name (default: "Job Applications")
- `LOG_LEVEL`: Logging level (default: "INFO")

## Resume Profiles

The system includes three specialized resume profiles:

### Resume A: Platform Infrastructure
Keywords include: platform, infrastructure, microservices, api, scalability, aws, kubernetes, data, analytics, technical product, cloud, ci/cd, observability, cross-functional

### Resume B: Developer Tools & Observability  
Keywords include: developer tools, observability, devops, monitoring, alerting, instrumentation, platform engineering, internal tools, logging, on-call, incident, runbooks

### Resume C: Billing & Revenue Platform
Keywords include: billing, pricing, monetization, payments, revenue, invoicing, payment processor, checkout, stripe, subscription, fintech, business model

### Custom Profiles
Add custom profiles by setting the `RESUME_PROFILES` environment variable with JSON format:

```json
{
  "Custom_Profile": {
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "description": "Description of this profile"
  }
}
```

## API Setup

### Slack Bot Setup
1. Go to https://api.slack.com/apps
2. Create a new app for your workspace
3. Add OAuth permissions: `chat:write`, `channels:read`
4. Install the app to your workspace
5. Copy the Bot User OAuth Token as `SLACK_BOT_TOKEN`
6. Get your channel ID by right-clicking the channel and copying the link

### Airtable Setup
1. Create a new base in Airtable
2. Create a table called "Job Applications" (or set custom name in `AIRTABLE_TABLE_NAME`)
3. Get your API key from https://airtable.com/account
4. Get your base ID from the base URL

## Architecture

```
job-application-system/
├── api_clients/          # API integration modules
│   ├── lever_client.py   # Lever API client
│   ├── greenhouse_client.py # Greenhouse API client
│   ├── slack_client.py   # Slack notifications
│   └── airtable_client.py # Airtable storage
├── matching/             # Job matching engine
│   ├── keyword_matcher.py # Keyword matching logic
│   └── resume_profiles.py # Resume profile definitions
├── storage/              # Data storage
│   └── job_storage.py    # Job deduplication
├── utils/                # Utilities
│   └── logger.py         # Logging configuration
├── main.py               # Main application
├── config.py             # Configuration management
└── scheduler.py          # Job scheduling
```

## Monitoring

The system provides comprehensive logging:
- Console output for real-time monitoring
- Log file (`job_application_system.log`) for historical data
- Slack status messages for system events

## Customization

### Adding New Job Sources
1. Create a new client in `api_clients/`
2. Implement the `fetch_jobs()` method
3. Add to the main job fetching loop in `main.py`

### Custom Matching Logic
Modify `matching/keyword_matcher.py` to implement:
- Different scoring algorithms
- Additional matching criteria
- Industry-specific keyword weighting

### Notification Formats
Customize Slack message formatting in `api_clients/slack_client.py`

## Troubleshooting

### Common Issues
- **404 errors**: Some companies don't use public APIs - this is normal
- **Authentication errors**: Verify your API keys are correct
- **No jobs found**: Check that target companies use Lever/Greenhouse
- **Low match scores**: Review and update your resume profile keywords

### Debugging
- Check the log file for detailed error information
- Use `LOG_LEVEL=DEBUG` for verbose logging
- Monitor the console output for real-time status

## Support

For issues or questions:
1. Check the log files for error details
2. Verify all environment variables are set correctly
3. Ensure API keys have proper permissions
4. Review the company names in `TARGET_COMPANIES`