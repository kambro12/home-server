# Home Server Configurations

Zbiór plików konfiguracyjnych mojego domowego serwera i systemu automatyki domowej (Home Assistant).

## 💻 Sprzęt
* **Serwer:** Dell 5040
* **System operacyjny:** Ubuntu Linux

## 📂 Struktura repozytorium
* `/esphome` - Konfiguracje YAML dla modułów ESP8266/ESP32 (inteligentne gniazdka, sterowniki LED, rolety, głośniki itp.).
* `/lektor-web` - Pliki źródłowe i szablony strony internetowej opartej na generatorze Lektor.

## 🔒 Bezpieczeństwo
Ze względów bezpieczeństwa pliki zawierające poświadczenia (np. `secrets.yaml` z ESPHome) oraz główny plik struktury usług `docker-compose.yml` zostały wykluczone z tego publicznego repozytorium za pomocą `.gitignore`.
