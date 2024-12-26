from app.agency_admin.agency_endpoint import AgencyEndpoint


def test_create_product(app_config):
    endpoint = AgencyEndpoint()
    product_data = {"name": "Test Product", "price": 10000}
    response = endpoint.create_product(product_data)
    assert response.status_code == 200
