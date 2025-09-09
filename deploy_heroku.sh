#!/bin/bash

# Heroku Deployment Script for S&P 500 Price Dip Analysis App

echo "🚀 Deploying S&P 500 Price Dip Analysis App to Heroku..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Please install it first:"
    echo "   brew install heroku/brew/heroku"
    exit 1
fi

# Check if user is logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "🔐 Please login to Heroku first:"
    echo "   heroku login"
    exit 1
fi

# Get app name from user
read -p "Enter your Heroku app name (or press Enter to create new): " APP_NAME

if [ -z "$APP_NAME" ]; then
    echo "Creating new Heroku app..."
    heroku create
    APP_NAME=$(heroku apps --json | jq -r '.[0].name')
    echo "✅ Created app: $APP_NAME"
else
    echo "Using existing app: $APP_NAME"
    heroku git:remote -a $APP_NAME
fi

# Add data files to git (if not already)
echo "📁 Adding data files to git..."
git add data/
git commit -m "Add S&P 500 data files" || echo "Data files already committed"

# Deploy to Heroku
echo "🚀 Deploying to Heroku..."
git push heroku main

# Open the app
echo "🌐 Opening your app..."
heroku open -a $APP_NAME

echo "✅ Deployment complete!"
echo "📊 Your S&P 500 Price Dip Analysis App is now live at:"
echo "   https://$APP_NAME.herokuapp.com"
