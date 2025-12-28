const cron = require('node-cron');
const axios = require('axios');
const Port = require('../models/Port');
const Vessel = require('../models/Vessel');
const logger = require('../utils/logger');

// Sync port congestion data every 10 minutes
module.exports = (io) => {
  const syncCongestionData = async () => {
    try {
      logger.info('Starting port congestion sync...');

      const ports = await Port.find({});

      for (const port of ports) {
        // In production, fetch data from port authority API
        // For demo, calculate based on nearby vessels

        const vessels = await Vessel.find({
          $or: [
            { 'destination.port': port.name },
            {
              status: { $in: ['at_anchor', 'moored'] },
              'currentPosition.latitude': {
                $gte: port.location.latitude - 0.5,
                $lte: port.location.latitude + 0.5
              },
              'currentPosition.longitude': {
                $gte: port.location.longitude - 0.5,
                $lte: port.location.longitude + 0.5
              }
            }
          ]
        });

        const vesselsWaiting = vessels.filter(v => v.status === 'at_anchor').length;
        const vesselsBerthed = vessels.filter(v => v.status === 'moored').length;
        
        // Calculate congestion status
        let status = 'green';
        let averageWaitTime = 0;

        if (port.capacity && port.capacity.maxVessels) {
          const utilizationPercent = (vesselsBerthed / port.capacity.maxVessels) * 100;
          
          if (utilizationPercent > 80) {
            status = 'red';
            averageWaitTime = 12 + Math.random() * 12; // 12-24 hours
          } else if (utilizationPercent > 60) {
            status = 'yellow';
            averageWaitTime = 4 + Math.random() * 8; // 4-12 hours
          } else {
            status = 'green';
            averageWaitTime = Math.random() * 4; // 0-4 hours
          }
        } else {
          // No capacity data, use waiting vessels as indicator
          if (vesselsWaiting > 10) {
            status = 'red';
            averageWaitTime = 12 + Math.random() * 12;
          } else if (vesselsWaiting > 5) {
            status = 'yellow';
            averageWaitTime = 4 + Math.random() * 8;
          } else {
            status = 'green';
            averageWaitTime = Math.random() * 4;
          }
        }

        // Update port congestion
        const previousStatus = port.currentCongestion.status;

        port.currentCongestion = {
          status,
          vesselsWaiting,
          averageWaitTime: Math.round(averageWaitTime * 10) / 10,
          lastUpdated: new Date()
        };

        // Add to history
        port.congestionHistory.push({
          timestamp: new Date(),
          vesselsWaiting,
          averageWaitTime: Math.round(averageWaitTime * 10) / 10,
          status
        });

        // Keep only last 30 days of history
        const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
        port.congestionHistory = port.congestionHistory.filter(
          h => new Date(h.timestamp) > thirtyDaysAgo
        );

        await port.save();

        // Emit real-time update
        io.to(`port:${port._id}`).emit('port:congestion:updated', {
          portId: port._id,
          congestion: port.currentCongestion
        });

        // Create alert if status changed to red
        if (status === 'red' && previousStatus !== 'red') {
          const Alert = require('../models/Alert');
          await Alert.create({
            type: 'congestion',
            severity: 'warning',
            title: 'High Port Congestion',
            message: `Port ${port.name} is experiencing high congestion with ${vesselsWaiting} vessels waiting`,
            affectedPorts: [port._id],
            location: {
              latitude: port.location.latitude,
              longitude: port.location.longitude
            },
            targetRoles: ['operator', 'analyst', 'admin'],
            status: 'active',
            expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
            notifications: {
              email: false,
              inApp: true
            },
            metadata: {
              source: 'congestion_sync',
              vesselsWaiting,
              averageWaitTime
            }
          });

          logger.info(`Congestion alert created for port ${port.name}`);
        }
      }

      logger.info(`Port congestion sync completed. Updated ${ports.length} ports.`);
    } catch (error) {
      logger.error('Port congestion sync error:', error);
    }
  };

  // Run every 10 minutes
  cron.schedule('*/10 * * * *', syncCongestionData);

  // Run immediately on startup
  syncCongestionData();
};
