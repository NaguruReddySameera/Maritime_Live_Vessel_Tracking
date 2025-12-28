const express = require('express');
const router = express.Router();
const SafetyZone = require('../models/SafetyZone');
const Alert = require('../models/Alert');
const { protect, authorize } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');

// @route   GET /api/safety/piracy
// @desc    Get piracy zones
// @access  Private
router.get('/piracy',
  protect,
  asyncHandler(async (req, res) => {
    const zones = await SafetyZone.find({
      type: 'piracy',
      isActive: true
    }).select('-__v');

    res.status(200).json({
      success: true,
      count: zones.length,
      zones
    });
  })
);

// @route   GET /api/safety/weather
// @desc    Get weather zones/warnings
// @access  Private
router.get('/weather',
  protect,
  asyncHandler(async (req, res) => {
    const zones = await SafetyZone.find({
      type: 'storm',
      isActive: true
    }).select('-__v');

    res.status(200).json({
      success: true,
      count: zones.length,
      zones
    });
  })
);

// @route   GET /api/safety/incidents
// @desc    Get accident hotspots
// @access  Private
router.get('/incidents',
  protect,
  asyncHandler(async (req, res) => {
    const { startDate, endDate, severity } = req.query;

    const query = {
      type: 'accident',
      isActive: true
    };

    if (severity) query.severity = severity;

    if (startDate || endDate) {
      query['metadata.incidentDate'] = {};
      if (startDate) query['metadata.incidentDate'].$gte = new Date(startDate);
      if (endDate) query['metadata.incidentDate'].$lte = new Date(endDate);
    }

    const incidents = await SafetyZone.find(query).select('-__v');

    res.status(200).json({
      success: true,
      count: incidents.length,
      incidents
    });
  })
);

// @route   GET /api/safety/zones
// @desc    Get all safety zones in area
// @access  Private
router.get('/zones',
  protect,
  asyncHandler(async (req, res) => {
    const { latitude, longitude, radius = 100 } = req.query;

    if (!latitude || !longitude) {
      return res.status(400).json({ message: 'Latitude and longitude required' });
    }

    // Find zones near the specified location
    // Convert radius from nautical miles to meters (1 NM ≈ 1852 meters)
    const radiusInMeters = parseFloat(radius) * 1852;

    const zones = await SafetyZone.find({
      isActive: true,
      geometry: {
        $near: {
          $geometry: {
            type: 'Point',
            coordinates: [parseFloat(longitude), parseFloat(latitude)]
          },
          $maxDistance: radiusInMeters
        }
      }
    });

    res.status(200).json({
      success: true,
      count: zones.length,
      zones
    });
  })
);

// @route   GET /api/safety/alerts
// @desc    Get active alerts for user
// @access  Private
router.get('/alerts',
  protect,
  asyncHandler(async (req, res) => {
    const { type, severity, status = 'active' } = req.query;

    const query = {
      status,
      $or: [
        { targetUsers: req.user._id },
        { targetRoles: req.user.role },
        { targetCompanies: req.user.company }
      ]
    };

    if (type) query.type = type;
    if (severity) query.severity = severity;

    const alerts = await Alert.find(query)
      .populate('affectedVessels', 'name mmsi')
      .populate('affectedPorts', 'name code')
      .sort({ createdAt: -1 })
      .limit(50);

    res.status(200).json({
      success: true,
      count: alerts.length,
      alerts
    });
  })
);

// @route   GET /api/safety/analytics/risks
// @desc    Get risk analytics (Analyst+)
// @access  Private/Analyst
router.get('/analytics/risks',
  protect,
  authorize('analyst', 'admin'),
  asyncHandler(async (req, res) => {
    const { region, startDate, endDate } = req.query;

    const query = { isActive: true };

    if (startDate || endDate) {
      query.createdAt = {};
      if (startDate) query.createdAt.$gte = new Date(startDate);
      if (endDate) query.createdAt.$lte = new Date(endDate);
    }

    // Aggregate risk data by type and severity
    const risksByType = await SafetyZone.aggregate([
      { $match: query },
      { 
        $group: {
          _id: { type: '$type', severity: '$severity' },
          count: { $sum: 1 }
        }
      },
      { $sort: { '_id.type': 1, '_id.severity': 1 } }
    ]);

    // Count active alerts
    const alertCounts = await Alert.aggregate([
      { $match: { status: 'active' } },
      {
        $group: {
          _id: { type: '$type', severity: '$severity' },
          count: { $sum: 1 }
        }
      }
    ]);

    res.status(200).json({
      success: true,
      risksByType,
      alertCounts
    });
  })
);

// @route   POST /api/safety/zones
// @desc    Create safety zone (Admin only)
// @access  Private/Admin
router.post('/zones',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const zone = await SafetyZone.create(req.body);

    // Create alert if severity is high or critical
    if (['high', 'critical'].includes(zone.severity)) {
      await Alert.create({
        type: zone.type,
        severity: zone.severity === 'critical' ? 'critical' : 'warning',
        title: zone.title,
        message: zone.description,
        location: {
          latitude: zone.geometry.coordinates[0][0][1],
          longitude: zone.geometry.coordinates[0][0][0]
        },
        targetRoles: ['operator', 'analyst', 'admin'],
        status: 'active'
      });
    }

    // Emit real-time update
    const io = req.app.get('io');
    io.emit('safety:zone:created', { zone });

    res.status(201).json({
      success: true,
      message: 'Safety zone created',
      zone
    });
  })
);

// @route   PUT /api/safety/zones/:id
// @desc    Update safety zone (Admin only)
// @access  Private/Admin
router.put('/zones/:id',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const zone = await SafetyZone.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true, runValidators: true }
    );

    if (!zone) {
      return res.status(404).json({ message: 'Safety zone not found' });
    }

    // Emit real-time update
    const io = req.app.get('io');
    io.emit('safety:zone:updated', { zone });

    res.status(200).json({
      success: true,
      message: 'Safety zone updated',
      zone
    });
  })
);

// @route   DELETE /api/safety/zones/:id
// @desc    Delete safety zone (Admin only)
// @access  Private/Admin
router.delete('/zones/:id',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const zone = await SafetyZone.findByIdAndDelete(req.params.id);

    if (!zone) {
      return res.status(404).json({ message: 'Safety zone not found' });
    }

    res.status(200).json({
      success: true,
      message: 'Safety zone deleted'
    });
  })
);

module.exports = router;
