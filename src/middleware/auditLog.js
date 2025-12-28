const AuditLog = require('../models/AuditLog');
const logger = require('../utils/logger');

// Middleware to log all requests
exports.auditLog = (req, res, next) => {
  // Store original send function
  const originalSend = res.send;

  // Override res.send to capture response
  res.send = function(data) {
    res.locals.responseBody = data;
    originalSend.call(this, data);
  };

  // Log after response is sent
  res.on('finish', async () => {
    try {
      // Skip logging for health checks and static files
      if (req.path === '/api/health' || req.path.startsWith('/static/')) {
        return;
      }

      const logEntry = {
        user: req.user ? req.user._id : null,
        action: `${req.method} ${req.path}`,
        resource: req.path.split('/')[2] || 'unknown', // Extract resource from path
        resourceId: req.params.id || null,
        method: req.method,
        endpoint: req.originalUrl,
        ipAddress: req.ip || req.connection.remoteAddress,
        userAgent: req.get('user-agent'),
        status: res.statusCode < 400 ? 'success' : 'failure',
        metadata: {
          statusCode: res.statusCode,
          query: req.query,
          body: req.method !== 'GET' ? req.body : undefined
        }
      };

      // For PUT/PATCH requests, we might want to log changes
      if (['PUT', 'PATCH', 'DELETE'].includes(req.method)) {
        logEntry.changes = {
          before: req.locals?.originalData,
          after: req.body
        };
      }

      await AuditLog.create(logEntry);
    } catch (error) {
      logger.error('Audit logging error:', error);
    }
  });

  next();
};

// Middleware to capture original data before modification (for audit trail)
exports.captureOriginalData = (model) => {
  return async (req, res, next) => {
    try {
      if (req.params.id && ['PUT', 'PATCH', 'DELETE'].includes(req.method)) {
        const original = await model.findById(req.params.id);
        if (original) {
          req.locals = req.locals || {};
          req.locals.originalData = original.toObject();
        }
      }
      next();
    } catch (error) {
      logger.error('Error capturing original data:', error);
      next();
    }
  };
};
