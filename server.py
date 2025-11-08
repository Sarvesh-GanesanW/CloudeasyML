from core.api.apiServer import ApiServer

if __name__ == "__main__":
    server = ApiServer(pluginsPath="plugins", dbPath="data/db")
    print("=" * 70)
    print("CloudEasyML Server Starting...")
    print("=" * 70)
    print("\nAPI Endpoints:")
    print("  - Health Check:    http://localhost:8000/health")
    print("  - List Models:     http://localhost:8000/models")
    print("  - Admin Dashboard: http://localhost:8000/admin")
    print("\nPress Ctrl+C to stop")
    print("=" * 70)
    server.run(host="0.0.0.0", port=8000)
