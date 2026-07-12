# 🏡 Dell 5040 - Home Server & Homelab

Zbiór plików konfiguracyjnych mojego domowego serwera i systemu automatyki domowej (Home Assistant).
Cała konfiguracja opiera się na **Docker Compose** i skupia się na domowym centrum rozrywki, inteligentnym domu (Smart Home) oraz w pełni zautomatyzowanym pobieraniu.

## 💻 Sprzęt
* **Serwer:** Dell OptiPlex 5040
* **System operacyjny:** Ubuntu Linux
* **Akceleracja GPU:** Wykorzystanie iGPU Intela (QuickSync) udostępnionego jako `/dev/dri` do sprzętowego transkodowania wideo.

---

## 🌟 Lista Usług (Kontenerów)

Poniżej znajduje się pełna lista systemów pracujących w klastrze, skonfigurowana w pliku `docker-compose.yml`:

### 📺 Multimedia i Przetwarzanie Wideo
* **[Jellyfin](https://jellyfin.org/)** – Główne domowe centrum multimedialne korzystające ze sprzętowego kodowania wideo.
* **[Jellyseerr](https://github.com/Fallenbagel/jellyseerr)** – Intuicyjny panel do zamawiania nowych filmów i seriali.
* **[Jellystat](https://github.com/CyferShepard/Jellystat)** – Rozbudowane statystyki oglądalności sprzężone z bazą PostgreSQL.
* **[Tdarr](https://tdarr.io/)** – Potężny węzeł transkodujący (Server + Node). W locie, całkowicie automatycznie i bezstratnie odchudza stare formaty wideo (np. XviD) do H.264/HEVC oszczędzając gigabajty przestrzeni.

### 🎬 Automatyzacja Pobierania (Arr Stack)
* **qBittorrent** – Niezawodny klient torrentów.
* **Prowlarr** – Serce całego ekosystemu; spina wszystkie trackery w jednym miejscu.
* **Sonarr** & **Radarr** – Automatyzacja śledzenia i pobierania odpowiednio seriali i filmów.
* **Bazarr** – Łowca napisów. Samodzielnie szuka i dociąga brakujące polskie translacje.
* **Flaresolverr** – Serwer proxy radzący sobie z barierami Cloudflare (kluczowy przy niektórych trackerach).

### 🏠 Smart Home i Automatyka
* **[Home Assistant](https://www.home-assistant.io/)** – Mózg całego inteligentnego domu.
* **[ESPHome](https://esphome.io/)** – Konfiguracje modułów ESP (inteligentne gniazdka, rolety, głośniki itp.) z kompilacją "w locie".
* **go2rtc** – Super-wydajny silnik streamingu na żywo dla kamer RTSP.

### 🎶 Dźwięk i Synteza Mowy
* **Music-Assistant** – Zaawansowany kombajn do dystrybucji muzyki po całym domu.
* **[Piper](https://github.com/rhasspy/piper)** – Niezależny, szybki, lokalny system Text-To-Speech (TTS) z polskimi, naturalnie brzmiącymi głosami.
* **Lektor-web** – Niestandardowy, zbudowany projekt frontendu webowego dla Pipera.

### 🌐 Inne i Narzędziowe
* **Cloudflared** – Wystawienie usług na świat przez bezpieczny tunel (bez "dziurawienia" routera).
* **Local Dashboard (Nginx)** – Niestandardowa, piękna i lokalna tablica. Posiada m.in. skrypty w JavaScript rozpakowujące kanały RSS lokalnych społeczności (np. Devil-Torrents, Electro-Torrent).
* **Filebrowser** – Intuicyjny menedżer plików przez przeglądarkę do obsługi `/mnt/media`.
* **Watchtower** – Narzędzie cicho dbające w tle o nocne aktualizacje obrazów Dockera do najnowszych wydań.
* **Metube** – Frontend do pobierania treści (YT-DLP).
* **SillyTavern** – Potężny interfejs chat-bota do zabaw z lokalnymi/zewnętrznymi modelami LLM.
* **Memos** – Podręczny, prywatny notatnik z bazą danych (w stylu małego Twittera).

---

## 🔒 Bezpieczeństwo i Architektura
* Większość multimediów jest zamontowana pod ścieżką `/mnt/media`.
* Ze względów bezpieczeństwa wszystkie loginy do trackerów, hasła bazy danych i plik `secrets.yaml` w ESPHome są wykluczone z głównego repozytorium przez reguły `.gitignore`.

*Stworzono z pomocą Antigravity IDE.*
