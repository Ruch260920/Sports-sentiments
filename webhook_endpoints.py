#!/usr/bin/env python3
"""
Webhook Endpoints
Handles incoming webhooks from twitterapi.io and other services
"""

from flask import Flask, request, jsonify
from celery import chain
import json
import logging
from datetime import datetime
from tasks.twitter_tasks import process_twitter_webhook, analyze_tweet
from services.twitter_webhook_service import TwitterWebhookService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app for webhook endpoints
webhook_app = Flask(__name__)

# Initialize Twitter service
twitter_service = TwitterWebhookService()

@webhook_app.route('/webhook/twitter/<username>', methods=['POST'])
def twitter_webhook(username):
    """
    Handle incoming Twitter webhooks from twitterapi.io
    
    Args:
        username (str): Twitter username from URL path
        
    Returns:
        JSON response indicating success/failure
    """
    try:
        # Log incoming webhook
        logger.info(f"Received Twitter webhook for @{username}")
        
        # Get the webhook payload
        payload = request.get_json()
        
        if not payload:
            logger.error("No JSON payload received")
            return jsonify({'error': 'No JSON payload'}), 400
        
        # Log payload structure for debugging
        logger.info(f"Webhook payload keys: {list(payload.keys())}")
        
        # Process the webhook asynchronously using Celery
        # This ensures the webhook response is quick
        task = process_twitter_webhook.delay(payload)
        
        logger.info(f"Webhook processing task started: {task.id}")
        
        # Return success immediately
        return jsonify({
            'status': 'success',
            'message': 'Webhook received and queued for processing',
            'task_id': task.id,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing Twitter webhook: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@webhook_app.route('/webhook/twitter/health', methods=['GET'])
def twitter_webhook_health():
    """
    Health check endpoint for Twitter webhooks
    
    Returns:
        JSON response with webhook health status
    """
    try:
        # Get webhook health information
        webhooks = twitter_service.list_webhooks()
        
        # Count active webhooks
        active_count = len([w for w in webhooks if w.get('is_active', False)])
        
        health_status = {
            'status': 'healthy',
            'total_webhooks': len(webhooks),
            'active_webhooks': active_count,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check for problematic webhooks
        problematic_webhooks = [w for w in webhooks if w.get('failure_count', 0) >= 5]
        if problematic_webhooks:
            health_status['status'] = 'warning'
            health_status['problematic_webhooks'] = len(problematic_webhooks)
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Error checking webhook health: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@webhook_app.route('/webhook/twitter/test', methods=['POST'])
def test_twitter_webhook():
    """
    Test endpoint for simulating Twitter webhook payloads
    
    Returns:
        JSON response with test results
    """
    try:
        # Get test payload
        payload = request.get_json()
        
        if not payload:
            # Create a sample test payload
            payload = {
                'data': {
                    'id': 'test_tweet_123',
                    'text': 'This is a test tweet for testing purposes',
                    'author_id': {
                        'username': 'testuser',
                        'id': '123456789'
                    },
                    'created_at': datetime.now().isoformat(),
                    'public_metrics': {
                        'retweet_count': 0,
                        'like_count': 0,
                        'reply_count': 0,
                        'quote_count': 0
                    },
                    'referenced_tweets': []
                }
            }
        
        # Process the test payload
        result = twitter_service.process_webhook_payload(payload)
        
        return jsonify({
            'status': 'success',
            'test_result': result,
            'message': 'Test webhook processed successfully',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing test webhook: {e}")
        return jsonify({
            'error': 'Test failed',
            'message': str(e)
        }), 500

@webhook_app.route('/webhook/twitter/manage', methods=['POST'])
def manage_twitter_webhook():
    """
    Manage Twitter webhook subscriptions (create/delete)
    
    Expected payload:
    {
        "action": "create" | "delete",
        "target_username": "username",
        "target_user_id": "user_id",
        "events": ["tweet"]  # optional
    }
    
    Returns:
        JSON response with operation result
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON payload'}), 400
        
        action = data.get('action')
        target_username = data.get('target_username')
        target_user_id = data.get('target_user_id')
        events = data.get('events', ['tweet'])
        
        if not all([action, target_username, target_user_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if action not in ['create', 'delete']:
            return jsonify({'error': 'Invalid action. Use "create" or "delete"'}), 400
        
        # Perform the requested action
        if action == 'create':
            result = twitter_service.create_webhook(target_username, target_user_id, events)
        else:  # delete
            # For delete, we need the webhook_id
            webhook_id = data.get('webhook_id')
            if not webhook_id:
                return jsonify({'error': 'webhook_id required for delete action'}), 400
            result = twitter_service.delete_webhook(webhook_id)
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error managing webhook: {e}")
        return jsonify({
            'error': 'Operation failed',
            'message': str(e)
        }), 500

@webhook_app.route('/webhook/twitter/list', methods=['GET'])
def list_twitter_webhooks():
    """
    List all active Twitter webhook subscriptions
    
    Returns:
        JSON response with list of webhooks
    """
    try:
        webhooks = twitter_service.list_webhooks()
        
        return jsonify({
            'status': 'success',
            'webhooks': webhooks,
            'count': len(webhooks),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        return jsonify({
            'error': 'Failed to list webhooks',
            'message': str(e)
        }), 500

# Error handlers
@webhook_app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@webhook_app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Run the webhook server
    webhook_app.run(debug=True, host='0.0.0.0', port=5001) 