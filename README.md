# Booking API

REST API для бронирования ресурсов (переговорки, столы) на FastAPI.

## Запуск
pip install -r requirements.txt
uvicorn main:app --reload

Документация: http://127.0.0.1:8000/docs

## Эндпоинты
- GET /health
- POST /resources, GET /resources, GET /resources/{id}
- POST /bookings, GET /bookings, DELETE /bookings/{id}

Проверка пересечений: нельзя забронировать занятый слот (409).