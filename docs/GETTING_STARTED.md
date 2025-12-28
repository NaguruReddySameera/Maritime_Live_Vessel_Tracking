# Getting Started with Vessel Tracking System

## Prerequisites

- **Node.js** 18+ and npm
- **MongoDB** 6+
- API keys for external services (optional for demo):
  - AIS data provider
  - Weather API (OpenWeatherMap, etc.)
  - Piracy data feed

## Installation

### 1. Install Dependencies

```bash
# Install backend dependencies
npm install

# Install frontend dependencies
cd client
npm install
cd ..
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required Configuration:**
- `MONGODB_URI` - MongoDB connection string
- `JWT_SECRET` - Secret key for JWT tokens
- `JWT_REFRESH_SECRET` - Secret key for refresh tokens

**Optional Configuration:**
- External API keys (AIS, Weather, Piracy data)
  - `STORMGLASS_API_KEY` - StormGlass API key for marine weather data (optional)
  - `MARINETRAFFIC_API_KEY` - MarineTraffic API key (optional, falls back to free AISHub)
- Email configuration for notifications
- Polling intervals for data refresh

**Note:** The system uses **AISHub (FREE)** for real-time vessel tracking by default. No API key required for basic AIS vessel positions. The map displays real ships from live AIS data sources.

### 3. Setup Database

```bash
# Start MongoDB (if not running)
# Option 1: Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:6

# Option 2: System service
sudo systemctl start mongod

# Seed database with sample data
node src/database/seed.js
```

This will create:
- 3 test users (Admin, Analyst, Operator)
- 3 sample vessels
- 4 sample ports
- 2 safety zones

### 4. Run Development Server

```bash
# Terminal 1: Start backend
npm run dev

# Terminal 2: Start frontend
npm run client

# OR run both concurrently
npm run dev:full
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- API Health: http://localhost:5000/api/health

## Test Credentials

After seeding the database, use these credentials:

### Admin Account
- **Email:** admin@vesseltracking.com
- **Password:** Admin@123456
- **Capabilities:** Full system access

### Analyst Account
- **Email:** analyst@shipping.com
- **Password:** Analyst@123
- **Capabilities:** Analytics, reports, dashboards

### Operator Account
- **Email:** operator@shipping.com
- **Password:** Operator@123
- **Capabilities:** View vessels, add notes

## Project Structure

```
Live_tracking/
├── src/                      # Backend source code
│   ├── server.js            # Express server entry point
│   ├── models/              # MongoDB schemas
│   ├── routes/              # API route handlers
│   ├── middleware/          # Auth, validation, logging
│   ├── utils/               # Helper functions
│   ├── jobs/                # Cron jobs for data sync
│   └── database/            # Migration and seed scripts
├── client/                   # React frontend
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Page components
│   │   ├── store/           # Redux state management
│   │   └── services/        # API and Socket.IO clients
│   └── public/
├── logs/                     # Application logs
├── .env                      # Environment configuration
├── package.json
└── docker-compose.yml       # Docker deployment config
```

## Development Workflow

### Backend Development

```bash
# Run with auto-reload
npm run dev

# Run tests
npm test

# Check logs
tail -f logs/combined.log
```

### Frontend Development

```bash
cd client
npm start

# Build for production
npm run build
```

### Database Operations

```bash
# Seed database
node src/database/seed.js

# Clear and re-seed
# (Database will be cleared during seed)
```

## API Testing

Use tools like Postman or curl:

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@vesseltracking.com","password":"Admin@123456"}'

# Get vessels (with token)
curl -X GET http://localhost:5000/api/vessels \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Common Issues

### MongoDB Connection Error
```
Error: connect ECONNREFUSED 127.0.0.1:27017
```
**Solution:** Ensure MongoDB is running
```bash
sudo systemctl start mongod
# OR
docker start mongodb
```

### Port Already in Use
```
Error: listen EADDRINUSE: address already in use :::5000
```
**Solution:** Change PORT in .env or kill the process
```bash
lsof -ti:5000 | xargs kill -9
```

### CORS Errors
**Solution:** Check `CLIENT_URL` in .env matches your frontend URL

## Next Steps

1. **Configure External APIs** - Add your API keys to `.env`
2. **Customize Data** - Add your vessels and ports via API or seed script
3. **Setup Email** - Configure SMTP for alert notifications
4. **Deploy** - See deployment guide below

## Deployment

### Using Docker

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Deployment

1. **Build frontend:**
```bash
cd client
npm run build
cd ..
```

2. **Set environment to production:**
```bash
export NODE_ENV=production
```

3. **Start with PM2:**
```bash
npm install -g pm2
pm2 start src/server.js --name vessel-tracking
pm2 save
```

## Support

For issues or questions:
1. Check the troubleshooting section in README.md
2. Review API documentation in docs/API.md
3. Check application logs in `logs/` directory
