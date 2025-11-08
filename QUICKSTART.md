# CloudEasyML Quick Start

Get your ML models deployed in 5 minutes.

## Installation

```bash
git clone https://github.com/yourusername/CloudEasyML.git
cd CloudEasyML
pip install -r requirements.txt
```

## Start the Server

```bash
python3 server.py
```

You should see:
```
======================================================================
CloudEasyML Server Starting...
======================================================================

API Endpoints:
  - Health Check:    http://localhost:8000/health
  - List Models:     http://localhost:8000/models
  - Admin Dashboard: http://localhost:8000/admin

Press Ctrl+C to stop
======================================================================
```

## Step 1: Create an API Key

```bash
curl -X POST "http://localhost:8000/api-keys?userId=demo_user" \
  -H "Content-Type: application/json" \
  -d '{"name": "My First Key", "rateLimit": 1000}'
```

Save the returned API key securely!

## Step 2: Create a Deployment

```bash
curl -X POST http://localhost:8000/deployments \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "modelName": "housingCrisis",
    "modelVersion": "1.0.0",
    "config": {}
  }'
```

Save the `deploymentId` from the response.

## Step 3: Make a Prediction

```bash
curl -X POST http://localhost:8000/predict \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "deploymentId": "YOUR_DEPLOYMENT_ID",
    "data": [{"GDP": 25000, "UNRATE": 5.5, "FEDFUNDS": 4.5}],
    "options": {"crisisDetection": true}
  }'
```

## Step 4: Check Usage

```bash
curl http://localhost:8000/usage \
  -H "Authorization: Bearer YOUR_API_KEY_HERE"
```

## Web Dashboard

Open your browser to `http://localhost:8000/admin` for a visual interface.

## API Documentation

Interactive API docs: `http://localhost:8000/docs`

## Create Your Own Plugin

See `docs/PLUGIN_GUIDE.md` for a complete tutorial on creating custom model plugins.

## Next Steps

- Read the full documentation in `README.md`
- Explore the example plugin in `plugins/housingCrisis/`
- Deploy to cloud: `./deploy/aws/deploy.sh`
- Join the community on GitHub Discussions

## Troubleshooting

### Server won't start

Check that all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Can't create deployment

Make sure the model name matches an available plugin:
```bash
curl http://localhost:8000/models
```

### Rate limit exceeded

Increase the rate limit when creating your API key:
```bash
curl -X POST "http://localhost:8000/api-keys?userId=demo_user" \
  -d '{"name": "High Limit Key", "rateLimit": 10000}'
```

## Support

- Documentation: `README.md`
- Plugin Guide: `docs/PLUGIN_GUIDE.md`
- Issues: GitHub Issues
- Examples: `plugins/`
