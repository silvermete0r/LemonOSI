import telebot
import sqlite3
import requests
import pytesseract
import cv2
import os
import threading
from datetime import datetime as dt
from constants import TELEGRAM_API_KEY
from flask import Flask, render_template
from telebot import types

app = Flask(__name__)

bot = telebot.TeleBot(TELEGRAM_API_KEY)

# C:\Program Files\Tesseract-OCR

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def send_camera_image(chat_id):
    # Capture an image using cv2
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
    _, img = cap.read()
    boxes = pytesseract.image_to_data(img)
    # print(boxes)
    for x,b in enumerate(boxes.splitlines()):
        if x!=0:
            b = b.split()
            if len(b) == 12:
                x,y,w,h = int(b[6]),int(b[7]),int(b[8]),int(b[9])
                cv2.rectangle(img,(x,y),(w+x,h+y),(0,0,255),1)
                cv2.putText(img,b[11],(x+10,y-15),cv2.FONT_HERSHEY_COMPLEX,0.8,(50,50,255),1) 
    image_path = 'captured_image.jpg'
    cv2.imwrite(image_path, img)
    with open(image_path, 'rb') as photo:
        bot.send_photo(chat_id, photo)
    
    os.remove(image_path)

# Connect to the SQLite database
conn = sqlite3.connect('lemonosi.db')
cursor = conn.cursor()

def checkTemperature(temperature):
    threshold = 25
    if temperature > threshold:
        return "bad"
    else:
        return "good"
def checkHumidity(humidity):
    threshold = 70 
    if humidity > threshold:
        return "bad"
    else:
        return "good"

# Create lemonosi-table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS houses (
        chat_id INTEGER PRIMARY KEY,
        house_id INTEGER UNIQUE NOT NULL,
        temperature REAL,
        humidity REAL,
        sound REAL,
        light REAL,
        motion REAL,
        datetime TEXT
    )
''')
conn.commit()
conn.close()

def insert_sample_database():
    conn = sqlite3.connect('lemonosi.db')
    cursor = conn.cursor()

    cursor.execute("""INSERT INTO houses (chat_id, house_id, temperature, humidity, sound, light, motion, datetime)
VALUES
    (702008676, 1237889, 23.3, 0.0, 0.0, 122.0, 0.0, '2023-05-18T19:19:14Z'),
    (702008615, 1237813, 24.1, 12.5, 1.0, 150.2, 1.0, '2023-05-17T10:25:30Z'),
    (702008616, 1237814, 22.8, 40.7, 0.0, 75.6, 0.0, '2023-05-16T08:45:21Z'),
    (702008617, 1237815, 23.9, 95.2, 1.0, 180.7, 1.0, '2023-05-15T16:58:47Z'),
    (702008618, 1237816, 22.5, 61.8, 0.0, 90.4, 1.0, '2023-05-14T11:30:10Z'),
    (702008619, 1237817, 23.7, 75.9, 1.0, 140.5, 0.0, '2023-05-13T09:05:55Z'),
    (702008620, 1237818, 24.4, 88.2, 0.0, 110.9, 1.0, '2023-05-12T17:12:40Z'),
    (702008621, 1237819, 22.1, 48.6, 1.0, 95.3, 0.0, '2023-05-11T14:20:26Z'),
    (702008622, 1237820, 23.8, 82.4, 0.0, 125.1, 1.0, '2023-05-10T12:38:09Z'),
    (702008623, 1237821, 24.7, 65.3, 1.0, 160.8, 0.0, '2023-05-09T18:45:52Z');
""")
    
    conn.commit()
    conn.close()

@app.route('/')
def display_data():
    return render_template('login.html')
@app.route('/dashboard')
def to_dashboard():
    conn = sqlite3.connect('lemonosi.db')
    cursor = conn.cursor()

    # Fetch all rows from the 'houses' table
    cursor.execute("SELECT * FROM houses")
    houses = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('index.html', houses=houses)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f'''👋 Здравствуйте, {message.chat.first_name}! LemonOSI поможет вам получить актуальную информацию о потреблении коммунальных услуг и состоянии дома в реальном времени!

 🔗 Для подключения напишите ID своего дома в формате: <code>/connect house_id</code>
    
 📋 Подборка полезных функции: 
    
 /state - Получить общую информацию;
 /info - Статистика потребления ресурсов;
 /bill - Получение счета по коммунальным услугам;
 /checkGas -  Проверить счетчик газа;
 /checkWater - Проверить счетчик воды;
 /checkElectricity - Проверить счетчик электричества;

    ℹ️ Поддержка: <code>supwithproject@gmail.com</code>
    ''', parse_mode = 'html')


@bot.message_handler(commands=['state'])
def send_info(message):
    # Retrieve the accommodation information for the user
    url = 'https://api.thingspeak.com/channels/2153911/feeds.json'
    response = requests.get(url)

    if response.status_code != 200:
        bot.reply_to(message, 'Что-то пошло не так повторите еще раз!')
        return
    result = response.json()
    result = result['feeds'][-1]
    if result:
        temperature, humidity, sound, light, motion, datetime = result['field1'], result['field2'], result['field4'], result['field3'], result['field5'], result['created_at']
        response = f'''#️⃣ Текущее состояние потребление ресурсов:\n\n🌡️ Temperature: {temperature}°C - {checkTemperature(int(float(temperature)))}\n💦 Humidity: {humidity}% - {checkHumidity(int(float(humidity)))}\n🔊 Sound: {sound} - {"good" if int(sound) == 0 else "bad"} dB\n💡 Light: {light} - {"light" if int(light) < 300 else "dark"} lux\n🏃 Motion: {int(float(motion))} - {"detected" if int(motion) == 1 else "calmly"} \n\nАктаульные данные на: {datetime}'''
        
        conn = sqlite3.connect('lemonosi.db')
        cursor = conn.cursor()
        cursor.execute(f"UPDATE houses SET temperature='{temperature}', sound='{sound}', light='{light}', motion='{motion}', datetime='{datetime}'")        
        conn.commit()
        conn.close()
    else:
        response = "Вы все еще не подключены к нашей системе. Пожалуйста воспользуйтесь функцией <code>/connect house_id</code> для подключения."

    bot.send_message(message.chat.id, response, parse_mode='html')


@bot.message_handler(commands=['connect'])
def register_house(message):
    text = message.text.strip().split()
    if len(text) != 2:
        bot.reply_to(message, 'Вы ошиблись при вводе данных!')
        return
    house_id = text[1]

    new_conn = sqlite3.connect('lemonosi.db')
    new_cursor = new_conn.cursor()

    new_cursor.execute(f"SELECT * FROM houses WHERE chat_id={message.chat.id}")
    result = new_cursor.fetchone()
    new_conn.commit()

    if result:
        bot.reply_to(message, "Вы уже зарегистрированы в системе Lemon OSI!")
    else:
        new_cursor.execute(f"INSERT INTO houses VALUES({message.chat.id},{int(house_id)},0,0,0,0,0,'{dt.now()}')")
        new_conn.commit()
        bot.reply_to(message, "Вы успешно зарегистрировались в системе Lemon OSI!")

    new_cursor.close()
    new_conn.close()

@bot.message_handler(commands=['info'])
def send_info(message):
    markup = types.InlineKeyboardMarkup()
    link_button = types.InlineKeyboardButton(text='LemonOSI Stats', url='https://thingspeak.com/channels/2153911')
    markup.add(link_button)
    response = 'Посмотрите вашу статистику потребления ресурсов!'

    bot.send_message(message.chat.id, response, reply_markup=markup)

@bot.message_handler(commands=['bill'])
def send_bill(message):
    send_communal_service_tariffs(message.chat.id)

def send_communal_service_tariffs(chat_id):
    tariffs = {
        'Gas': 'Тариф на газ: $0.75/m³',
        'Electricity': 'Тариф на электричество: $0.12/kWh',
        'Heating': 'Тариф на отопление: $0.80/sqm',
        'Hot water': 'Тариф на горячую воду: $1.20/m³',
        'Cold water': 'Тариф на холодную воду: $0.60/m³'
    }

    response = "Current tariffs for communal services in Astana:\n\n"

    for price in tariffs.values():
        response += f"🏷️ {price}\n"

    bot.send_message(chat_id, response)

@bot.message_handler(commands=['checkGas'])
def send_photo_with_id(message):
    send_camera_image(message.chat.id)

@bot.message_handler(commands=['checkElectricity'])
def send_photo_with_id(message):
    send_camera_image(message.chat.id)

@bot.message_handler(commands=['checkWater'])
def send_photo_with_id(message):
    send_camera_image(message.chat.id)
    
flask_thread = threading.Thread(target=app.run, kwargs={'host': '127.0.0.1', 'port': 5000})
telegram_thread = threading.Thread(target=bot.polling)

flask_thread.start()
telegram_thread.start()