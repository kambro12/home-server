# 🏡 Dell OptiPlex 5040 - Home Server & Homelab

Welcome to my personal, fully automated home server environment (Homelab).
The entire setup is based on **Docker Compose** and runs under a single, unified container network. It focuses on a home entertainment center, Smart Home automation, privacy services, and automated downloading, utilizing **Intel QuickSync** hardware video encoding directly from the server's CPU.

---

## 🌟 Services (Containers) List

Below is a complete list of the systems running "under the hood" of this cluster, as configured in the `docker-compose.yml` file:

### 📺 Multimedia & Video Processing
* **[Jellyfin](https://jellyfin.org/)** – The main home media center. Mapped with `/dev/dri` access for hardware transcoding support via iGPU.
* **[Jellyseerr](https://github.com/Fallenbagel/jellyseerr)** – An automated request management panel for discovering and requesting new movies and TV shows.
* **[Jellystat](https://github.com/CyferShepard/Jellystat)** – Comprehensive watch statistics and tracking integrated with Jellyfin (backed by PostgreSQL).
* **[Tdarr](https://tdarr.io/)** – A powerful, distributed transcoding node (Server + Node). Automatically scans and losslessly converts old, heavy video files (e.g., XviD) to modern formats (H.264/HEVC) using hardware acceleration (QSV), saving gigabytes of storage space.

### 🎬 Downloading Automation (Arr Stack)
* **qBittorrent** – A reliable torrent client for downloading content directly to the `/mnt/media` mount.
* **Prowlarr** – The indexer manager linking all torrent trackers in one place.
* **Sonarr** & **Radarr** – Automation tools for tracking and downloading TV shows and movies respectively.
* **Bazarr** – Subtitle hunter. Automatically searches for and downloads missing subtitles.
* **Flaresolverr** – Proxy server to bypass Cloudflare protection (crucial for some public trackers).

### 🏠 Smart Home & Automation
* **[Home Assistant](https://www.home-assistant.io/)** – The brain of the smart home, with full local network access and Docker Socket integration.
* **[ESPHome](https://esphome.io/)** – Management and on-the-fly compilation environment for ESP microcontrollers (smart plugs, LED drivers, blinds, sensors, etc.).
* **go2rtc** – Super-efficient live streaming engine for RTSP security cameras.

### 🎶 Audio & Speech Synthesis
* **Music-Assistant** – Advanced music streaming and distribution center integrated with Home Assistant.
* **[Piper](https://github.com/rhasspy/piper)** – Independent, fast, local Text-To-Speech (TTS) system based on neural networks. Uses natural-sounding voice models.
* **Lektor-web** – A custom-built web frontend for Piper.

### 🌐 Access & Management
* **Cloudflared** – Exposing local services to the outside world via a secure tunnel (without port-forwarding on the home router).
* **Local Dashboard (Nginx)** – A dedicated, custom landing page. Features JavaScript scripts to parse local RSS feeds from torrent communities.
* **Filebrowser** – Intuitive web-based file manager for easy access and management of `/mnt/media`.
* **Watchtower** – A background utility ensuring silent, nightly updates of Docker images to their latest stable releases.
* **Metube** – A convenient web frontend based on `yt-dlp` for downloading YouTube videos and music directly to the server.
* **SillyTavern** – A powerful chat-bot interface for experimenting with local or remote AI models (LLMs).
* **Memos** – A lightweight, private note-taking hub (similar to a self-hosted Twitter) for quick thoughts and links.

---

## 🛠️ Storage & Permissions Architecture
* Most media storage is mounted via a secure **FUSE** system (MergerFS) at `/mnt/media`.
* Environment variables `PUID=1000` and `PGID=1000` maintain permission consistency, ensuring different containers can edit the same files without "Access Denied" errors.
* Containers utilizing hardware graphics acceleration (Intel QuickSync) use mapped `/dev/dri` and appropriate permission groups (render/video).
* For security reasons, credentials, database passwords, and the ESPHome `secrets.yaml` file are excluded from the main public repository via `.gitignore` rules.

*Created with the help of Antigravity IDE.*
