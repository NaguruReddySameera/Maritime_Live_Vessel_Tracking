const express = require('express');
const router = express.Router();
const Dashboard = require('../models/Dashboard');
const { protect, authorize } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');
const { dashboardValidation, validate } = require('../middleware/validation');

// @route   GET /api/dashboards
// @desc    Get user's dashboards
// @access  Private
router.get('/',
  protect,
  asyncHandler(async (req, res) => {
    const dashboards = await Dashboard.find({
      $or: [
        { owner: req.user._id },
        { 'sharedWith.user': req.user._id }
      ]
    }).populate('owner', 'firstName lastName email');

    res.status(200).json({
      success: true,
      count: dashboards.length,
      dashboards
    });
  })
);

// @route   GET /api/dashboards/:id
// @desc    Get dashboard by ID
// @access  Private
router.get('/:id',
  protect,
  asyncHandler(async (req, res) => {
    const dashboard = await Dashboard.findById(req.params.id)
      .populate('owner', 'firstName lastName email')
      .populate('sharedWith.user', 'firstName lastName email');

    if (!dashboard) {
      return res.status(404).json({ message: 'Dashboard not found' });
    }

    // Check access
    const hasAccess = dashboard.owner.equals(req.user._id) ||
      dashboard.sharedWith.some(s => s.user.equals(req.user._id));

    if (!hasAccess && req.user.role !== 'admin') {
      return res.status(403).json({ message: 'Access denied' });
    }

    res.status(200).json({
      success: true,
      dashboard
    });
  })
);

// @route   POST /api/dashboards
// @desc    Create dashboard (Analyst+)
// @access  Private/Analyst
router.post('/',
  protect,
  authorize('analyst', 'admin'),
  dashboardValidation.create,
  validate,
  asyncHandler(async (req, res) => {
    const dashboard = await Dashboard.create({
      ...req.body,
      owner: req.user._id
    });

    res.status(201).json({
      success: true,
      message: 'Dashboard created successfully',
      dashboard
    });
  })
);

// @route   PUT /api/dashboards/:id
// @desc    Update dashboard
// @access  Private
router.put('/:id',
  protect,
  dashboardValidation.update,
  validate,
  asyncHandler(async (req, res) => {
    let dashboard = await Dashboard.findById(req.params.id);

    if (!dashboard) {
      return res.status(404).json({ message: 'Dashboard not found' });
    }

    // Check if user is owner or has edit permission
    const hasEditPermission = dashboard.owner.equals(req.user._id) ||
      dashboard.sharedWith.some(s => 
        s.user.equals(req.user._id) && s.permission === 'edit'
      );

    if (!hasEditPermission && req.user.role !== 'admin') {
      return res.status(403).json({ message: 'You do not have permission to edit this dashboard' });
    }

    dashboard = await Dashboard.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true, runValidators: true }
    );

    res.status(200).json({
      success: true,
      message: 'Dashboard updated successfully',
      dashboard
    });
  })
);

// @route   DELETE /api/dashboards/:id
// @desc    Delete dashboard
// @access  Private
router.delete('/:id',
  protect,
  asyncHandler(async (req, res) => {
    const dashboard = await Dashboard.findById(req.params.id);

    if (!dashboard) {
      return res.status(404).json({ message: 'Dashboard not found' });
    }

    // Only owner or admin can delete
    if (!dashboard.owner.equals(req.user._id) && req.user.role !== 'admin') {
      return res.status(403).json({ message: 'Only the owner can delete this dashboard' });
    }

    await dashboard.deleteOne();

    res.status(200).json({
      success: true,
      message: 'Dashboard deleted successfully'
    });
  })
);

// @route   POST /api/dashboards/:id/share
// @desc    Share dashboard with other users (Analyst+)
// @access  Private/Analyst
router.post('/:id/share',
  protect,
  authorize('analyst', 'admin'),
  asyncHandler(async (req, res) => {
    const { userId, permission = 'view' } = req.body;

    const dashboard = await Dashboard.findById(req.params.id);

    if (!dashboard) {
      return res.status(404).json({ message: 'Dashboard not found' });
    }

    // Only owner can share
    if (!dashboard.owner.equals(req.user._id)) {
      return res.status(403).json({ message: 'Only the owner can share this dashboard' });
    }

    // Check if already shared
    const alreadyShared = dashboard.sharedWith.some(s => s.user.equals(userId));

    if (alreadyShared) {
      return res.status(400).json({ message: 'Dashboard already shared with this user' });
    }

    dashboard.sharedWith.push({ user: userId, permission });
    await dashboard.save();

    res.status(200).json({
      success: true,
      message: 'Dashboard shared successfully',
      dashboard
    });
  })
);

// @route   DELETE /api/dashboards/:id/share/:userId
// @desc    Unshare dashboard
// @access  Private/Analyst
router.delete('/:id/share/:userId',
  protect,
  authorize('analyst', 'admin'),
  asyncHandler(async (req, res) => {
    const dashboard = await Dashboard.findById(req.params.id);

    if (!dashboard) {
      return res.status(404).json({ message: 'Dashboard not found' });
    }

    // Only owner can unshare
    if (!dashboard.owner.equals(req.user._id)) {
      return res.status(403).json({ message: 'Only the owner can unshare this dashboard' });
    }

    dashboard.sharedWith = dashboard.sharedWith.filter(
      s => !s.user.equals(req.params.userId)
    );

    await dashboard.save();

    res.status(200).json({
      success: true,
      message: 'Dashboard unshared successfully',
      dashboard
    });
  })
);

module.exports = router;
