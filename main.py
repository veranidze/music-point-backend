# main.py

import os
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

# --- Конфигурация ---
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# --- Инициализация FastAPI ---
app = FastAPI()

# --- Настройка CORS ---
# Это КРАЙНЕ ВАЖНО для связи фронтенда на Vercel и бэкенда на Render.
# В origins можно будет позже вставить URL вашего сайта для большей безопасности.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Логика работы с Google Calendar API ---
def get_calendar_service():
    """
    Создает и возвращает авторизованный объект для работы с Calendar API,
    используя данные из переменных окружения.
    """
    try:
        creds_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if not creds_json_str:
            raise ValueError("Переменная окружения GOOGLE_CREDENTIALS_JSON не найдена.")
        
        creds_info = json.loads(creds_json_str)
        creds = service_account.Credentials.from_service_account_info(
            creds_info, scopes=SCOPES)
            
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"ОШИБКА при аутентификации в Google: {e}")
        return None

# --- API Эндпоинт (точка входа) ---
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
        raise HTTPException(status_code=500, detail="Ошибка конфигурации сервера: не удалось подключиться к сервису Google Calendar.")

    time_min = datetime(year, month, 1).isoformat() + 'Z'
    next_month_year = year + (month // 12)
    next_month = month % 12 + 1
    time_max = datetime(next_month_year, next_month, 1).isoformat() + 'Z'

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
        error_reason = str(error.reason)
        if error.resp.status == 404:
            error_reason = "Календарь не найден. Проверьте ID календаря."
        elif error.resp.status == 403:
             error_reason = "Нет доступа к календарю. Убедитесь, что вы поделились им с сервисным аккаунтом."
        
        print(f'Произошла ошибка HTTP: {error_reason}')
        raise HTTPException(status_code=error.resp.status, detail=f"Ошибка Google Calendar API: {error_reason}")
    except Exception as e:
        print(f'Произошла общая ошибка: {e}')
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")

