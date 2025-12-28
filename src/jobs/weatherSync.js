const cron = require('node-cron');
const axios = require('axios');
const SafetyZone = require('../models/SafetyZone');
const Alert = require('../models/Alert');
const Vessel = require('../models/Vessel');
const logger = require('../utils/logger');

// Sync weather data every 5 minutes
module.exports = (io) => {
  const syncWeatherData = async () => {
    try {
      logger.info('Starting weather data sync...');

      if (!process.env.WEATHER_API_KEY || !process.env.WEATHER_API_URL) {
        logger.warn('Weather API not configured');
        return;
      }

      // Get active vessels to check weather around them
      const vessels = await Vessel.find({
        status: { $in: ['underway', 'at_anchor'] }
      }).select('currentPosition name mmsi');

      // In production, fetch weather data from API
      // Example: OpenWeatherMap, WeatherAPI, etc.
      
      // For demo, create sample storm zones
      const existingStorms = await SafetyZone.find({ 
        type: 'storm', 
        isActive: true 
      });

      // Deactivate old storms (older than 12 hours)
      const twelveHoursAgo = new Date(Date.now() - 12 * 60 * 60 * 1000);
      await SafetyZone.updateMany(
        {
          type: 'storm',
          isActive: true,
          startDate: { $lt: twelveHoursAgo }
        },
        {
          isActive: false,
          endDate: new Date()
        }
      );

      // Check if vessels are in storm zones
      for (const vessel of vessels) {
        if (!vessel.currentPosition) continue;

        const nearbyStorms = await SafetyZone.find({
          type: 'storm',
          isActive: true,
          geometry: {
            $near: {
              $geometry: {
                type: 'Point',
                coordinates: [
                  vessel.currentPosition.longitude,
                  vessel.currentPosition.latitude
                ]
              },
              $maxDistance: 92600 // 50 nautical miles in meters
            }
          }
        });

        if (nearbyStorms.length > 0) {
          // Check if alert already exists
          const existingAlert = await Alert.findOne({
            type: 'weather',
            affectedVessels: vessel._id,
            status: 'active'
          });

          if (!existingAlert) {
            // Create new alert
            const alert = await Alert.create({
              type: 'weather',
              severity: nearbyStorms.some(s => s.severity === 'critical') ? 'critical' : 'warning',
              title: 'Storm Warning',
              message: `Vessel ${vessel.name} is near ${nearbyStorms.length} active storm zone(s)`,
              affectedVessels: [vessel._id],
              location: {
                latitude: vessel.currentPosition.latitude,
                longitude: vessel.currentPosition.longitude
              },
              targetRoles: ['operator', 'analyst', 'admin'],
              status: 'active',
              expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
              notifications: {
                email: true,
                inApp: true
              },
              metadata: {
                source: 'weather_sync',
                stormCount: nearbyStorms.length
              }
            });

            // Emit real-time alert
            io.emit('alert:created', alert);

            logger.info(`Weather alert created for vessel ${vessel.name}`);
          }
        }
      }

      logger.info('Weather data sync completed');
    } catch (error) {
      logger.error('Weather data sync error:', error);
    }
  };

  // Run every 5 minutes
  const interval = parseInt(process.env.WEATHER_POLLING_INTERVAL) || 300000;
  cron.schedule(`*/${interval / 60000} * * * *`, syncWeatherData);

  // Run immediately on startup
  syncWeatherData();
};
