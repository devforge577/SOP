"""Flask web server for health checks and API endpoints."""
import os
from flask import Flask, jsonify
from database.db import get_connection
from config import config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load configuration
app.config.from_object(config[os.getenv('FLASK_ENV', 'development')])


@app.route('/health')
def health_check():
    """Basic health check endpoint."""
    try:
        # Test database connection
        conn = get_connection()
        cursor = conn.cursor()

        # Test basic connectivity
        cursor.execute("SELECT 1")
        cursor.fetchone()

        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_table = cursor.fetchone()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        products_table = cursor.fetchone()

        conn.close()

        status = 'healthy' if users_table and products_table else 'degraded'
        db_status = 'initialized' if users_table and products_table else 'uninitialized'

        return jsonify({
            'status': status,
            'database': db_status,
            'timestamp': '2024-01-01T00:00:00Z'  # Would use datetime in real implementation
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500


@app.route('/api/v1/status')
def system_status():
    """Detailed system status endpoint."""
    try:
        # Database status
        db_status = 'healthy'
        user_count = 0
        product_count = 0

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM products")
                product_count = cursor.fetchone()[0]

            conn.close()
        except Exception as e:
            db_status = f'error: {str(e)}'

        return jsonify({
            'status': 'operational' if db_status == 'healthy' else 'degraded',
            'components': {
                'database': db_status,
                'web_server': 'healthy'
            },
            'metrics': {
                'users_count': user_count,
                'products_count': product_count
            },
            'version': '1.0.0'
        }), 200

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/v1/products')
def get_products_api():
    """API endpoint to get products (read-only)."""
    try:
        from modules.products import get_all_products
        products = get_all_products()

        return jsonify({
            'products': products,
            'count': len(products)
        }), 200

    except Exception as e:
        logger.error(f"Products API failed: {e}")
        return jsonify({
            'error': 'Failed to retrieve products',
            'details': str(e)
        }), 500


if __name__ == '__main__':
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )