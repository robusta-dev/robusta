#!/bin/sh
kubectl apply -f ./crashpodv1.yaml 
read -p "Press enter to change Deployment..."
kubectl apply -f ./crashpodv2_broken.yaml

read -p "Press enter to cleanup..."
kubectl delete deployment crashpod
