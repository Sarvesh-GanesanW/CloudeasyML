#!/bin/bash
set -e

MODE=${1:-serve}

case "$MODE" in
  serve)
    echo "Starting inference server..."
    exec python /app/src/api/server.py
    ;;

  train)
    echo "Running training pipeline..."
    exec python /app/main.py --mode train "$@"
    ;;

  predict)
    echo "Running prediction pipeline..."
    exec python /app/main.py --mode predict "$@"
    ;;

  job)
    echo "Running batch job..."
    exec python /app/src/jobs/batchJob.py "$@"
    ;;

  bash)
    exec /bin/bash
    ;;

  *)
    echo "Unknown mode: $MODE"
    echo "Available modes: serve, train, predict, job, bash"
    exit 1
    ;;
esac
