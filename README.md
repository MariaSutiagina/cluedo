# Cluedo
# Tg бот игры Cluedo
## История

## Управление

## Игра

## Установка игры
Бот может работать под операционной системой Linux (тестировалось на Ubuntu 20.04)

### Конфигурация
#### На домашнем сервере или другой машине, имеющей внешний белый IP адрес
0. Скачиваем с гитхаба исходники проекта
1. Выясняем внешний адрес машины, на котором будет развернуто приложение бота
Для debian linux (Ubuntu, Debian, Astra linux) смотрим вывод команды "ip a"
Для windows - смотрим вывод команды ipconfig

Для примера, далее будем рассматривать внешний IP = 1.2.3.4

2. Поскольку для работы ботов в режиме WebHook телеграм требует, чтобы бот работал по протоколу https, необходимо сгенерировать самоподписанный сертификат, который передается в API телеграм
Для генерации сертификата создадим файл cert.cnf, в котором в поля CN и  IP.1 пропишем внешний IP адрес машины с ботом:
```
[req]
default_bits = 2048
default_md = sha256
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no
[req_distinguished_name]
C = US
ST = VA
L = SomeCity
O = SomeOrgInc
OU = RogaYKopyta
CN = 1.2.3.4
[v3_req]
#extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
IP.1 = 1.2.3.4
```

Далее, сгенерируем приватный ключ и сертификат tg_cluedo.key, tg_cluedo.pem командой:
```
openssl req -new -nodes -x509 -days 3650 -keyout tg_cluedo.key -out tg_cluedo.pem -config ./cert.cnf
```

После этого ключ и сертификат надо разместить в директории config проекта

3. Создаем yaml файл конфигурации приложения бота - config.yaml и разместим его в директории config
В этом файле указываем внешний url и порт WebHook'a, на котором телеграм будет искать наш бот (в нашем случае webhook_host=https://1.2.3.4 и webhook_port=8443)
далее - пропишем пути к ранее сгенерированным приватному ключу и сертификату https (webhook_cert=config/tg_cluedo.pem, webhook_key=config/tg_cluedo.pem)
также необходимо настроить хост и порт, на котором будет работать сервер django (это локальный IP машины с ботом - например host=192.168.16.197, port=8888)
далее - настроим токен бота, запросив его у BotFather'a и прописав в поле token
далее - настроим секретный ключ django - любое длинное случайное значение (поле secret)
для CORS настроим поле allowed_hosts на все возможные адреса, которые мы захотим использовать для тестирования бота
```yaml
telegram:
  token: 5192318520:AAGltUG6bY2YhAWIxxCl379cizz1uiVbke-g
  webhook_host: https://1.2.3.4
  webhook_path: /
  webhook_port: 8443
  webhook_cert: config/tg_cluedo.pem
  webhook_key: config/tg_cluedo.key
server:
  host: 192.168.16.197
  port: 8888
  log_file: ./bot.log
  message_timeout: 10
django: 
  secret: nf*a54-muy*hx)rd2=^&8qx8%296zq4^x^*61e577s12fmb4co
  allowed_hosts:
    - 127.0.0.1
    - 192.168.16.197
```

#### На хостинге (на примере Heroku)
### Запуск бота