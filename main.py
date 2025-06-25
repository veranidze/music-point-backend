# main.py

import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta

# --- Конфигурация ---
import json

# ...

def get_calendar_service():
    """Создает и возвращает авторизованный объект для работы с Calendar API."""
    try:
        # Читаем секретные данные из переменной окружения
        creds_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if not creds_json_str:
            raise ValueError("Переменная окружения GOOGLE_CREDENTIALS_JSON не найдена.")

        creds_info = json.loads(creds_json_str)
        creds = service_account.Credentials.from_service_account_info(
            creds_info, scopes=SCOPES)

        service = build('calendar', 'v3', credentials=creds)
        return service
    except FileNotFoundError:
        print(f"ОШИБКА: Файл '{SERVICE_ACCOUNT_FILE}' не найден. Убедитесь, что он находится в той же папке, что и main.py")
        return None
    except Exception as e:
        print(f"Произошла ошибка при аутентификации: {e}")
        return None

# --- API эндпоинт (точка входа) ---
@app.get("/api/events")
def get_events(
    calendar_id: str = Query(..., description="ID Google Календаря для запроса"),
    year: int = Query(..., description="Год"),
    month: int = Query(..., description="Месяц (1-12)")
):
    """
    Эндпоинт для получения событий из указанного календаря за определенный месяц.
    """
    service = get_calendar_service()
    if not service:
        raise HTTPException(status_code=500, detail="Не удалось подключиться к сервису Google Calendar.")

    # Определяем начало и конец месяца
    time_min = datetime(year, month, 1).isoformat() + 'Z'
    # Чтобы получить события за весь месяц, нужно указать начало следующего месяца
    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1
    time_max = datetime(next_year, next_month, 1).isoformat() + 'Z'

    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return {"items": events}

    except HttpError as error:
        print(f'Произошла ошибка HTTP: {error}')
        raise HTTPException(status_code=error.resp.status, detail=f"Ошибка при запросе к Google Calendar API: {error.reason}")
    except Exception as e:
        print(f'Произошла общая ошибка: {e}')
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")

# Запуск сервера: uvicorn main:app --reload
```text
# requirements.txt

fastapi
uvicorn[standard]
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
