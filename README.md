##Инструкция к тестовому заданию

####Собрать и запустить контейнер
```
docker-compose up -d
```

####Выполнить миграции
```
docker-compose exec webapp python manage.py migrate
```

####Спарсить данные
```
docker-compose exec webapp python manage.py import_data --path=<tickers file (не обязательно)> --thread_number=<threads count (не обязательно)>
```

####Запустить runserver
```
docker-compose exec webapp python manage.py runserver 0.0.0.0:8000
```

```
http://localhost:8090
```