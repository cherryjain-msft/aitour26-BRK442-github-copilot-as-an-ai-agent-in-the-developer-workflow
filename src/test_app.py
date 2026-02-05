import pytest
import json
from app import app, data


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    # Clear data before each test to ensure clean state
    data.clear()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_product():
    """Sample product data for testing"""
    return {
        'name': 'Test Product',
        'description': 'This is a test product'
    }


def test_get_products_empty(client):
    """Test getting products when store is empty"""
    response = client.get('/products')
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_product(client, sample_product):
    """Test creating a new product"""
    response = client.post('/products',
                          data=json.dumps(sample_product),
                          content_type='application/json')
    assert response.status_code == 201
    product = response.get_json()
    assert 'id' in product
    assert product['name'] == sample_product['name']
    assert product['description'] == sample_product['description']


def test_create_product_without_name(client):
    """Test creating a product without required name field"""
    response = client.post('/products',
                          data=json.dumps({'description': 'No name'}),
                          content_type='application/json')
    assert response.status_code == 400


def test_create_product_without_body(client):
    """Test creating a product without request body"""
    response = client.post('/products',
                          data=json.dumps({}),
                          content_type='application/json')
    assert response.status_code == 400


def test_get_products_with_data(client, sample_product):
    """Test getting all products when store has data"""
    # Create a product first
    client.post('/products',
               data=json.dumps(sample_product),
               content_type='application/json')
    
    # Get all products
    response = client.get('/products')
    assert response.status_code == 200
    products = response.get_json()
    assert len(products) == 1
    assert products[0]['name'] == sample_product['name']


def test_get_product_by_id(client, sample_product):
    """Test getting a specific product by ID"""
    # Create a product first
    create_response = client.post('/products',
                                  data=json.dumps(sample_product),
                                  content_type='application/json')
    product = create_response.get_json()
    product_id = product['id']
    
    # Get the product by ID
    response = client.get(f'/products/{product_id}')
    assert response.status_code == 200
    retrieved_product = response.get_json()
    assert retrieved_product['id'] == product_id
    assert retrieved_product['name'] == sample_product['name']


def test_get_nonexistent_product(client):
    """Test getting a product that doesn't exist"""
    response = client.get('/products/nonexistent-id')
    assert response.status_code == 404


def test_update_product(client, sample_product):
    """Test updating an existing product"""
    # Create a product first
    create_response = client.post('/products',
                                  data=json.dumps(sample_product),
                                  content_type='application/json')
    product = create_response.get_json()
    product_id = product['id']
    
    # Update the product
    updated_data = {
        'name': 'Updated Product',
        'description': 'Updated description'
    }
    response = client.put(f'/products/{product_id}',
                         data=json.dumps(updated_data),
                         content_type='application/json')
    assert response.status_code == 200
    updated_product = response.get_json()
    assert updated_product['name'] == updated_data['name']
    assert updated_product['description'] == updated_data['description']


def test_update_nonexistent_product(client):
    """Test updating a product that doesn't exist"""
    response = client.put('/products/nonexistent-id',
                         data=json.dumps({'name': 'Test'}),
                         content_type='application/json')
    assert response.status_code == 404


def test_update_product_without_name(client, sample_product):
    """Test updating a product without required name field"""
    # Create a product first
    create_response = client.post('/products',
                                  data=json.dumps(sample_product),
                                  content_type='application/json')
    product = create_response.get_json()
    product_id = product['id']
    
    # Try to update without name
    response = client.put(f'/products/{product_id}',
                         data=json.dumps({'description': 'Only description'}),
                         content_type='application/json')
    assert response.status_code == 400


def test_delete_product(client, sample_product):
    """Test deleting an existing product"""
    # Create a product first
    create_response = client.post('/products',
                                  data=json.dumps(sample_product),
                                  content_type='application/json')
    product = create_response.get_json()
    product_id = product['id']
    
    # Delete the product
    response = client.delete(f'/products/{product_id}')
    assert response.status_code == 204
    
    # Verify product is deleted
    get_response = client.get(f'/products/{product_id}')
    assert get_response.status_code == 404


def test_delete_nonexistent_product(client):
    """Test deleting a product that doesn't exist"""
    response = client.delete('/products/nonexistent-id')
    assert response.status_code == 404


def test_product_description_optional(client):
    """Test creating a product without description (optional field)"""
    product_data = {'name': 'Product Without Description'}
    response = client.post('/products',
                          data=json.dumps(product_data),
                          content_type='application/json')
    assert response.status_code == 201
    product = response.get_json()
    assert product['name'] == product_data['name']
    assert product['description'] == ''  # Should default to empty string


def test_multiple_products_crud(client):
    """Test CRUD operations with multiple products"""
    # Create multiple products
    products = [
        {'name': 'Product 1', 'description': 'Description 1'},
        {'name': 'Product 2', 'description': 'Description 2'},
        {'name': 'Product 3', 'description': 'Description 3'}
    ]
    
    created_ids = []
    for product in products:
        response = client.post('/products',
                             data=json.dumps(product),
                             content_type='application/json')
        assert response.status_code == 201
        created_ids.append(response.get_json()['id'])
    
    # Get all products
    response = client.get('/products')
    assert response.status_code == 200
    all_products = response.get_json()
    assert len(all_products) == 3
    
    # Delete one product
    response = client.delete(f'/products/{created_ids[1]}')
    assert response.status_code == 204
    
    # Verify only 2 products remain
    response = client.get('/products')
    assert response.status_code == 200
    remaining_products = response.get_json()
    assert len(remaining_products) == 2