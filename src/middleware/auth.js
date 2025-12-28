const jwt = require('jsonwebtoken');
const User = require('../models/User');
const logger = require('../utils/logger');

// Verify JWT token and attach user to request
exports.protect = async (req, res, next) => {
  let token;

  if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
    token = req.headers.authorization.split(' ')[1];
  }

  if (!token) {
    return res.status(401).json({ message: 'Not authorized to access this route' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = await User.findById(decoded.id).select('-password');

    if (!req.user) {
      return res.status(401).json({ message: 'User not found' });
    }

    if (!req.user.isActive) {
      return res.status(401).json({ message: 'Account is deactivated' });
    }

    if (req.user.isLocked) {
      return res.status(401).json({ message: 'Account is locked' });
    }

    next();
  } catch (error) {
    logger.error('Auth middleware error:', error);
    return res.status(401).json({ message: 'Token is invalid or expired' });
  }
};

// Role-based authorization
exports.authorize = (...roles) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ message: 'Not authorized' });
    }

    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ 
        message: `Role '${req.user.role}' is not authorized to access this resource` 
      });
    }

    next();
  };
};

// Check if user has access to specific vessel
exports.checkVesselAccess = async (req, res, next) => {
  try {
    const user = req.user;
    
    // Admins have access to all vessels
    if (user.role === 'admin') {
      return next();
    }

    const vesselId = req.params.id || req.body.vesselId;
    
    // Check if user has 'all' permission or specific vessel access
    if (user.permissions.vessels.includes('all')) {
      return next();
    }

    if (user.permissions.vessels.includes(vesselId)) {
      return next();
    }

    // Check if vessel belongs to user's company
    const Vessel = require('../models/Vessel');
    const vessel = await Vessel.findById(vesselId);
    
    if (vessel && vessel.company === user.company) {
      return next();
    }

    return res.status(403).json({ 
      message: 'You do not have access to this vessel' 
    });
  } catch (error) {
    logger.error('Vessel access check error:', error);
    return res.status(500).json({ message: 'Error checking vessel access' });
  }
};

// Check if user has access to specific port
exports.checkPortAccess = async (req, res, next) => {
  try {
    const user = req.user;
    
    // Admins have access to all ports
    if (user.role === 'admin') {
      return next();
    }

    const portId = req.params.id || req.body.portId;
    
    // Check if user has 'all' permission or specific port access
    if (user.permissions.ports.includes('all') || user.permissions.ports.includes(portId)) {
      return next();
    }

    return res.status(403).json({ 
      message: 'You do not have access to this port' 
    });
  } catch (error) {
    logger.error('Port access check error:', error);
    return res.status(500).json({ message: 'Error checking port access' });
  }
};
