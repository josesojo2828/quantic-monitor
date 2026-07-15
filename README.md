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
| `15102` | Prometheus | Almacenamiento (60d / 20GB) — expuesto para Grafana externo |
| — | node-exporter | CPU, RAM, disco, red, uptime (solo red interna) |
| — | auth-exporter | SSH logins (fallidos/ok), IPs, sudo (solo red interna) |
| `15103` | Grafana | Dashboards (solo con `--profile complete`)

## Quick Start

```bash
# Clonar
git clone https://github.com/josesojo2828/quantic-monitor.git
cd quantic-monitor

# Opcional: cambiar password de Grafana
cp .env.example .env

# Solo servicios base (node-exporter + auth-exporter + prometheus)
docker compose up -d

# Stack completo (con Grafana incluido)
docker compose --profile complete up -d
```

- **Prometheus**: [http://localhost:15102](http://localhost:15102)
- **Grafana** (con profile): [http://localhost:15103](http://localhost:15103) — `admin / admin123`

## Usar con Grafana externo

Si ya tenés un Grafana en otro lado (VPS, servidor central):

1. Agregá **Prometheus** como datasource apuntando a `http://<IP-del-server>:15102`
2. Importá los dashboards de `grafana/dashboards/` usando ese datasource

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

## Alertas (PromQL)

Consultas listas para configurar alertas en Grafana o Prometheus. Todos los thresholds son orientativos, ajustalos según tu server.

### 🔴 CPU > 80%

```
(100 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
```

Alerta cuando el CPU promedio de los últimos 5 minutos supere el 80%.

### 🟡 CPU > 90% (crítico)

```
(100 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
```

### 🔴 RAM disponible < 10%

```
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 10
```

Alerta cuando quede menos del 10% de RAM disponible.

### 🟡 RAM disponible < 20%

```
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 20
```

### 🔴 Disco (/) ocupado > 90%

```
(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 > 90
```

### 🟡 Disco (/) ocupado > 80%

```
(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 > 80
```

### 🚨 SSH: múltiples fallos en poco tiempo

```
sum(rate(auth_ssh_failed_total[5m])) > 1
```

Alerta cuando haya más de 1 intento fallido por segundo en promedio los últimos 5 minutos (ajustá el threshold según tu caso).

### 🐌 Load Average alto

```
node_load1 > 4
```

Alerta si el load average de 1 minuto supera 4. Ajustá el número según los cores de tu CPU.

### ⚙️ Cómo configurar en Grafana

1. Panel → **Alert** → **Create alert rule**
2. Pegá la query PromQL
3. Definí: `Evaluate every 1m`, `For 5m` (para evitar falsos positivos)
4. Elegí canal de notificación (email, Telegram, Slack, etc.)

## Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GRAFANA_USER` | `admin` | Usuario de Grafana |
| `GRAFANA_PASSWORD` | `admin123` | Password de Grafana |

## Licencia

MIT
