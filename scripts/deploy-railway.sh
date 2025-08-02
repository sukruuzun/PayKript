#!/bin/bash

# PayKript Railway Deployment Script
# Bu script'i çalıştırmadan önce 'railway login' yapın

set -e

echo "🚂 PayKript Railway Deployment Starting..."

# Railway project varlığını kontrol et
if ! railway status &> /dev/null; then
    echo "📝 Creating new Railway project..."
    railway init --name paykript-production
else
    echo "✅ Railway project already exists"
fi

# PostgreSQL addon'ı ekle
echo "🗄️ Adding PostgreSQL database..."
if ! railway add postgresql; then
    echo "⚠️ PostgreSQL might already exist or error occurred"
fi

echo "🔧 Setting up environment variables..."

# Critical environment variables
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=INFO
railway variables set ALGORITHM=HS256
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES=60
railway variables set PAYMENT_TIMEOUT_MINUTES=15
railway variables set REQUIRED_CONFIRMATIONS=1
railway variables set USDT_CONTRACT_ADDRESS=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t

echo "⚠️ MANUAL SETUP REQUIRED:"
echo "Please set these environment variables manually in Railway dashboard:"
echo ""
echo "1. SECRET_KEY=your-very-secure-production-secret-key-at-least-32-chars"
echo "2. TRON_GRID_API_KEY=your-trongrid-api-key"
echo "3. WEBHOOK_SECRET=your-webhook-secret-key"
echo "4. ALLOWED_ORIGINS=https://your-domain.com"
echo ""
echo "To set variables run:"
echo 'railway variables set SECRET_KEY="your-secret-here"'
echo 'railway variables set TRON_GRID_API_KEY="your-api-key-here"'
echo 'railway variables set WEBHOOK_SECRET="your-webhook-secret-here"'
echo 'railway variables set ALLOWED_ORIGINS="https://your-domain.com"'
echo ""

read -p "Have you set all the required environment variables? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying to Railway..."
    railway up
    
    echo ""
    echo "✅ Deployment completed!"
    echo ""
    echo "🔗 Your PayKript API is now live!"
    echo "📊 Check status: railway status"
    echo "📝 View logs: railway logs"
    echo "🌐 Get URL: railway domain"
    echo ""
    echo "Next steps:"
    echo "1. Test health endpoint: curl https://your-app.railway.app/health"
    echo "2. Check API docs: https://your-app.railway.app/api/v1/docs"
    echo "3. Update WordPress plugin with production URL"
    echo ""
else
    echo "❌ Please set environment variables first, then run this script again"
    exit 1
fi 