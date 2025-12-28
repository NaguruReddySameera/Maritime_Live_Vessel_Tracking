const { body, param, query, validationResult } = require('express-validator');

// Validation middleware to check for errors
exports.validate = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ 
      message: 'Validation failed',
      errors: errors.array() 
    });
  }
  next();
};

// User validation rules
exports.userValidation = {
  register: [
    body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('password')
      .isLength({ min: 8 }).withMessage('Password must be at least 8 characters')
      .matches(/[A-Z]/).withMessage('Password must contain uppercase letter')
      .matches(/[a-z]/).withMessage('Password must contain lowercase letter')
      .matches(/[0-9]/).withMessage('Password must contain number')
      .matches(/[^A-Za-z0-9]/).withMessage('Password must contain special character'),
    body('firstName').trim().notEmpty().withMessage('First name is required'),
    body('lastName').trim().notEmpty().withMessage('Last name is required'),
    body('company').trim().notEmpty().withMessage('Company is required'),
    body('organizationType')
      .isIn(['shipping_company', 'port_authority', 'insurer', 'other'])
      .withMessage('Invalid organization type')
  ],
  
  login: [
    body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('password').notEmpty().withMessage('Password is required')
  ],

  updateProfile: [
    body('email').optional().isEmail().normalizeEmail(),
    body('firstName').optional().trim().notEmpty(),
    body('lastName').optional().trim().notEmpty(),
    body('password').optional().isLength({ min: 8 })
  ],

  updateRole: [
    body('role').isIn(['operator', 'analyst', 'admin']).withMessage('Invalid role')
  ]
};

// Vessel validation rules
exports.vesselValidation = {
  addNote: [
    body('note').trim().notEmpty().withMessage('Note cannot be empty')
  ],
  
  filter: [
    query('company').optional().trim(),
    query('status').optional().isIn(['underway', 'at_anchor', 'moored', 'not_under_command', 'restricted_maneuverability']),
    query('shipType').optional().isIn(['cargo', 'tanker', 'container', 'bulk_carrier', 'passenger', 'fishing', 'other'])
  ]
};

// Dashboard validation rules
exports.dashboardValidation = {
  create: [
    body('name').trim().notEmpty().withMessage('Dashboard name is required'),
    body('description').optional().trim(),
    body('layout').isArray().withMessage('Layout must be an array')
  ],

  update: [
    body('name').optional().trim().notEmpty(),
    body('layout').optional().isArray()
  ]
};

// Analytics validation rules
exports.analyticsValidation = {
  dateRange: [
    query('startDate').optional().isISO8601().withMessage('Invalid start date'),
    query('endDate').optional().isISO8601().withMessage('Invalid end date')
  ]
};
