#
#  README.md
#  CryptoTracker
#
#  Created by Cascade on Dec 14, 2025.
#  Copyright © 2025 CryptoTracker. All rights reserved.
#

# CryptoTracker

Aplicación Flask para visualizar las principales criptomonedas en tiempo real con datos de CoinGecko y panel interactivo tipo dashboard financiero.

![CryptoTracker Dashboard Placeholder](docs/screenshots/dashboard-placeholder.png)

## Requisitos previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Acceso a Internet para consumir la API pública de CoinGecko

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/victorsanchez01/cryptotracker.git
   cd cryptotracker
   ```
2. Crear y activar un entorno virtual (opcional pero recomendado):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configurar variables de entorno si se requiere (ej. `FLASK_ENV`, `PORT`) usando `.env`.

## Ejecución

```bash
flask --app app run --debug
```

La aplicación quedará disponible en `http://127.0.0.1:5000/`.

Para despliegues productivos se recomienda usar `gunicorn`:

```bash
gunicorn -w 2 -b 0.0.0.0:8000 app:app
```

## Endpoints API

| Endpoint | Método | Descripción |
| --- | --- | --- |
| `/` | GET | Página principal del dashboard. |
| `/api/cryptos` | GET | Retorna las top 10 criptomonedas por market cap en USD con campos: `id`, `symbol`, `name`, `current_price`, `price_change_percentage_24h`, `market_cap`, `image`, `total_volume`. |
| `/api/crypto/<id>/history` | GET | Devuelve el historial de precios (7 días) para la cripto con `id` determinado usando datos de CoinGecko. |

## Tecnologías utilizadas

- Flask + Jinja2
- CoinGecko API
- Chart.js
- Fetch API y JavaScript modular
- CSS moderno con tema oscuro (Space Grotesk)

## Estructura del proyecto

```
cryptotracker/
├── app.py
├── requirements.txt
├── README.md
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── templates/
    └── index.html
```

## Testing

1. **Instalar dependencias de testing**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ejecutar solo tests unitarios**
   ```bash
    pytest -m unit
   ```

3. **Ejecutar solo tests E2E (requiere servidor Flask en http://localhost:5000)**
   ```bash
    pytest -m e2e
   ```

4. **Ejecutar todo el suite con cobertura y reporte HTML**
   - macOS/Linux:
     ```bash
     ./run_tests.sh
     ```
   - Windows:
     ```bat
     run_tests.bat
     ```

5. **Ver el reporte de cobertura**
   1. Ejecuta los scripts anteriores (generan `htmlcov/`).
   2. Abre `htmlcov/index.html` en tu navegador favorito.

## Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).
