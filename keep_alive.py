from flask import Flask
from threading import Thread

app = Flask(_name_)

@app.route('/')
def home():
    return "Bot is running!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
