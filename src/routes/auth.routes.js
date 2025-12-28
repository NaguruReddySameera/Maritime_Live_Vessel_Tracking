const express = require('express');
const router = express.Router();
const User = require('../models/User');
const { protect, authorize } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');
const { userValidation, validate } = require('../middleware/validation');
const { sendTokenResponse, generateToken, verifyRefreshToken } = require('../utils/jwt');
const logger = require('../utils/logger');

// @route   POST /api/auth/register
// @desc    Register a new user (Admin only)
// @access  Private/Admin
router.post('/register', 
  protect, 
  authorize('admin'),
  userValidation.register,
  validate,
  asyncHandler(async (req, res) => {
    const { email, password, firstName, lastName, company, organizationType, role, permissions } = req.body;

    const user = await User.create({
      email,
      password,
      firstName,
      lastName,
      company,
      organizationType,
      role: role || 'operator',
      permissions: permissions || { vessels: [], ports: [], regions: [] }
    });

    logger.info(`New user registered: ${user.email} by admin ${req.user.email}`);

    res.status(201).json({
      success: true,
      message: 'User created successfully',
      user: {
        id: user._id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        role: user.role,
        company: user.company
      }
    });
  })
);

// @route   POST /api/auth/login
// @desc    Login user
// @access  Public
router.post('/login',
  userValidation.login,
  validate,
  asyncHandler(async (req, res) => {
    const { email, password } = req.body;

    const user = await User.findOne({ email }).select('+password');

    if (!user) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    // Check if account is locked
    if (user.isLocked && user.lockoutUntil > Date.now()) {
      const remainingTime = Math.ceil((user.lockoutUntil - Date.now()) / 1000 / 60);
      return res.status(423).json({ 
        message: `Account is locked. Try again in ${remainingTime} minutes.` 
      });
    }

    // Check if account is active
    if (!user.isActive) {
      return res.status(401).json({ message: 'Account is deactivated' });
    }

    // Validate password
    const isMatch = await user.comparePassword(password);

    if (!isMatch) {
      await user.incrementLoginAttempts();
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    // Reset login attempts on successful login
    if (user.loginAttempts > 0 || user.lockoutUntil) {
      await user.resetLoginAttempts();
    }

    // Update last login
    user.lastLogin = Date.now();
    await user.save();

    logger.info(`User logged in: ${user.email}`);

    sendTokenResponse(user, 200, res);
  })
);

// @route   POST /api/auth/logout
// @desc    Logout user
// @access  Private
router.post('/logout',
  protect,
  asyncHandler(async (req, res) => {
    logger.info(`User logged out: ${req.user.email}`);
    
    res.status(200).json({
      success: true,
      message: 'Logged out successfully'
    });
  })
);

// @route   POST /api/auth/refresh
// @desc    Refresh JWT token
// @access  Public
router.post('/refresh',
  asyncHandler(async (req, res) => {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      return res.status(401).json({ message: 'Refresh token required' });
    }

    const decoded = verifyRefreshToken(refreshToken);

    if (!decoded) {
      return res.status(401).json({ message: 'Invalid refresh token' });
    }

    const user = await User.findById(decoded.id);

    if (!user || !user.isActive) {
      return res.status(401).json({ message: 'User not found or inactive' });
    }

    const newToken = generateToken(user._id);

    res.status(200).json({
      success: true,
      token: newToken
    });
  })
);

// @route   GET /api/auth/profile
// @desc    Get current user profile
// @access  Private
router.get('/profile',
  protect,
  asyncHandler(async (req, res) => {
    res.status(200).json({
      success: true,
      user: req.user
    });
  })
);

// @route   PUT /api/auth/profile
// @desc    Update own profile
// @access  Private
router.put('/profile',
  protect,
  userValidation.updateProfile,
  validate,
  asyncHandler(async (req, res) => {
    const { firstName, lastName, email, password, preferences } = req.body;

    const user = await User.findById(req.user._id);

    if (firstName) user.firstName = firstName;
    if (lastName) user.lastName = lastName;
    if (email) user.email = email;
    if (password) user.password = password;
    if (preferences) user.preferences = { ...user.preferences, ...preferences };

    await user.save();

    logger.info(`User updated profile: ${user.email}`);

    res.status(200).json({
      success: true,
      message: 'Profile updated successfully',
      user
    });
  })
);

module.exports = router;
