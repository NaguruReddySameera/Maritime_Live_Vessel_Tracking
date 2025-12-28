const express = require('express');
const router = express.Router();
const Port = require('../models/Port');
const { protect, authorize, checkPortAccess } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');
const logger = require('../utils/logger');

// @route   GET /api/ports
// @desc    Get all ports with congestion status
// @access  Private
router.get('/',
  protect,
  asyncHandler(async (req, res) => {
    const { region, country, status, search, page = 1, limit = 50 } = req.query;

    const query = {};

    // Filter by permissions
    if (req.user.role !== 'admin' && !req.user.permissions.ports.includes('all')) {
      query._id = { $in: req.user.permissions.ports };
    }

    if (region) query.region = region;
    if (country) query.country = country;
    if (status) query['currentCongestion.status'] = status;
    
    if (search) {
      query.$or = [
        { name: { $regex: search, $options: 'i' } },
        { code: { $regex: search, $options: 'i' } }
      ];
    }

    const ports = await Port.find(query)
      .select('-congestionHistory') // Exclude history for list view
      .limit(limit * 1)
      .skip((page - 1) * limit)
      .sort({ name: 1 });

    const count = await Port.countDocuments(query);

    res.status(200).json({
      success: true,
      count,
      totalPages: Math.ceil(count / limit),
      currentPage: parseInt(page),
      ports
    });
  })
);

// @route   GET /api/ports/:id
// @desc    Get port details
// @access  Private
router.get('/:id',
  protect,
  checkPortAccess,
  asyncHandler(async (req, res) => {
    const port = await Port.findById(req.params.id);

    if (!port) {
      return res.status(404).json({ message: 'Port not found' });
    }

    res.status(200).json({
      success: true,
      port
    });
  })
);

// @route   GET /api/ports/:id/congestion
// @desc    Get detailed congestion data for port
// @access  Private
router.get('/:id/congestion',
  protect,
  checkPortAccess,
  asyncHandler(async (req, res) => {
    const port = await Port.findById(req.params.id)
      .select('name code currentCongestion');

    if (!port) {
      return res.status(404).json({ message: 'Port not found' });
    }

    // Get vessels currently at or heading to this port
    const Vessel = require('../models/Vessel');
    const vesselsInPort = await Vessel.countDocuments({
      $or: [
        { 'destination.port': port.name },
        { status: 'at_anchor', 'currentPosition.latitude': { 
          $gte: port.location.latitude - 0.5,
          $lte: port.location.latitude + 0.5
        }, 'currentPosition.longitude': {
          $gte: port.location.longitude - 0.5,
          $lte: port.location.longitude + 0.5
        }}
      ]
    });

    res.status(200).json({
      success: true,
      port: {
        id: port._id,
        name: port.name,
        code: port.code,
        congestion: port.currentCongestion,
        vesselsCount: vesselsInPort
      }
    });
  })
);

// @route   GET /api/ports/:id/history
// @desc    Get historical congestion trends (Analyst+)
// @access  Private/Analyst
router.get('/:id/history',
  protect,
  authorize('analyst', 'admin'),
  checkPortAccess,
  asyncHandler(async (req, res) => {
    const { startDate, endDate, interval = 'day' } = req.query;

    const port = await Port.findById(req.params.id)
      .select('name code congestionHistory');

    if (!port) {
      return res.status(404).json({ message: 'Port not found' });
    }

    let history = port.congestionHistory;

    // Filter by date range
    if (startDate || endDate) {
      history = history.filter(h => {
        const date = new Date(h.timestamp);
        if (startDate && date < new Date(startDate)) return false;
        if (endDate && date > new Date(endDate)) return false;
        return true;
      });
    }

    // Aggregate by interval if needed
    // (simplified - in production, use MongoDB aggregation)

    res.status(200).json({
      success: true,
      port: {
        id: port._id,
        name: port.name,
        code: port.code
      },
      history,
      count: history.length
    });
  })
);

// @route   POST /api/ports/:id/congestion
// @desc    Update port congestion status (Admin only)
// @access  Private/Admin
router.post('/:id/congestion',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const { status, vesselsWaiting, averageWaitTime } = req.body;

    const port = await Port.findById(req.params.id);

    if (!port) {
      return res.status(404).json({ message: 'Port not found' });
    }

    // Add to history
    port.congestionHistory.push({
      timestamp: new Date(),
      vesselsWaiting: vesselsWaiting || port.currentCongestion.vesselsWaiting,
      averageWaitTime: averageWaitTime || port.currentCongestion.averageWaitTime,
      status: status || port.currentCongestion.status
    });

    // Update current congestion
    port.currentCongestion = {
      status: status || port.currentCongestion.status,
      vesselsWaiting: vesselsWaiting || port.currentCongestion.vesselsWaiting,
      averageWaitTime: averageWaitTime || port.currentCongestion.averageWaitTime,
      lastUpdated: new Date()
    };

    await port.save();

    logger.info(`Port congestion updated: ${port.name} by ${req.user.email}`);

    // Emit real-time update
    const io = req.app.get('io');
    io.to(`port:${port._id}`).emit('port:congestion:updated', {
      portId: port._id,
      congestion: port.currentCongestion
    });

    res.status(200).json({
      success: true,
      message: 'Congestion status updated',
      congestion: port.currentCongestion
    });
  })
);

// @route   GET /api/ports/analytics/compare
// @desc    Compare congestion across multiple ports (Analyst+)
// @access  Private/Analyst
router.get('/analytics/compare',
  protect,
  authorize('analyst', 'admin'),
  asyncHandler(async (req, res) => {
    const { portIds, startDate, endDate } = req.query;

    if (!portIds) {
      return res.status(400).json({ message: 'Port IDs required' });
    }

    const ids = portIds.split(',');
    const ports = await Port.find({ _id: { $in: ids } })
      .select('name code currentCongestion congestionHistory');

    // Process comparison data
    const comparison = ports.map(port => {
      let history = port.congestionHistory;

      if (startDate || endDate) {
        history = history.filter(h => {
          const date = new Date(h.timestamp);
          if (startDate && date < new Date(startDate)) return false;
          if (endDate && date > new Date(endDate)) return false;
          return true;
        });
      }

      // Calculate averages
      const avgWaitTime = history.length > 0
        ? history.reduce((sum, h) => sum + h.averageWaitTime, 0) / history.length
        : 0;

      return {
        id: port._id,
        name: port.name,
        code: port.code,
        currentStatus: port.currentCongestion.status,
        currentWaitTime: port.currentCongestion.averageWaitTime,
        avgWaitTime: avgWaitTime.toFixed(2),
        dataPoints: history.length
      };
    });

    res.status(200).json({
      success: true,
      comparison
    });
  })
);

module.exports = router;
