const express = require('express');
const router = express.Router();
const VesselTrack = require('../models/VesselTrack');
const Vessel = require('../models/Vessel');
const Port = require('../models/Port');
const { protect, authorize } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');
const { analyticsValidation, validate } = require('../middleware/validation');
const { createObjectCsvWriter } = require('csv-writer');
const path = require('path');
const fs = require('fs');

// @route   GET /api/analytics/voyages
// @desc    Get voyage analytics (Analyst+)
// @access  Private/Analyst
router.get('/voyages',
  protect,
  authorize('analyst', 'admin'),
  analyticsValidation.dateRange,
  validate,
  asyncHandler(async (req, res) => {
    const { startDate, endDate, vesselId, company } = req.query;

    const query = {};

    if (startDate || endDate) {
      query.startTime = {};
      if (startDate) query.startTime.$gte = new Date(startDate);
      if (endDate) query.startTime.$lte = new Date(endDate);
    }

    if (vesselId) {
      query.vessel = vesselId;
    }

    // Join with vessels to filter by company
    const matchStage = vesselId ? { _id: vesselId } : {};
    if (company) matchStage.company = company;
    if (req.user.role !== 'admin') matchStage.company = req.user.company;

    const vessels = await Vessel.find(matchStage).select('_id mmsi');
    const mmsiList = vessels.map(v => v.mmsi);

    if (mmsiList.length === 0) {
      return res.status(200).json({
        success: true,
        count: 0,
        voyages: []
      });
    }

    query.mmsi = { $in: mmsiList };

    const voyages = await VesselTrack.find(query)
      .populate('vessel', 'name imo mmsi company')
      .sort({ startTime: -1 })
      .limit(100);

    // Calculate voyage statistics
    const statistics = voyages.map(voyage => {
      const positions = voyage.positions;
      if (positions.length === 0) return null;

      const duration = voyage.endTime 
        ? (new Date(voyage.endTime) - new Date(voyage.startTime)) / 1000 / 3600 // hours
        : null;

      const totalDistance = positions.reduce((sum, pos, i) => {
        if (i === 0) return 0;
        const prev = positions[i - 1];
        return sum + calculateDistance(
          prev.latitude, prev.longitude,
          pos.latitude, pos.longitude
        );
      }, 0);

      const avgSpeed = positions.reduce((sum, p) => sum + (p.speed || 0), 0) / positions.length;

      return {
        voyageId: voyage.voyageId,
        vessel: voyage.vessel,
        startTime: voyage.startTime,
        endTime: voyage.endTime,
        duration,
        distance: totalDistance.toFixed(2),
        avgSpeed: avgSpeed.toFixed(2),
        positionCount: positions.length
      };
    }).filter(v => v !== null);

    res.status(200).json({
      success: true,
      count: statistics.length,
      voyages: statistics
    });
  })
);

// @route   GET /api/analytics/routes
// @desc    Get route optimization analytics (Analyst+)
// @access  Private/Analyst
router.get('/routes',
  protect,
  authorize('analyst', 'admin'),
  asyncHandler(async (req, res) => {
    const { origin, destination, startDate, endDate } = req.query;

    // Find voyages matching origin/destination
    // This is a simplified version - in production, you'd use more sophisticated matching
    const query = {};
    if (startDate || endDate) {
      query.startTime = {};
      if (startDate) query.startTime.$gte = new Date(startDate);
      if (endDate) query.startTime.$lte = new Date(endDate);
    }

    const voyages = await VesselTrack.find(query)
      .populate('vessel', 'name imo company')
      .limit(50);

    // Analyze routes
    const routeAnalysis = voyages.map(voyage => {
      if (voyage.positions.length < 2) return null;

      const start = voyage.positions[0];
      const end = voyage.positions[voyage.positions.length - 1];

      // Calculate total distance
      let totalDistance = 0;
      for (let i = 1; i < voyage.positions.length; i++) {
        const prev = voyage.positions[i - 1];
        const curr = voyage.positions[i];
        totalDistance += calculateDistance(
          prev.latitude, prev.longitude,
          curr.latitude, curr.longitude
        );
      }

      const duration = (new Date(end.timestamp) - new Date(start.timestamp)) / 1000 / 3600;
      const avgSpeed = totalDistance / duration;

      return {
        voyageId: voyage.voyageId,
        vessel: voyage.vessel,
        origin: { lat: start.latitude, lng: start.longitude },
        destination: { lat: end.latitude, lng: end.longitude },
        distance: totalDistance.toFixed(2),
        duration: duration.toFixed(2),
        avgSpeed: avgSpeed.toFixed(2)
      };
    }).filter(r => r !== null);

    res.status(200).json({
      success: true,
      count: routeAnalysis.length,
      routes: routeAnalysis
    });
  })
);

// @route   GET /api/analytics/risks
// @desc    Get risk assessments (Analyst+)
// @access  Private/Analyst
router.get('/risks',
  protect,
  authorize('analyst', 'admin'),
  asyncHandler(async (req, res) => {
    const { vesselId, region, riskType } = req.query;

    // Get vessels
    const vesselQuery = {};
    if (vesselId) vesselQuery._id = vesselId;
    if (req.user.role !== 'admin') vesselQuery.company = req.user.company;

    const vessels = await Vessel.find(vesselQuery)
      .select('name imo currentPosition status company');

    // Calculate risk scores based on various factors
    const SafetyZone = require('../models/SafetyZone');
    const riskAssessments = await Promise.all(vessels.map(async vessel => {
      if (!vessel.currentPosition) return null;

      // Check proximity to safety zones
      const nearbyZones = await SafetyZone.find({
        isActive: true,
        geometry: {
          $near: {
            $geometry: {
              type: 'Point',
              coordinates: [vessel.currentPosition.longitude, vessel.currentPosition.latitude]
            },
            $maxDistance: 185200 // 100 nautical miles in meters
          }
        }
      });

      // Calculate risk score
      let riskScore = 0;
      const riskFactors = [];

      nearbyZones.forEach(zone => {
        if (zone.type === 'piracy') {
          riskScore += zone.severity === 'critical' ? 40 : zone.severity === 'high' ? 30 : 20;
          riskFactors.push(`Piracy zone (${zone.severity})`);
        } else if (zone.type === 'storm') {
          riskScore += zone.severity === 'critical' ? 35 : zone.severity === 'high' ? 25 : 15;
          riskFactors.push(`Storm (${zone.severity})`);
        } else if (zone.type === 'accident') {
          riskScore += 15;
          riskFactors.push('Accident hotspot');
        }
      });

      // Add other risk factors
      if (vessel.status === 'not_under_command') {
        riskScore += 25;
        riskFactors.push('Not under command');
      }

      return {
        vessel: {
          id: vessel._id,
          name: vessel.name,
          imo: vessel.imo,
          company: vessel.company
        },
        riskScore: Math.min(riskScore, 100),
        riskLevel: riskScore > 70 ? 'high' : riskScore > 40 ? 'medium' : 'low',
        riskFactors,
        nearbyZonesCount: nearbyZones.length
      };
    }));

    const validAssessments = riskAssessments.filter(r => r !== null);

    res.status(200).json({
      success: true,
      count: validAssessments.length,
      riskAssessments: validAssessments.sort((a, b) => b.riskScore - a.riskScore)
    });
  })
);

// @route   POST /api/analytics/export
// @desc    Export analytics data (Analyst+)
// @access  Private/Analyst
router.post('/export',
  protect,
  authorize('analyst', 'admin'),
  asyncHandler(async (req, res) => {
    const { dataType, filters, format = 'csv' } = req.body;

    if (!['csv', 'excel'].includes(format)) {
      return res.status(400).json({ message: 'Invalid format. Use csv or excel' });
    }

    let data = [];
    let filename = '';

    // Fetch data based on type
    switch (dataType) {
      case 'vessels':
        const vessels = await Vessel.find(filters || {})
          .select('name imo mmsi company status currentPosition destination');
        data = vessels.map(v => ({
          Name: v.name,
          IMO: v.imo,
          MMSI: v.mmsi,
          Company: v.company,
          Status: v.status,
          Latitude: v.currentPosition?.latitude || '',
          Longitude: v.currentPosition?.longitude || '',
          Speed: v.currentPosition?.speed || '',
          Destination: v.destination?.port || ''
        }));
        filename = `vessels_${Date.now()}.csv`;
        break;

      case 'ports':
        const ports = await Port.find(filters || {})
          .select('name code country currentCongestion');
        data = ports.map(p => ({
          Name: p.name,
          Code: p.code,
          Country: p.country,
          Status: p.currentCongestion?.status || '',
          VesselsWaiting: p.currentCongestion?.vesselsWaiting || 0,
          AvgWaitTime: p.currentCongestion?.averageWaitTime || 0
        }));
        filename = `ports_${Date.now()}.csv`;
        break;

      default:
        return res.status(400).json({ message: 'Invalid data type' });
    }

    if (data.length === 0) {
      return res.status(404).json({ message: 'No data to export' });
    }

    // Create CSV
    const exportDir = path.join(__dirname, '../../exports');
    if (!fs.existsSync(exportDir)) {
      fs.mkdirSync(exportDir, { recursive: true });
    }

    const filePath = path.join(exportDir, filename);
    const csvWriter = createObjectCsvWriter({
      path: filePath,
      header: Object.keys(data[0]).map(key => ({ id: key, title: key }))
    });

    await csvWriter.writeRecords(data);

    res.download(filePath, filename, (err) => {
      if (err) {
        console.error('Download error:', err);
      }
      // Clean up file after download
      fs.unlinkSync(filePath);
    });
  })
);

// Helper function to calculate distance between two coordinates (Haversine formula)
function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 3440.065; // Radius of Earth in nautical miles
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function toRad(degrees) {
  return degrees * (Math.PI / 180);
}

module.exports = router;
