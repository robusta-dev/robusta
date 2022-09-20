#!/bin/sh
kubectl apply -f ./crashpodv1.yaml 
read -p "Press enter to change Deployment..."
kubectl apply -f ./crashpodv2_broken.yaml

echo "\nWaiting 60 seconds"
sleep 60
echo "Done waiting. Check your Slack channel and the Robusta UI"

read -p "Press enter to cleanup..."
kubectl delete deployment crashpod
