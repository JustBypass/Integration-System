import logging
import requests
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import time

# Инициализация Flask-приложения
app = Flask(__name__)

# Логирование
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# URL других сервисов
TARGET_SERVICE_1 = 'https://example.com/api/service1'
TARGET_SERVICE_2 = 'https://example.com/api/service2'

# Создание планировщика для фоновых задач
scheduler = BackgroundScheduler()

# Метод для отправки HTTP-запроса к сервисам
def send_request_to_service(url, service_name):
    try:
        logger.info(f"Sending request to {service_name} at {url}")
        response = requests.get(url)
        
        # Проверка успешности ответа
        if response.status_code == 200:
            logger.info(f"Success response from {service_name}: {response.text}")
            return response.json()  # Возвращаем данные сервиса, если они есть
        else:
            logger.error(f"Failed request to {service_name}. Status code: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error while sending request to {service_name}: {str(e)}")
        return None

# Функция для выполнения задачи по расписанию
def scheduled_task():
    logger.info("Scheduled task started")

    # Отправляем запросы на два сервиса
    data_service1 = send_request_to_service(TARGET_SERVICE_1, "Service 1")
    data_service2 = send_request_to_service(TARGET_SERVICE_2, "Service 2")
    
    # Обрабатываем полученные данные
    if data_service1:
        logger.info(f"Data from Service 1: {data_service1}")
    if data_service2:
        logger.info(f"Data from Service 2: {data_service2}")
    
    logger.info("Scheduled task finished")

# Запуск задачи по расписанию (например, каждые 60 секунд)
scheduler.add_job(scheduled_task, 'interval', seconds=60)

# Обработчик для POST-запроса
@app.route('/api/receive', methods=['POST'])
def handle_post_request():
    try:
        # Получаем данные из POST-запроса
        data = request.get_json()
        if not data:
            logger.warning("No JSON data received in POST request")
            return jsonify({'error': 'No JSON data received'}), 400
        
        logger.info(f"Received POST request with data: {data}")

        # Отправляем данные на целевой сервис
        target_response = requests.post(TARGET_SERVICE_1, json=data)

        if target_response.status_code == 200:
            logger.info(f"Successfully forwarded data to target service: {target_response.text}")
            return jsonify({'status': 'success', 'message': 'Data sent to target service successfully'}), 200
        else:
            logger.error(f"Failed to send data to target service. Response: {target_response.text}")
            return jsonify({'status': 'error', 'message': 'Failed to send data'}), 500
    except Exception as e:
        logger.error(f"Error in POST request handler: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'}), 500

# Запуск планировщика задач
scheduler.start()

# Главный метод для запуска сервера
if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=True, use_reloader=False)  # use_reloader=False для предотвращения повторного старта из-за APScheduler
