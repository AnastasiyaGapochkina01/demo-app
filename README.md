# Metrics demo app
Простое приложение на FastAPI с интегрированным сбором метрик для мониторинга. 
Предоставляет как стандартные метрики Prometheus, так и пользовательский JSON-эндпоинт, удобный для интеграции с Zabbix или другими системами мониторинга.

### Требования
- python3.12

Для запуска необходимо
- склонировать репозиторий
- установить зависимости (`pip install -r requirements.txt`)
- запустить командой `uvicorn app:app --host 0.0.0.0 --port 8001`

### Проверки
```bash
curl http://localhost:8001/health

curl http://localhost:8001/data
curl -X POST http://localhost:8001/create
curl http://localhost:8001/list

curl http://localhost:8001/metrics | jq .
```
