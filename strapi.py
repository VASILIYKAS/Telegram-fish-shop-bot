import requests
from io import BytesIO


def get_products(strapi_token, base_url):
    url = f'{base_url}api/products'
    headers = {
        'Authorization': f'Bearer {strapi_token}'
    }
    
    response = requests.get(
        url,
        headers=headers,
        params={'populate': '*'},
        timeout=10
    )
    if response.status_code == 200:
        products = response.json()['data']
        return products
    else:
        return []


def get_cart_contents(cart_document_id: str, strapi_token, base_url):
    url = f'{base_url}api/carts'
    headers = {
        'Authorization': f'Bearer {strapi_token}',
        'Content-Type': 'application/json'
    }
    params = {
        'filters[documentId][$eq]': cart_document_id,
        'populate[cart_items][populate][product][populate][picture]': 'true'
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    carts = response.json()['data']
    return carts[0] if carts else None
    
    
def get_or_create_cart(chat_id: int, strapi_token, base_url):
    url = f'{base_url}api/carts'
    headers = {
        'Authorization': f'Bearer {strapi_token}',
        'Content-Type': 'application/json'
    }
    params = {'filters[chat_id][$eq]': chat_id}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    carts = response.json().get('data', [])

    if carts:
        return carts[0]
    
    create_url = f'{base_url}api/carts'
    paylaod = {'data': {'chat_id': str(chat_id)}}
    create_response = requests.post(create_url, json=paylaod, headers=headers)
    create_response.raise_for_status()
    created_cart = create_response.json().get('data')
    return created_cart



def get_product_image(product: dict, base_url):
    if not product.get('picture'):
        return None
    
    img_url = base_url + product['picture'][0]['url']

    response = requests.get(img_url)
    response.raise_for_status()
    image_bytes = BytesIO(response.content)
    image_bytes.name = product['picture'][0]['name']
    return image_bytes
    
    
def add_product_to_cart(cart_document_id: str, product_document_id: str, strapi_token, base_url, quantity: int = 1):
    url = f'{base_url}api/cart-items'
    headers = {
        'Authorization': f'Bearer {strapi_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'data': {
            'quantity': quantity,
            'cart': {
                'connect': [{'documentId': cart_document_id}]
            },
            'product': {
                'connect': [{'documentId': product_document_id}]
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json().get('data')
    
    
def clear_cart(cart_document_id: str, strapi_token, base_url) -> bool:
    url = f'{base_url}api/cart-items'

    headers = {
        'Authorization': f'Bearer {strapi_token}',
        'Content-Type': 'application/json'
    }
    params = {
        'filters[cart][documentId][$eq]': cart_document_id
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    cart_items = response.json()['data']
    
    disconnect_ids = [{'documentId': item['documentId']} for item in cart_items]

    put_url = f'{base_url}api/carts/{cart_document_id}'
    payload = {
        'data': {
            'cart_items': {
                'disconnect': disconnect_ids
            }
        }
    }
    put_response = requests.put(put_url, json=payload, headers=headers)
    put_response.raise_for_status()
    
    return True
    

def create_client(email: str, strapi_token, base_url) -> dict:
    url = f'{base_url}api/clients'
    headers = {
        'Authorization': f'Bearer {strapi_token}',
        'Content-Type': 'application/json'
    }
    params = {'filters[email][$eq]': email}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    clients = response.json()['data']
    if clients:
        return clients[0]

    payload = {
        'data': {
            'email': email
        }
    }
    
    response = requests.post(f'{base_url}api/clients', json=payload, headers=headers)
    response.raise_for_status()
    return response.json()['data']