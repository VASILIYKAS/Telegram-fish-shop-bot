import logging
import os

import redis
from dotenv import load_dotenv
from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    ParseMode,
    Update,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)
from strapi import (
    add_product_to_cart,
    clear_cart,
    create_client,
    get_cart_contents,
    get_or_create_cart,
    get_product_image,
    get_products,
)


def set_menu_commands(bot):
    commands = [
        BotCommand('start', 'Запустить бота'),
    ]
    bot.set_my_commands(commands)
    

def show_menu(update: Update, context: CallbackContext) -> str:
    strapi_token = context.bot_data["STRAPI_TOKEN"]
    products = get_products(strapi_token)
    keyboard = []

    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=product['title'],
                callback_data=product['documentId']
            )
        ])

    keyboard.append([
        InlineKeyboardButton('Моя корзина', callback_data='SHOW_CART')
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        update.effective_message.reply_text('Выберите товар:', reply_markup=reply_markup)
    else:
        update.message.reply_text('Выберите товар:', reply_markup=reply_markup)

    return 'HANDLE_MENU'


def show_cart(update: Update, context: CallbackContext) -> str:
    strapi_token = context.bot_data["STRAPI_TOKEN"]
    query = update.callback_query
    chat_id = query.message.chat_id if query else update.message.chat_id

    cart = get_or_create_cart(chat_id, strapi_token)
    if not cart or 'documentId' not in cart:
        message = 'Корзина пуста или не удалось её получить.'
        if query:
            query.answer(message)
            query.message.reply_text(message)
        else:
            update.message.reply_text(message)
        return 'HANDLE_MENU'

    cart_document_id = cart['documentId']
    cart_data = get_cart_contents(cart_document_id, strapi_token)
    
    if not cart_data or not cart_data.get('cart_items'):
        message = 'Ваша корзина пуста.'
        if query:
            query.answer(message)
            query.message.reply_text(message)
        else:
            update.message.reply_text(message)
        return 'HANDLE_MENU'

    total_price = 0
    cart_text = '*Содержимое корзины:*\n\n'
    for item in cart_data['cart_items']:
        product = item.get('product', {})
        if not product:
            continue
        title = product.get('title', 'Неизвестный товар')
        quantity = item.get('quantity', 1)
        price = product.get('price', 0)
        item_total = price * quantity
        total_price += item_total
        cart_text += f'- {title} ({quantity} шт.) - {item_total} руб.\n'

    cart_text += f'\n*Итого:* {total_price} руб.'

    keyboard = [
        [InlineKeyboardButton('Назад в меню', callback_data='BACK_TO_MENU')],
        [InlineKeyboardButton('Очистить корзину', callback_data='CLEAR_CART')],
        [InlineKeyboardButton('Оплатить', callback_data='PAY')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        query.answer()
        query.message.reply_text(cart_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        update.message.reply_text(cart_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    return 'HANDLE_CART'


def show_product(update: Update, context: CallbackContext, product_document_id: str) -> str:
    strapi_token = context.bot_data["STRAPI_TOKEN"]
    query = update.callback_query
    products = get_products(strapi_token)
    product = next((p for p in products if p['documentId'] == product_document_id), None)
    
    if not product:
        query.message.reply_text('Товар не найден.')
        return 'HANDLE_MENU'

    title = product['title']
    description = product['description']
    price = product['price']

    text = f'*{title}*\n\n{description}\n\nЦена: {price} руб/кг.'

    keyboard = [[InlineKeyboardButton('Назад', callback_data='BACK_TO_MENU')],
                [InlineKeyboardButton('Добавить в корзину', callback_data=f'ADD_TO_CART_{product_document_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    image_bytes = get_product_image(product)
    if image_bytes:
        media = InputMediaPhoto(media=image_bytes, caption=text, parse_mode=ParseMode.MARKDOWN)
        query.message.edit_media(media=media, reply_markup=reply_markup)
    else:
        query.message.edit_text(text=text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        
    return 'HANDLE_DESCRIPTION'


def handle_callback(update: Update, context: CallbackContext, callback_data: str) -> str:
    strapi_token = context.bot_data["STRAPI_TOKEN"]
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id

    if callback_data == 'BACK_TO_MENU':
        query.message.delete()
        return show_menu(update, context)
    
    elif callback_data == 'SHOW_CART':
        return show_cart(update, context)
    
    elif callback_data == 'CLEAR_CART':
        cart = get_or_create_cart(chat_id, strapi_token)
        if not cart or 'documentId' not in cart:
            query.message.reply_text('Корзина не найдена.')
            logger.error(f'Ошибка: корзина не найдена для chat_id={chat_id}')
            return 'HANDLE_CART'

        cart_document_id = cart['documentId']
        logger.info(f'Очистка корзины: cart_document_id={cart_document_id}')
        if clear_cart(cart_document_id, strapi_token):
            query.message.reply_text('Корзина очищена.')
            query.message.delete()
            return show_menu(update, context)
        else:
            query.message.reply_text('Не удалось очистить корзину.')
            return 'HANDLE_CART'
    
    elif callback_data == 'PAY':
        query.message.delete()
        query.message.reply_text('Пожалуйста, укажите ваш email для оформления заказа.')
        return 'WAITING_EMAIL'
    
    elif callback_data.startswith('ADD_TO_CART_'):
        product_document_id = callback_data.replace('ADD_TO_CART_', '')
        cart = get_or_create_cart(chat_id, strapi_token)
        if not cart or 'documentId' not in cart:
            query.answer('Не удалось получить или создать корзину')
            logger.error(f'Ошибка: корзина не создана или отсутствует documentId, cart={cart}')
            return 'HANDLE_DESCRIPTION'
        
        cart_document_id = cart['documentId']
        logger.info(f'Добавляем товар: cart_document_id={cart_document_id}, product_document_id={product_document_id}, quantity=1')
        
        add_product = add_product_to_cart(cart_document_id, product_document_id, strapi_token, quantity=1)
        
        if add_product:
            query.message.reply_text('Товар добавлен в корзину')
            return show_menu(update, context)
        
        query.answer('Ошибка при добавлении товара в корзину')
        return 'HANDLE_DESCRIPTION'
    
    else:
        return show_product(update, context, callback_data)


def handle_cart(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    if not query:
        return show_cart(update, context)
    
    return handle_callback(update, context, query.data)


def handle_description(update: Update, context: CallbackContext) -> str:
    query = update.callback_query
    if not query:
        return 'HANDLE_MENU'
    
    return handle_callback(update, context, query.data)


def handle_email(update: Update, context: CallbackContext) -> str:
    strapi_token = context.bot_data["STRAPI_TOKEN"]
    email = update.message.text.strip()

    if '@' not in email or '.' not in email:
        update.message.reply_text('Пожалуйста, укажите корректный email.')
        return 'WAITING_EMAIL'

    client = create_client(email, strapi_token)
    if not client or 'documentId' not in client:
        update.message.reply_text('Ошибка при регистрации клиента.')
        logger.error(f'Не удалось создать клиента для email={email}')
        return show_menu(update, context)

    update.message.reply_text(
        f'Ваш Email ({email}) успешно сохранён! С вами свяжется наш менеджер для проведения оплаты.'
    )
    
    return show_menu(update, context)
        
    
def handle_users_reply(update, context):
    db = get_database_connection()
    chat_id = None
    
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    
    if user_reply == '/start':
        next_state = show_menu(update, context)
        db.set(chat_id, next_state)
        return
    else:
        stored_state = db.get(chat_id)
        user_state = stored_state.decode('utf-8') if stored_state else 'START'
    
    states_functions = {
        'START': show_menu,
        'HANDLE_MENU': handle_description,
        'HANDLE_DESCRIPTION': handle_description,
        'SHOW_CART': show_cart,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': handle_email,
        
    }

    state_handler = states_functions.get(user_state, show_menu)
    
    try:
        next_state = state_handler(update, context)
    except Exception as err:
        logger.error(f'Ошибка при обработке состояния {user_state}: {err}')
        next_state = show_menu(update, context)

    db.set(chat_id, next_state)


def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv('REDIS_DB_PASSWORD')
        database_host = os.getenv('REDIS_DB_HOST')
        database_port = os.getenv('REDIS_DB_PORT')
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )
    global logger
    logger = logging.getLogger(__name__)
    
    global _database
    _database = None
    
    load_dotenv()
    token = os.getenv('TG_BOT_TOKEN')
    strapi_token = os.getenv("STRAPI_TOKEN")
    
    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.bot_data["STRAPI_TOKEN"] = strapi_token
    
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))

    set_menu_commands(updater.bot)
    
    updater.start_polling()
    updater.idle()
    
    
if __name__ == '__main__':
    main()