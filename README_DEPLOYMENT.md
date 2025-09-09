# 🚀 S&P 500 Price Dip Analysis App - Deployment Guide

## Quick Deploy Options

### Option 1: Heroku (Recommended)
```bash
# 1. Install Heroku CLI
brew install heroku/brew/heroku

# 2. Login to Heroku
heroku login

# 3. Run deployment script
./deploy_heroku.sh
```

### Option 2: Railway
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Railway will auto-detect Flask and deploy

### Option 3: Render
1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub repository
4. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

## Manual Heroku Deployment

```bash
# 1. Initialize git (if not already)
git init
git add .
git commit -m "Initial commit"

# 2. Create Heroku app
heroku create your-app-name

# 3. Deploy
git push heroku main

# 4. Open app
heroku open
```

## Environment Variables (Optional)

Set these in your hosting platform:
- `PORT`: Port number (usually auto-set)
- `FLASK_ENV`: Set to `production` for production

## Data Files

The app includes sample S&P 500 data in the `data/` folder:
- `sp500_companies.csv` - Company information
- `sp500_stocks.csv` - Stock price data
- `sp500_index.csv` - Index data

## Features

✅ **Price Dip Detection**: Find stocks with significant daily declines
✅ **Recovery Analysis**: Calculate days to recover 10%, 15%, 20%, 30%+
✅ **Interactive Dashboard**: Real-time metrics and filtering
✅ **Stock History**: Individual stock price charts and tables
✅ **Responsive Design**: Works on desktop and mobile

## API Endpoints

- `GET /` - Main dashboard
- `GET /stock_history` - Stock history page
- `GET /api/stats` - Basic statistics
- `GET /api/significant_declines` - Decline data with recovery times
- `GET /api/recovery_stats` - Recovery statistics
- `GET /api/stocks` - Available stocks list
- `GET /api/stock_history?symbol=AAPL` - Individual stock data

## Support

For issues or questions, check the main README.md file.
