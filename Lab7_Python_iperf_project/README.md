# Лабораторна робота 7

Автоматизація мережевого тестування засобами Python, iperf3 та pytest.

Виконав: Владислав Криворот, група ІП-34.

## Середовище

- ПК1: Ubuntu Server 24.04.3 LTS ARM64, адреса 10.0.0.1, користувач vlad; SSH та iperf3-сервер.
- ПК2: Ubuntu Server 24.04.3 LTS ARM64, адреса 10.0.0.100; Python-скрипт і pytest.
- Зафіксовані версії: Python 3.12.3, iperf3 3.16, pytest 9.2.0, Paramiko 5.1.0.
- TCP-порт iperf3: 5201. Тривалість тесту: 10 с; інтервал вимірювання: 1 с.

## Підготовка

На ПК1 установити iperf3 та openssh-server, увімкнути SSH. Автоматичну службу iperf3 залишити вимкненою: життєвим циклом сервера керує тест.

На ПК2 у папці проєкту:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Перед запуском автоматизації перевірити підключення та зберегти ключ хоста у known_hosts:

```bash
ssh vlad@10.0.0.1 hostname
```

## Частина 1

На ПК1 запустити сервер вручну:

```bash
iperf3 -s
```

На ПК2 виконати ручну перевірку, парсинг і запуск через Python:

```bash
iperf3 -c 10.0.0.1 -t 10 -i 1 -f m | tee manual_tcp.txt
python parser.py
python client.py
```

Негативні сценарії:

```bash
python client.py --bitrate 10M --output slow_tcp.txt
python client.py --port 5202 --output connection_error.txt
```

Звичайний сценарій має завершуватися PASS і кодом 0. Негативні сценарії навмисно порушують умови: очікуються FAIL і код 1. Код попередньої команди перевіряється окремою командою `echo $?` відразу після її завершення.

## Частина 2

Зупинити ручний сервер на ПК1 через Control+C. На ПК2 у Bash ввести пароль ПК1 без запису його в код:

```bash
read -s -p "Password for PC1: " LAB_SSH_PASSWORD
export LAB_SSH_PASSWORD
```

Успішний сценарій:

```bash
python -m pytest -v -s test_iperf.py
```

Очікується `1 passed`, код завершення 0.

Недостатня швидкість:

```bash
python -m pytest -v -s --tb=short test_iperf.py --bitrate 10M --result-name pytest_slow
```

Очікується `1 failed` із причиною `Transfer too low`, код 1.

Неправильний порт клієнта:

```bash
python -m pytest -v -s --tb=short test_iperf.py --client-port 5202 --result-name pytest_connection_error
```

Очікується `1 failed` із причиною `Client error` / `Connection refused`, код 1. Після кожного сценарію фікстура зупиняє створений нею сервер і закриває SSH-з'єднання.

Після роботи видалити змінну з паролем із поточного сеансу:

```bash
unset LAB_SSH_PASSWORD
```

## Файли

- `client.py`: запуск iperf3 через subprocess, отримання stdout/stderr та перевірка порогів.
- `parser.py`: розбір звичайного однопотокового TCP-виводу Linux із полями Retr і Cwnd.
- `conftest.py`: фікстури server і client, SSH, setup/teardown, збереження результатів.
- `test_iperf.py`: перевірка помилок, наявності інтервалів і порогових значень.
- `requirements.txt`: точні версії Python-пакетів використаного середовища.
- `results/`: початковий вивід iperf3 та stderr для трьох сценаріїв pytest.
- `docs/test_cases.md`: тест-кейси та фактичні результати.
- `docs/defect_report.md`: навчальний опис помилки конфігурації порту.
- `evidence/`: скріншоти фактичних запусків.

## Критерії

У кожному розібраному інтервалі Transfer має бути строго більше 2 MBytes, а Bitrate - строго більше 20 Mbits/sec. Парсер приводить Transfer до одиниць 2^20 байтів, Bitrate до 10^6 біт/с, Cwnd до 2^10 байтів. Підсумкові рядки sender і receiver не включаються повторно. Порожній результат або помилка підключення не вважаються успішною перевіркою.

Виміряно пропускну здатність між двома VM на одному MacBook. Ці числа характеризують віртуальну мережу. Автоматизований сценарій стосується TCP; для UDP потрібен інший формат парсингу.

## Зафіксовані результати

| Сценарій pytest | Результат | Час за скріншотом | Код завершення |
| --- | --- | --- | --- |
| Звичайний запуск | PASSED | 10.57 с | 0 |
| Обмеження 10M | FAILED: Transfer too low, 1.25 MBytes | 10.49 с | 1 |
| Порт клієнта 5202 | FAILED: Connection refused | 0.44 с | 1 |

Негативні запуски демонструють очікувану реакцію перевірки на навмисно створені несприятливі умови. Скріншоти підтверджують виконання teardown також після FAILED.
