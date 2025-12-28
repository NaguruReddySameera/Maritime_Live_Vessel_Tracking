const express = require('express');
const router = express.Router();
const User = require('../models/User');
const { protect, authorize } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');
const { userValidation, validate } = require('../middleware/validation');
const logger = require('../utils/logger');

// @route   GET /api/users
// @desc    Get all users (Admin only)
// @access  Private/Admin
router.get('/',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const { role, company, isActive, search, page = 1, limit = 20 } = req.query;

    const query = {};
    if (role) query.role = role;
    if (company) query.company = company;
    if (isActive !== undefined) query.isActive = isActive === 'true';
    if (search) {
      query.$or = [
        { email: { $regex: search, $options: 'i' } },
        { firstName: { $regex: search, $options: 'i' } },
        { lastName: { $regex: search, $options: 'i' } }
      ];
    }

    const users = await User.find(query)
      .select('-password')
      .limit(limit * 1)
      .skip((page - 1) * limit)
      .sort({ createdAt: -1 });

    const count = await User.countDocuments(query);

    res.status(200).json({
      success: true,
      count,
      totalPages: Math.ceil(count / limit),
      currentPage: page,
      users
    });
  })
);

// @route   GET /api/users/:id
// @desc    Get user by ID (Admin only)
// @access  Private/Admin
router.get('/:id',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const user = await User.findById(req.params.id).select('-password');

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    res.status(200).json({
      success: true,
      user
    });
  })
);

// @route   POST /api/users
// @desc    Create user (Admin only)
// @access  Private/Admin
router.post('/',
  protect,
  authorize('admin'),
  userValidation.register,
  validate,
  asyncHandler(async (req, res) => {
    const user = await User.create(req.body);

    logger.info(`User created: ${user.email} by admin ${req.user.email}`);

    res.status(201).json({
      success: true,
      message: 'User created successfully',
      user
    });
  })
);

// @route   PUT /api/users/:id
// @desc    Update user (Admin only)
// @access  Private/Admin
router.put('/:id',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const { password, ...updateData } = req.body;

    const user = await User.findById(req.params.id);

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    // Update fields
    Object.keys(updateData).forEach(key => {
      user[key] = updateData[key];
    });

    // Update password separately if provided
    if (password) {
      user.password = password;
    }

    await user.save();

    logger.info(`User updated: ${user.email} by admin ${req.user.email}`);

    res.status(200).json({
      success: true,
      message: 'User updated successfully',
      user
    });
  })
);

// @route   DELETE /api/users/:id
// @desc    Delete user (Admin only)
// @access  Private/Admin
router.delete('/:id',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const user = await User.findById(req.params.id);

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    await user.deleteOne();

    logger.info(`User deleted: ${user.email} by admin ${req.user.email}`);

    res.status(200).json({
      success: true,
      message: 'User deleted successfully'
    });
  })
);

// @route   PUT /api/users/:id/role
// @desc    Change user role (Admin only)
// @access  Private/Admin
router.put('/:id/role',
  protect,
  authorize('admin'),
  userValidation.updateRole,
  validate,
  asyncHandler(async (req, res) => {
    const { role } = req.body;

    const user = await User.findById(req.params.id);

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    const oldRole = user.role;
    user.role = role;
    await user.save();

    logger.info(`User role changed: ${user.email} from ${oldRole} to ${role} by admin ${req.user.email}`);

    res.status(200).json({
      success: true,
      message: 'User role updated successfully',
      user
    });
  })
);

// @route   PUT /api/users/:id/lock
// @desc    Lock/unlock user account (Admin only)
// @access  Private/Admin
router.put('/:id/lock',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const { isLocked } = req.body;

    const user = await User.findById(req.params.id);

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    user.isLocked = isLocked;
    if (!isLocked) {
      user.loginAttempts = 0;
      user.lockoutUntil = undefined;
    }
    await user.save();

    logger.info(`User ${isLocked ? 'locked' : 'unlocked'}: ${user.email} by admin ${req.user.email}`);

    res.status(200).json({
      success: true,
      message: `User ${isLocked ? 'locked' : 'unlocked'} successfully`,
      user
    });
  })
);

// @route   PUT /api/users/:id/activate
// @desc    Activate/deactivate user account (Admin only)
// @access  Private/Admin
router.put('/:id/activate',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const { isActive } = req.body;

    const user = await User.findById(req.params.id);

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    user.isActive = isActive;
    await user.save();

    logger.info(`User ${isActive ? 'activated' : 'deactivated'}: ${user.email} by admin ${req.user.email}`);

    res.status(200).json({
      success: true,
      message: `User ${isActive ? 'activated' : 'deactivated'} successfully`,
      user
    });
  })
);

// @route   POST /api/users/:id/reset-password
// @desc    Reset user password (Admin only)
// @access  Private/Admin
router.post('/:id/reset-password',
  protect,
  authorize('admin'),
  asyncHandler(async (req, res) => {
    const { password } = req.body;

    if (!password || password.length < 8) {
      return res.status(400).json({ message: 'Password must be at least 8 characters' });
    }

    const user = await User.findById(req.params.id);

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    user.password = password;
    user.loginAttempts = 0;
    user.isLocked = false;
    user.lockoutUntil = undefined;
    await user.save();

    logger.info(`Password reset for user: ${user.email} by admin ${req.user.email}`);

    res.status(200).json({
      success: true,
      message: 'Password reset successfully'
    });
  })
);

module.exports = router;
