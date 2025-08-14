# Slack Events API Setup for ✅ React-to-Track Feature

This guide will help you set up Slack Events API to enable automatic job application tracking when users react with ✅ to job notifications.

## 🔧 Quick Setup Steps

### 1. **Get Your Replit App URL**
Your Slack Events Server is running at: `https://<your-repl-name>.<your-username>.repl.co`

### 2. **Configure Slack App Events**

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Select your existing Slack app (the one with your bot token)
3. Navigate to **"Event Subscriptions"** in the left sidebar
4. **Enable Events**: Toggle "Enable Events" to ON
5. **Request URL**: Enter your Replit URL + `/slack/events`
   ```
   https://<your-repl-name>.<your-username>.repl.co/slack/events
   ```
6. **Verify URL**: Slack will send a challenge request to verify the endpoint

### 3. **Subscribe to Bot Events**

In the "Subscribe to bot events" section, add:
- `reaction_added` - When users add reactions to messages

### 4. **Set OAuth Scopes** 

Go to **"OAuth & Permissions"** and ensure these scopes are enabled:
- `chat:write` (already configured for sending messages)
- `reactions:read` (to read reactions on messages)
- `channels:history` (to read message content)

### 5. **Reinstall App to Workspace**

After adding new scopes, you'll need to reinstall the app:
1. Click **"Install to Workspace"** 
2. Approve the new permissions

## 🎯 How It Works

Once configured, the system will:

1. **Listen for ✅ reactions** on job notification messages
2. **Extract job details** from the formatted message:
   - Company name
   - Job title  
   - Match score
   - Resume used
   - Job URL
   - Location
3. **Log to Airtable** with these fields:
   - Company
   - Title
   - Applied Date (current UTC time)
   - Resume Used
   - Match Score
   - Job Link
   - Source (Lever/Greenhouse)
   - Status = "Applied"
4. **Add confirmation ✔️** reaction to show it was logged
5. **Prevent duplicates** using job URL as deduplication key

## 📋 Testing

1. Send a test job notification (already done)
2. React with ✅ to the message
3. Check for ✔️ confirmation reaction
4. Verify new record appears in your Airtable

## 🚨 Troubleshooting

- **URL verification fails**: Make sure the Slack Events Server is running
- **No reactions detected**: Check bot has `reactions:read` scope
- **Can't read messages**: Verify `channels:history` scope is enabled
- **Airtable errors**: Check API key and base permissions

## 🔗 Endpoints

- **Events**: `/slack/events` - Slack webhook endpoint
- **Health**: `/health` - Server status check
- **Root**: `/` - Server information

Your react-to-track feature is ready once Slack Events API is configured!