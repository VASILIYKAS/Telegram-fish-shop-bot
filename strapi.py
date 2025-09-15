import os

import requests
from dotenv import load_dotenv
from io import BytesIO


load_dotenv()


def get_products():
    headers = {
        'Authorization': f'Bearer {os.getenv("STRAPI_TOKEN")}'
    }
    
    try:
        response = requests.get(
            'http://localhost:1337/api/products?populate=*',
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            products = response.json()['data']
            return products
        else:
            print(f'Error response: {response.text}')
            return []
            
    except Exception as e:
        print(f'Request error: {e}')
        return []


def get_cart_contents(cart_document_id: str) -> dict:
    url = (
        f'http://localhost:1337/api/carts'
        f'?filters[documentId][$eq]={cart_document_id}'
        f'&populate[cart_items][populate][product][populate][picture]=true'
    )
    headers = {
        'Authorization': f'Bearer {os.getenv("STRAPI_TOKEN")}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        carts = response.json()['data']
        return carts[0] if carts else None
    except requests.exceptions.RequestException as e:
        print(f'Ошибка при получении содержимого корзины: {e}')
        return None
    
    
def get_or_create_cart(chat_id: int):
    url = f'http://localhost:1337/api/carts?filters[chat_id][$eq]={chat_id}'
    headers = {
        'Authorization': f'Bearer {os.getenv("STRAPI_TOKEN")}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        carts = response.json().get('data', [])

        if carts:
            return carts[0]
        else:
            create_url = 'http://localhost:1337/api/carts'
            paylaod = {'data': {'chat_id': str(chat_id)}}
            create_response = requests.post(create_url, json=paylaod, headers=headers)
            create_response.raise_for_status()
            created_cart = create_response.json().get("data")
            return created_cart

    except Exception as e:
        print(f'Ошибка при получении или создании корзины: {e}')
        return None


def get_product_image(product: dict):
    if not product.get('picture'):
        return None
    
    img_url = 'http://localhost:1337' + product['picture'][0]['url']
    try:
        response = requests.get(img_url)
        response.raise_for_status()
        image_bytes = BytesIO(response.content)
        image_bytes.name = product['picture'][0]['name']
        return image_bytes
    except Exception as e:
        print(f'Ошибка при загрузке картинки: {e}')
        return None
    
    
def add_product_to_cart(cart_document_id: str, product_document_id: str, quantity: int = 1):
    url = 'http://localhost:1337/api/cart-items'
    headers = {
        'Authorization': f'Bearer {os.getenv("STRAPI_TOKEN")}',
        "Content-Type": "application/json"
    }
    paylaod = {
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
    
    response = requests.post(url, headers=headers, json=paylaod)
    
    if response.status_code == 200 or response.status_code == 201:
        return response.json()
    else:
        print("Ошибка при добавлении:", response.status_code, response.text)
        return None
    
    
def clear_cart(cart_document_id: str) -> bool:
    headers = {
        'Authorization': f'Bearer {os.getenv("STRAPI_TOKEN")}',
        'Content-Type': 'application/json'
    }
    try:
        url = f"http://localhost:1337/api/cart-items?filters[cart][documentId][$eq]={cart_document_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        cart_items = response.json()['data']
        
        disconnect_ids = [{'documentId': item['documentId']} for item in cart_items]

        put_url = f"http://localhost:1337/api/carts/{cart_document_id}"
        data = {
            "data": {
                "cart_items": {
                    "disconnect": disconnect_ids
                }
            }
        }
        put_response = requests.put(put_url, json=data, headers=headers)
        put_response.raise_for_status()
        
        return True
    except Exception as e:
        print(f"Ошибка при очистке корзины: {e}")
        return False
    

def create_client(email: str) -> dict:
    headers = {
        'Authorization': f'Bearer {os.getenv("STRAPI_TOKEN")}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get(
            f'http://localhost:1337/api/clients?filters[email][$eq]={email}',
            headers=headers
        )
        response.raise_for_status()
        clients = response.json()['data']
        if clients:
            return clients[0]
    except Exception as e:
        print(f"Ошибка при проверке клиента: {e}")

    data = {
        'data': {
            'email': email
        }
    }
    try:
        response = requests.post('http://localhost:1337/api/clients', json=data, headers=headers)
        response.raise_for_status()
        return response.json()['data']
        
    except Exception as e:
        print(f"Ошибка при создании клиента: {e}")
        return None