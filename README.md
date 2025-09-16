# Продаём рыбу в Telegram

**Telegram Fish Bot** — это Telegram-бот для осуществления покупок. Бот позволяет просматривать каталог товаров, добавлять их в корзину, оформлять заказ с указанием email. Основные особенности:

- **Хранение состояний**: Использует базу данных Redis для управления состояниями пользовательских сессий (например, текущий шаг взаимодействия с ботом).
- **Хранение данных**: Использует CMS Strapi для управления данными о товарах, корзинах, покупках и клиентах.

<p align="center">
    <img src="https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzA5ejFibXFhaTN5Y2o4Z3dlZHFuMng0MDl4eGkwbm91NTFwdjNseCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/FSrDCCqeOTs52jYc6b/giphy.gif">
</p>

Бот написан на Python с использованием библиотеки `python-telegram-bot` (версия 13.15) и взаимодействует с API Strapi для получения данных о продуктах и управления заказами.

## Оглавление

- [Требования](#требования)
- [Установка](#установка)
- [Переменные окружения](#переменные-окружения)
- [Модели в Strapi](#модели-в-Strapi)
- [Запуск проекта](#запуск-проекта)
- [Цель проекта](#цель-проекта)


## Требования

- **Python**: 3.11 или выше
- **Redis**: Для хранения состояний сессий
- **Strapi**: Для управления данными (продукты, корзины, клиенты)


## Установка

- Python 3.11 должен быть установлен
- Скачайте код:
```bash
git clone https://github.com/VASILIYKAS/Telegram-fish-shop-bot.git
```
- Рекомендуется создать виртуальное окружение. Для этого нужно выполнить команду: 
```bash
python -m venv .venv
```
- Активируйте виртуальное окружение:
```bash
.venv\Scripts\activate    # Для Windows
source .venv/bin/activate # Для Linux
```
- Затем установите все необходимые библиотеки, сделать это можно командой: 
```bash
pip install -r requirements.txt
```
- **Установите Strapi**:\
[Инструкция](https://github.com/strapi/strapi?tab=readme-ov-file#-installation) по установке.\
Перед установкой strapi необходимо установить Node.js (если он ещё не установлен).
    - Установите [NVM](https://github.com/coreybutler/nvm-windows/releases) (Node Version Manager).
    - Проверьте установку в терминале (PowerShell / cmd / macOS Terminal / bash):
    ```powershell
    nvm -v
    ```
    Если вы увидели версию nvm значит установка прошла успешно.
    - Установите Node.js с помощью nvm:
    ```powershell
    nvm install 22.9.0
    ```
    - Перейдите в папку своего проекта:
    ```powershell
    cd path\to\your\project
    ```
    - Создайте новый проект strapi:
    ```powershell
    npx create-strapi@latest
    ```
    - Перейдите в папку с проектом strapi:
    ```powershell
    cd path\to\your\project\strapi-project
    ```
    - Установите зависимости:
    ```powershell
    npm install
    ```
    - Теперь вы можете запустить свой проект strapi, для этого выполните команду:
    ```powershell
    npm run develop
    ```
    Сервер запустится на http://localhost:1337 \
    Админка будет доступна по http://localhost:1337/admin

    При первом запуске Strapi предложит создать первого администратора.\
    После этого можно войти и управлять админкой.


## Переменные окружения

Проект использует файл `.env` для хранения конфиденциальных данных. В репозитории уже есть шаблон `example.env`, который нужно скопировать и настроить:
1. Скопируйте файл example.env в .env:
- Для macOS и Linux выполните команду:
```bash
cp example.env .env
```
- Для Windows используйте команду:
```powershell
copy example.env .env
```
2. Откройте файл `.env` в текстовом редакторе.
3. Укажите значение переменных после знака `=`:
- `STRAPI_TOKEN` - получить токен можно в админке strapi, перейдите в settings -> API Tokens.
```python
STRAPI_TOKEN=your_strapi_token
```

- `TG_BOT_TOKEN` - получить токен можно здесь [BotFather](https://telegram.me/BotFather).
```python
TG_BOT_TOKEN=your_telegram_bot_token
```

- `REDIS_DB_HOST` - можно получить на сайте [Redis](https://cloud.redis.io/#/login). 
    - Зарегистрируйтесь и зайди в Redis. 
    - В меню слева нажмите "Databases" и выбирете свою бд.
    - На вкладке "General" найдите "Public endpoint", это и есть ваш адрес бд, в конце после двоеточия идёт порт. 

- `REDIS_DB_PORT` - можно получить на сайте [Redis](https://cloud.redis.io/#/login). 
    - Зарегистрируйтесь и зайди в Redis. 
    - В меню слева нажмите "Databases" и выбирете свою бд.
    - На вкладке "General" найдите "Public endpoint", это и есть ваш адрес бд, в конце после двоеточия идёт порт.

- `REDIS_DB_PASSWORD` - можно получить на сайте [Redis](https://cloud.redis.io/#/login).
    - Зарегистрируйтесь и зайди в Redis. 
    - В меню слева нажмите "Databases" и выбирете свою бд.
    - На вкладке "Security" будет ваш пароль "Default user password"


## Модели в Strapi

Для добавления моделей в Strapi перейдите в админку http://localhost:1337/admin
- откройте вкладку `Content-Type Builder`
- нажмите на `+` в разделе `Collection Types`
- Укажите название модели, например `Cart`
- Откройте созданую модель и добавьте поля, кнопка `Add new field`
- Добавьте следующие модели и поля:

1. Cart

    Поля:
    - chat_id — Text (required)
    - cart_items — Relation (one-to-many) → Cart Item
    - users_permissions_user — Relation (many-to-one) → User (from users-permissions plugin)
    - client — Relation (many-to-one) → Client

Описание:
Модель корзины хранит информацию о заказах конкретного пользователя (Telegram chat) и связывает товары через Cart Item.

2. Cart Item

Поля:
- quantity — Number
- cart — Relation (many-to-one) → Cart
- product — Relation (many-to-one) → Product

Описание:
Элементы корзины — каждый объект представляет один товар с указанным количеством.

3. Product

Поля:
- title — Text
- description — Text
- picture — Media (Multiple)
- price — Number
- cart_items — Relation (one-to-many) → Cart Item

Описание:
Товары, которые можно добавить в корзину. Связь cart_items позволяет определить, в каких корзинах данный товар присутствует.

4. Client

Поля:
- email — Email

Описание:
Хранит клиентов, которые оформляют заказы.

Так же необходимо выдать права на эти модели, перейдите в `settings` → раздел `Users & Permissions plugin` → `Roles` → `Public`.\
Найдите созданые модели и установите флажок рядом с `Select all`.


## Запуск проекта

1. **Запустите Strapi**:
   ```powershell
   cd your_folder_strapi_project
   npm run develop
   ```
   - Убедитесь, что Strapi доступен по `http://localhost:1337`.

2. **Запустите бота**:
   - Откройте новый терминал.
    - Активируйте виртуальное окружение:
    ```bash
    .venv\Scripts\activate    # Для Windows
    source .venv/bin/activate # Для Linux
    ```
   - Запустите бота:
     ```powershell
     python bot.py
     ```

3. **Проверьте работу бота**:
   - Откройте Telegram, найдите вашего бота и отправьте команду `/start`.
   - Выберите товар, добавьте в корзину, оформите заказ.


## Цель проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).