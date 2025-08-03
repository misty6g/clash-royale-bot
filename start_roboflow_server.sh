#!/bin/bash

echo "🚀 Starting Roboflow Inference Server for Clash Royale Bot..."
echo "This will enable full computer vision capabilities!"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    echo "You should see the Docker whale icon in your menu bar when it's ready."
    exit 1
fi

echo "✅ Docker is running!"
echo "🔄 Starting Roboflow inference server on port 9001..."
echo ""

# Start the Roboflow inference server
docker run --rm -it \
    -p 9001:9001 \
    --name roboflow-inference \
    roboflow/roboflow-inference-server-cpu:latest

echo ""
echo "🎉 Roboflow inference server started successfully!"
echo "Your Clash Royale bot now has full computer vision capabilities!"
