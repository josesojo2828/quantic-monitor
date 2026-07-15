# quantic-monitor 👁️

[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?logo=prometheus&logoColor=white)](https://prometheus.io)
[![Grafana](https://img.shields.io/badge/Grafana-F46800?logo=grafana&logoColor=white)](https://grafana.com)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://python.org)

Stack de monitoreo centralizado para servidores, todo dockerizado. Métricas del sistema + seguridad SSH en un solo lugar.

## Stack

```
┌────────────────┐     ┌──────────────┐     ┌────────────────┐
│  node-exporter  │────▶              │────▶│    Grafana     │
│  (host stats)   │     │  Prometheus  │     │  Dashboards    │
├────────────────┤     │  (storage)   │     ├────────────────┤
│  auth-exporter  │────▶  60d / 20GB  │     │ Node Full      │
│  (SSH security) │     └──────────────┘     │ SSH Security   │
└────────────────┘                           └────────────────┘
```

## Puertos

| Puerto | Servicio | Qué monitorea |
|--------|----------|---------------|
| `15100` | node-exporter | CPU, RAM, disco, red, uptime |
| `15101` | auth-exporter | SSH logins (fallidos/ok), IPs, sudo |
| `15102` | Prometheus | Almacenamiento (60d / 20GB) |
| `15103` | Grafana | Dashboards pre-configurados |

## Quick Start

```bash
# Clonar
git clone https://github.com/josesojo2828/quantic-monitor.git
cd quantic-monitor

# Opcional: cambiar password de Grafana
cp .env.example .env

# Levantar
docker compose up -d
```

Abrir [http://localhost:15103](http://localhost:15103) — `admin / admin123`

## Dashboards

### Node Exporter Full
- CPU Usage (gauge + time series)
- Load Average (1m, 5m, 15m)
- RAM Usage & Breakdown
- Disk Space (table con thresholds)
- Disk IO (reads/writes)
- Network Traffic (in/out en bps)
- Network Errors
- Uptime

### SSH Security Monitor
- Failed Logins (24h) — stat con thresholds
- Successful Logins (24h) — stat con thresholds
- Sudo Commands (24h)
- Currently Tracked Offending IPs
- Failed Logins Over Time
- Successful Logins Over Time
- Top 10 Offending IPs — bar gauge
- Auth Events by User — tabla
- Sudo Activity — tabla

## Retención

| Componente | Config |
|------------|--------|
| Prometheus | 60 días o 20GB (lo que se cumpla primero) |
| node-exporter | Sin estado |
| auth-exporter | Sin estado (parsea logs en vivo) |

## auth-exporter

Contenedor Python liviano que monta `/var/log/` del host (read-only) y expone métricas Prometheus en `:9101`:

| Métrica | Tipo | Labels |
|---------|------|--------|
| `auth_ssh_failed_total` | Counter | `user`, `ip`, `auth_method` |
| `auth_ssh_success_total` | Counter | `user`, `ip`, `auth_method` |
| `auth_ssh_failed_by_ip` | Gauge | `ip` |
| `auth_sudo_total` | Counter | `user`, `command` |
| `auth_lines_processed_total` | Counter | — |

## Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GRAFANA_USER` | `admin` | Usuario de Grafana |
| `GRAFANA_PASSWORD` | `admin123` | Password de Grafana |

## Licencia

MIT
