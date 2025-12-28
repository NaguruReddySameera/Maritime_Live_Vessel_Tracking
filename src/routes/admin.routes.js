const express = require('express');
const router = express.Router();
const AuditLog = require('../models/AuditLog');
const { protect, authorize } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');
const logger = require('../utils/logger');
const os = require('os');

// @route   GET /api/admin/health
// @desc    Get system health status
// @access  Private/Admin
router.get('/health',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const mongoose = require('mongoose');
    
    // Database status
    const dbStatus = mongoose.connection.readyState === 1 ? 'connected' : 'disconnected';
    
    // System metrics
    const systemMetrics = {
      uptime: process.uptime(),
      memory: {
        total: os.totalmem(),
        free: os.freemem(),
        used: os.totalmem() - os.freemem(),
        usagePercent: ((os.totalmem() - os.freemem()) / os.totalmem() * 100).toFixed(2)
      },
      cpu: {
        cores: os.cpus().length,
        loadAvg: os.loadavg()
      },
      platform: os.platform(),
      nodeVersion: process.version
    };

    // Count documents
    const User = require('../models/User');
    const Vessel = require('../models/Vessel');
    const Port = require('../models/Port');
    
    const counts = {
      users: await User.countDocuments(),
      vessels: await Vessel.countDocuments(),
      ports: await Port.countDocuments(),
      auditLogs: await AuditLog.countDocuments()
    };

    res.status(200).json({
      success: true,
      status: 'healthy',
      timestamp: new Date().toISOString(),
      database: {
        status: dbStatus,
        collections: counts
      },
      system: systemMetrics
    });
  })
);

// @route   GET /api/admin/logs
// @desc    Get system logs
// @access  Private/Admin
router.get('/logs',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const { level, startDate, endDate, page = 1, limit = 100 } = req.query;

    const query = {};
    
    if (level) query.level = level;
    
    if (startDate || endDate) {
      query.timestamp = {};
      if (startDate) query.timestamp.$gte = new Date(startDate);
      if (endDate) query.timestamp.$lte = new Date(endDate);
    }

    // Read from audit logs
    const logs = await AuditLog.find(query)
      .sort({ createdAt: -1 })
      .limit(limit * 1)
      .skip((page - 1) * limit)
      .populate('user', 'email firstName lastName');

    const count = await AuditLog.countDocuments(query);

    res.status(200).json({
      success: true,
      count,
      totalPages: Math.ceil(count / limit),
      currentPage: parseInt(page),
      logs
    });
  })
);

// @route   GET /api/admin/audit
// @desc    Get audit trail
// @access  Private/Admin
router.get('/audit',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const { 
      userId, 
      resource, 
      action, 
      startDate, 
      endDate, 
      page = 1, 
      limit = 50 
    } = req.query;

    const query = {};
    
    if (userId) query.user = userId;
    if (resource) query.resource = resource;
    if (action) query.action = { $regex: action, $options: 'i' };
    
    if (startDate || endDate) {
      query.createdAt = {};
      if (startDate) query.createdAt.$gte = new Date(startDate);
      if (endDate) query.createdAt.$lte = new Date(endDate);
    }

    const logs = await AuditLog.find(query)
      .sort({ createdAt: -1 })
      .limit(limit * 1)
      .skip((page - 1) * limit)
      .populate('user', 'email firstName lastName role');

    const count = await AuditLog.countDocuments(query);

    res.status(200).json({
      success: true,
      count,
      totalPages: Math.ceil(count / limit),
      currentPage: parseInt(page),
      auditLogs: logs
    });
  })
);

// @route   GET /api/admin/sources
// @desc    Get external data sources configuration
// @access  Private/Admin
router.get('/sources',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    // Return configuration status of external sources
    const sources = [
      {
        name: 'AIS Provider',
        type: 'ais',
        status: process.env.AIS_API_KEY ? 'configured' : 'not_configured',
        url: process.env.AIS_API_URL,
        lastSync: null // This would come from a sync status collection
      },
      {
        name: 'Weather API',
        type: 'weather',
        status: process.env.WEATHER_API_KEY ? 'configured' : 'not_configured',
        url: process.env.WEATHER_API_URL,
        lastSync: null
      },
      {
        name: 'Port Congestion',
        type: 'congestion',
        status: process.env.CONGESTION_API_URL ? 'configured' : 'not_configured',
        url: process.env.CONGESTION_API_URL,
        lastSync: null
      },
      {
        name: 'Piracy Data',
        type: 'piracy',
        status: process.env.PIRACY_API_KEY ? 'configured' : 'not_configured',
        lastSync: null
      }
    ];

    res.status(200).json({
      success: true,
      sources
    });
  })
);

// @route   POST /api/admin/sources/sync
// @desc    Trigger manual data sync
// @access  Private/Admin
router.post('/sources/sync',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const { sourceType } = req.body;

    if (!sourceType) {
      return res.status(400).json({ message: 'Source type required' });
    }

    logger.info(`Manual sync triggered for ${sourceType} by ${req.user.email}`);

    // Trigger sync jobs
    // In production, this would call the actual sync functions
    let message = '';
    switch (sourceType) {
      case 'ais':
        message = 'AIS data sync initiated';
        // Call AIS sync function
        break;
      case 'weather':
        message = 'Weather data sync initiated';
        // Call weather sync function
        break;
      case 'congestion':
        message = 'Port congestion sync initiated';
        // Call congestion sync function
        break;
      case 'piracy':
        message = 'Piracy data sync initiated';
        // Call piracy sync function
        break;
      default:
        return res.status(400).json({ message: 'Invalid source type' });
    }

    res.status(200).json({
      success: true,
      message
    });
  })
);

// @route   GET /api/admin/config
// @desc    Get system configuration
// @access  Private/Admin
router.get('/config',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const config = {
      security: {
        passwordMinLength: process.env.PASSWORD_MIN_LENGTH || 8,
        passwordRequireUppercase: process.env.PASSWORD_REQUIRE_UPPERCASE === 'true',
        passwordRequireLowercase: process.env.PASSWORD_REQUIRE_LOWERCASE === 'true',
        passwordRequireNumber: process.env.PASSWORD_REQUIRE_NUMBER === 'true',
        passwordRequireSpecial: process.env.PASSWORD_REQUIRE_SPECIAL === 'true',
        maxLoginAttempts: process.env.MAX_LOGIN_ATTEMPTS || 5,
        lockoutTime: process.env.LOCKOUT_TIME || 900,
        sessionTimeout: process.env.SESSION_TIMEOUT || 3600
      },
      dataRefresh: {
        mapRefreshInterval: process.env.MAP_REFRESH_INTERVAL || 30000,
        aisPollingInterval: process.env.AIS_POLLING_INTERVAL || 60000,
        weatherPollingInterval: process.env.WEATHER_POLLING_INTERVAL || 300000
      },
      email: {
        smtpHost: process.env.SMTP_HOST,
        smtpPort: process.env.SMTP_PORT,
        emailFrom: process.env.EMAIL_FROM,
        configured: !!(process.env.SMTP_HOST && process.env.SMTP_USER)
      },
      logging: {
        level: process.env.LOG_LEVEL || 'info',
        filePath: process.env.LOG_FILE_PATH || './logs'
      }
    };

    res.status(200).json({
      success: true,
      config
    });
  })
);

// @route   PUT /api/admin/config
// @desc    Update system configuration
// @access  Private/Admin
router.put('/config',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const { category, settings } = req.body;

    if (!category || !settings) {
      return res.status(400).json({ message: 'Category and settings required' });
    }

    logger.info(`System configuration updated: ${category} by ${req.user.email}`);

    // In production, this would update configuration in database or config file
    // For now, just acknowledge the update

    res.status(200).json({
      success: true,
      message: 'Configuration updated successfully',
      note: 'Some changes may require server restart to take effect'
    });
  })
);

// @route   GET /api/admin/stats
// @desc    Get system statistics and metrics
// @access  Private/Admin
router.get('/stats',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const User = require('../models/User');
    const Vessel = require('../models/Vessel');
    const Port = require('../models/Port');
    const Alert = require('../models/Alert');

    // User statistics
    const userStats = await User.aggregate([
      {
        $group: {
          _id: '$role',
          count: { $sum: 1 }
        }
      }
    ]);

    const activeUsers = await User.countDocuments({ isActive: true });
    const lockedUsers = await User.countDocuments({ isLocked: true });

    // Vessel statistics
    const vesselsByStatus = await Vessel.aggregate([
      {
        $group: {
          _id: '$status',
          count: { $sum: 1 }
        }
      }
    ]);

    // Port congestion statistics
    const portsByStatus = await Port.aggregate([
      {
        $group: {
          _id: '$currentCongestion.status',
          count: { $sum: 1 }
        }
      }
    ]);

    // Alert statistics
    const activeAlerts = await Alert.countDocuments({ status: 'active' });
    const criticalAlerts = await Alert.countDocuments({ 
      status: 'active', 
      severity: 'critical' 
    });

    res.status(200).json({
      success: true,
      statistics: {
        users: {
          byRole: userStats,
          active: activeUsers,
          locked: lockedUsers
        },
        vessels: {
          total: await Vessel.countDocuments(),
          byStatus: vesselsByStatus
        },
        ports: {
          total: await Port.countDocuments(),
          byStatus: portsByStatus
        },
        alerts: {
          active: activeAlerts,
          critical: criticalAlerts
        }
      }
    });
  })
);

module.exports = router;
