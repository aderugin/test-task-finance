##Инструкция к тестовому заданию

1. Собрать и запустить контейнер
```
docker-compose up -d
```

2. Выполнить миграции
```
docker-compose exec webapp python manage.py migrate
```

3. Спарсить данные
```
docker-compose exec webapp python manage.py import_data --path=<tickers file (не обязательно)> --thread_number=<threads count (не обязательно)>
```

4. Запустить runserver
```
docker-compose exec webapp python manage.py runserver 0.0.0.0:8000
```

```
http://localhost:8090
```