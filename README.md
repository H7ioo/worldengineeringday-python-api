# Istanbul Seismic Risk API

A high-performance **FastAPI** backend designed to calculate and serve neighborhood-level seismic risk data for Istanbul. This project was developed as part of the "Resilient Cities" initiative for the World Engineering Day Hackathon.

## 🚀 Quick Start (Local)

1. **Install Dependencies**:

```bash
pip install fastapi uvicorn pandas scikit-learn numpy

```

2. **Prepare Data**:
   Ensure your `master_datasheet.csv` is in the same directory as `main.py`.
3. **Run Server**:

```bash
python main.py

```

The API will be live at `http://localhost:8000`

---

## 🛠 Features

- **Dynamic Risk Engine**: Recalculates risk scores on-the-fly based on custom weights for Human Life, Infrastructure, and Building Integrity.
- **Data-Rich Response**: Provides detailed building inventory (age/floor distribution), seismic impact projections, and geolocation data.
- **Normalization**: Uses `MinMaxScaler` to ensure fair priority scoring across different urban metrics.

---

## 📡 API Endpoints

### `GET /neighborhoods-priority`

Fetches the full priority list of Istanbul neighborhoods.

**Query Parameters (Optional):**
| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `w_lives` | float | 0.5 | Weight assigned to life density / casualties. |
| `w_buildings` | float | 0.3 | Weight assigned to structural fragility. |
| `w_infra` | float | 0.2 | Weight assigned to pipeline/infrastructure damage. |

**Example Usage:**
`GET /neighborhoods-priority?w_lives=0.7&w_buildings=0.2&w_infra=0.1`

---

## 📂 Project Structure

- `main.py`: The core FastAPI application and calculation logic.
- `master_datasheet.csv`: The processed dataset containing seismic scenario results.
- `requirements.txt`: List of Python dependencies for deployment.

---

## ☁️ Deployment (Render)

This backend is optimized for **Render**.

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
