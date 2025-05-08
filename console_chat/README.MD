# Скрипты для работы с серверным чатом

Консольные утилиты для работы с подключениями к чатам.
Для получения сообщений используется скрипт chat_listen.py
Для отправки сообщений используется скрипт chat_write.py


## Как установить

Для работы скриптов нужен Python версии не ниже 3.6.

```bash
pip install -r requirements.txt
```

## Как запустить

### Чтение сообщений из чата
python chat_listen.py

Аргументы командной строки
- --host - адрес хоста чата
- --port - номер порта для прослушивания
- --history - путь к файлу для сохранения истории чата

Пример: 
- python chat_listen.py --host 192.168.0.1 --port 5001 --history ~/minechat.history

### Отправка сообщений в чат:

python write_minechat.py
Аргументы командной строки
- message - сообщение для отправки
- -s, --host - адрес хоста чата
- -p, --port - номер порта для отправки
- -t, --token - токен авторизации
- -u, --username - имя пользователя

usage: chat_write.py [-h] [-s HOST] [-p PORT] [-t TOKEN] [-u USERNAME] message

### Поддерживаются переменные окружения:
- Создайте файл .env в корне проекта. Пример представлен в .env.example:
```bash
LISTEN_HOST="minechat.dvmn.org"
LISTEN_PORT=5000
HISTORY_FILE_NAME="history.txt"

WRITE_HOST="minechat.dvmn.org"
WRITE_PORT=5050
WRITE_MESSAGE="message"
WRITE_TOKEN="619497fc-1d3e-11f0-abed-0242ac110002"
WRITE_USERNAME="username"
```
