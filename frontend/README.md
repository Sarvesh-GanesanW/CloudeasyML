# Frontend Options

## Pure JavaScript Interface

A clean, modern dark-themed UI built with vanilla JavaScript and Chart.js.

### Features
- Real-time API status monitoring
- Interactive input forms
- Live charting with Chart.js
- Crisis detection visualization
- Policy recommendations display
- Zero dependencies except Chart.js CDN

### Usage

**Option 1: Open Directly**
```bash
open frontend/index.html
```

**Option 2: Serve with Python**
```bash
cd frontend
python -m http.server 8080
# Open http://localhost:8080
```

**Option 3: Serve with Node.js**
```bash
cd frontend
npx http-server -p 8080
# Open http://localhost:8080
```

### Requirements
- Modern web browser (Chrome, Firefox, Safari, Edge)
- API running on http://localhost:8000 (or configure endpoint)

## Jupyter Interface

Interactive notebook with three options:

### Option 1: Embedded HTML
- Embeds the full HTML interface inside Jupyter
- Best for full-featured UI in notebook

### Option 2: Pure Python Widgets
- Uses ipywidgets for native Jupyter controls
- Best for Python-native experience

### Option 3: Direct API
- Pure Python code cells
- Best for scripting and automation

### Setup
```bash
pip install ipywidgets plotly
jupyter nbextension enable --py widgetsnbextension
```

### Usage
```bash
jupyter notebook notebooks/interactive.ipynb
```

## API Configuration

Both interfaces connect to the FastAPI backend:

**Default:** `http://localhost:8000`

**Change in HTML:** Edit the input field in the Configuration card

**Change in Jupyter:** Modify the `apiUrl` variable

## Port Forwarding for Kubernetes

If API is running in Kubernetes:
```bash
kubectl port-forward svc/housing-crisis-inference 8000:80 -n ml-inference
```

Then access frontend at the URLs above.

## Screenshots

### HTML Interface
- Dark theme optimized for developers
- Responsive grid layout
- Real-time status indicators
- Interactive charts with Chart.js
- Crisis level color coding

### Jupyter Interface
- Native Jupyter widgets
- Plotly interactive charts
- Multiple interface options
- Easy to extend with code cells
