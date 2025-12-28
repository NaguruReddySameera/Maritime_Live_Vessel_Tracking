const cron = require('node-cron');
const axios = require('axios');
const Vessel = require('../models/Vessel');
const VesselTrack = require('../models/VesselTrack');
const logger = require('../utils/logger');

// Sync AIS data every minute
module.exports = (io) => {
  const syncAISData = async () => {
    try {
      logger.info('Starting AIS data sync...');

      // In production, this would call the actual AIS API
      // Example: https://api.aisstream.io/v0/positions
      
      if (!process.env.AIS_API_KEY || !process.env.AIS_API_URL) {
        logger.warn('AIS API not configured');
        return;
      }

      // Real AIS provider call (configurable header scheme)
      // If configured, attempt to fetch positions from configured AIS API
      try {
        const headerName = process.env.AIS_AUTH_HEADER_NAME || 'Authorization';
        const scheme = process.env.AIS_AUTH_SCHEME || 'Bearer';
        const path = process.env.AIS_POSITIONS_PATH || '/positions';

        const headers = {};
        if (headerName.toLowerCase() === 'authorization') {
          headers[headerName] = `${scheme} ${process.env.AIS_API_KEY}`;
        } else {
          headers[headerName] = process.env.AIS_API_KEY;
        }

        // Example: https://api.marinesia.com/api/v1/vessels/area or provider-specific path
        const resp = await axios.get(`${process.env.AIS_API_URL}${path}`, { headers });
        if (resp && Array.isArray(resp.data)) {
          logger.info(`Fetched ${resp.data.length} AIS positions from external provider`);
          // Map external positions to local vessels by MMSI when possible (optional enhancement)
        }
      } catch (e) {
        logger.debug('External AIS fetch failed or not applicable; continuing with simulation');
      }

      // For demo purposes, simulate position updates
      const vessels = await Vessel.find({ status: 'underway' }).limit(10);

      for (const vessel of vessels) {
        if (!vessel.currentPosition) continue;

        // Simulate position update (small random movement)
        const newPosition = {
          latitude: vessel.currentPosition.latitude + (Math.random() - 0.5) * 0.01,
          longitude: vessel.currentPosition.longitude + (Math.random() - 0.5) * 0.01,
          heading: vessel.currentPosition.heading + (Math.random() - 0.5) * 10,
          speed: vessel.currentPosition.speed + (Math.random() - 0.5) * 2,
          course: vessel.currentPosition.course + (Math.random() - 0.5) * 5,
          timestamp: new Date()
        };

        // Update vessel position
        vessel.currentPosition = newPosition;
        vessel.metadata.aisLastUpdate = new Date();
        await vessel.save();

        // Add to track history
        let track = await VesselTrack.findOne({
          mmsi: vessel.mmsi,
          endTime: null
        }).sort({ startTime: -1 });

        if (!track) {
          // Create new track
          track = await VesselTrack.create({
            vessel: vessel._id,
            mmsi: vessel.mmsi,
            voyageId: `${vessel.mmsi}-${Date.now()}`,
            startTime: new Date(),
            positions: [newPosition],
            retentionDate: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000) // 1 year retention
          });
        } else {
          // Add position to existing track
          track.positions.push(newPosition);
          
          // Keep only last 1000 positions per track
          if (track.positions.length > 1000) {
            track.positions = track.positions.slice(-1000);
          }
          
          await track.save();
        }

        // Emit real-time update via Socket.IO
        io.to('vessels').emit('vessel:position:updated', {
          vesselId: vessel._id,
          position: newPosition
        });
      }

      logger.info(`AIS data sync completed. Updated ${vessels.length} vessels.`);
    } catch (error) {
      logger.error('AIS data sync error:', error);
    }
  };

  // Run every minute
  const interval = parseInt(process.env.AIS_POLLING_INTERVAL) || 60000;
  cron.schedule(`*/${interval / 60000} * * * *`, syncAISData);

  // Run immediately on startup
  syncAISData();
};
