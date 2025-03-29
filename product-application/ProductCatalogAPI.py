# ProductCatalogAPI.py
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from datetime import datetime
import sys
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./product_catalog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Product(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Float, nullable=False)
    category = Column(String(50))
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'is_available': self.is_available,
            'created_at': self.created_at.isoformat()
        }

with app.app_context():
    db.create_all()

@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    if not data or 'name' not in data or 'price' not in data:
        logger.warning("Invalid product creation request.")
        return jsonify({'error': 'Name and price are required'}), 400

    try:
        new_product = Product(
            name=data['name'],
            description=data.get('description'),
            price=data['price'],
            category=data.get('category'),
            is_available=data.get('is_available', True)  # Default to True
        )
        db.session.add(new_product)
        db.session.commit()
        logger.info(f"Product created: {new_product.id}")
        return jsonify(new_product.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/products', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
        return jsonify([product.to_dict() for product in products])
    except Exception as e:
        logger.error(f"Error retrieving products: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            logger.warning(f"Product not found: {product_id}")
            return jsonify({'error': 'Product not found'}), 404
        return jsonify(product.to_dict())
    except Exception as e:
        logger.error(f"Error retrieving product {product_id}: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            logger.warning(f"Product not found: {product_id}")
            return jsonify({'error': 'Product not found'}), 404
        data = request.get_json()
        if not data:
            logger.warning("Invalid product update request.")
            return jsonify({'error': 'Invalid data'}), 400

        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
        if 'category' in data:
            product.category = data['category']
        if 'is_available' in data:
          product.is_available = data['is_available']

        db.session.commit()
        logger.info(f"Product updated: {product_id}")
        return jsonify(product.to_dict())
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            logger.warning(f"Product not found: {product_id}")
            return jsonify({'error': 'Product not found'}), 404
        db.session.delete(product)
        db.session.commit()
        logger.info(f"Product deleted: {product_id}")
        return jsonify({'message': 'Product deleted'}), 200
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/products/search', methods=['GET'])
def search_products():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    try:
        results = Product.query.filter(Product.name.ilike(f"%{query}%")).all()
        return jsonify([product.to_dict() for product in results])
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/test/headers', methods=['GET'])
def test_headers():
    headers = dict(request.headers)
    return jsonify(headers)

@app.route('/test/status/<int:code>', methods=['GET'])
def test_status(code):
    return make_response(jsonify({'message': f'Status code {code}'}), code)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error starting the application: {e}")
        sys.exit(1)
