#!/usr/bin/env python3
"""
Flask server to handle Slack Events API webhooks for reaction tracking.
"""

import logging
from flask import Flask, request, jsonify
from api_clients.slack_event_handler import SlackEventHandler
from utils.logger import setup_logger


app = Flask(__name__)
logger = setup_logger()

# Initialize event handler
try:
    event_handler = SlackEventHandler()
except Exception as e:
    logger.warning(f"Failed to initialize SlackEventHandler: {e}")
    event_handler = None


@app.route('/slack/events', methods=['POST'])
def slack_events():
    """Handle incoming Slack events."""
    try:
        data = request.get_json()
        
        # Handle URL verification challenge
        if data.get('type') == 'url_verification':
            return jsonify({'challenge': data.get('challenge')})
        
        # Handle event callbacks
        if data.get('type') == 'event_callback':
            if not event_handler:
                logger.warning("Event handler not initialized, skipping event processing")
                return jsonify({'status': 'ok'}), 200
            
            event = data.get('event', {})
            event_type = event.get('type')
            
            if event_type == 'reaction_added':
                logger.info(f"Processing reaction_added event: {event.get('reaction', 'unknown')}")
                success = event_handler.handle_reaction_added(event)
                
                if success:
                    logger.info("Reaction processed successfully")
                else:
                    logger.warning("Reaction processing failed or was ignored")
        
        # Always return 200 to acknowledge receipt
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.error(f"Error handling Slack event: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'slack-events-server'}), 200


@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    return jsonify({
        'service': 'Job Application Slack Events Server',
        'status': 'running',
        'endpoints': {
            'events': '/slack/events',
            'health': '/health'
        }
    }), 200


if __name__ == '__main__':
    logger.info("Starting Slack Events Server")
    app.run(host='0.0.0.0', port=5000, debug=False)