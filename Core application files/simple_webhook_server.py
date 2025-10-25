#!/usr/bin/env python3
"""
Simple Twitter Webhook Server
Minimal webhook server for testing Twitter webhook functionality
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Simple in-memory storage for testing
webhook_data = []
tweet_data = []

@app.route('/webhook/twitter/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Twitter Webhook Server',
        'version': '1.0.0'
    })

@app.route('/webhook/twitter/receive', methods=['POST'])
def receive_webhook():
    """Receive Twitter webhook payloads"""
    try:
        # Get the webhook payload
        payload = request.get_json()
        
        if not payload:
            raise BadRequest("No JSON payload received")
        
        logger.info(f"Received webhook payload: {json.dumps(payload, indent=2)}")
        
        # Store the payload for testing
        webhook_data.append({
            'timestamp': datetime.now().isoformat(),
            'payload': payload
        })
        
        # Extract tweet information
        if 'data' in payload:
            tweet_info = payload['data']
            tweet_data.append({
                'id': tweet_info.get('id'),
                'text': tweet_info.get('text'),
                'author': tweet_info.get('author_id', {}).get('username'),
                'created_at': tweet_info.get('created_at'),
                'metrics': tweet_info.get('public_metrics', {}),
                'received_at': datetime.now().isoformat()
            })
            
            logger.info(f"Processed tweet: {tweet_info.get('id')} from @{tweet_info.get('author_id', {}).get('username')}")
        
        # Return success immediately (webhook best practice)
        return jsonify({
            'status': 'success',
            'message': 'Webhook received and processed',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except BadRequest as e:
        logger.error(f"Bad request: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@app.route('/webhook/twitter/test', methods=['GET'])
def test_webhook():
    """Test endpoint to simulate webhook data"""
    return jsonify({
        'status': 'success',
        'message': 'Test endpoint working',
        'webhooks_received': len(webhook_data),
        'tweets_processed': len(tweet_data),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/webhook/twitter/data', methods=['GET'])
def get_webhook_data():
    """Get all received webhook data"""
    return jsonify({
        'webhooks': webhook_data,
        'tweets': tweet_data,
        'counts': {
            'webhooks': len(webhook_data),
            'tweets': len(tweet_data)
        }
    })

@app.route('/webhook/twitter/simulate', methods=['POST'])
def simulate_webhook():
    """Simulate a webhook payload for testing"""
    try:
        # Create a sample webhook payload
        sample_payload = {
            'data': {
                'id': f'sim_tweet_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'text': 'This is a simulated tweet for testing the webhook system! #Test #Webhook',
                'author_id': {
                    'username': 'TestUser',
                    'id': '999999999'
                },
                'created_at': datetime.now().isoformat(),
                'public_metrics': {
                    'retweet_count': 5,
                    'like_count': 25,
                    'reply_count': 3,
                    'quote_count': 1
                },
                'referenced_tweets': []
            }
        }
        
        # Process it as if it were a real webhook
        webhook_data.append({
            'timestamp': datetime.now().isoformat(),
            'payload': sample_payload,
            'simulated': True
        })
        
        tweet_data.append({
            'id': sample_payload['data']['id'],
            'text': sample_payload['data']['text'],
            'author': sample_payload['data']['author_id']['username'],
            'created_at': sample_payload['data']['created_at'],
            'metrics': sample_payload['data']['public_metrics'],
            'received_at': datetime.now().isoformat(),
            'simulated': True
        })
        
        return jsonify({
            'status': 'success',
            'message': 'Simulated webhook processed',
            'tweet_id': sample_payload['data']['id'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error simulating webhook: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Simple Twitter Webhook Server...")
    print("📍 Server will run on http://localhost:5001")
    print("🔗 Available endpoints:")
    print("   GET  /webhook/twitter/health     - Health check")
    print("   POST /webhook/twitter/receive    - Receive webhooks")
    print("   GET  /webhook/twitter/test       - Test endpoint")
    print("   GET  /webhook/twitter/data       - View received data")
    print("   POST /webhook/twitter/simulate   - Simulate webhook")
    print("")
    print("💡 To test, send a POST request to /webhook/twitter/receive")
    print("   or use /webhook/twitter/simulate to generate test data")
    print("")
    
    app.run(host='0.0.0.0', port=5001, debug=True) 