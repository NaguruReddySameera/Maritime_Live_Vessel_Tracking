const express = require('express');
const router = express.Router();
const Vessel = require('../models/Vessel');
const VesselTrack = require('../models/VesselTrack');
const { protect, authorize, checkVesselAccess } = require('../middleware/auth');
const { asyncHandler } = require('../middleware/errorHandler');
const { vesselValidation, validate } = require('../middleware/validation');
const logger = require('../utils/logger');

// @route   GET /api/vessels
// @desc    Get all vessels with filters
// @access  Private
router.get('/',
  protect,
  vesselValidation.filter,
  validate,
  asyncHandler(async (req, res) => {
    const { 
      company, 
      status, 
      shipType, 
      search,
      minSpeed,
      maxSpeed,
      destination,
      page = 1, 
      limit = 50 
    } = req.query;

    const query = {};

    // Filter by company based on role
    if (req.user.role !== 'admin') {
      if (req.user.permissions.vessels.includes('all')) {
        query.company = req.user.company;
      } else {
        query._id = { $in: req.user.permissions.vessels };
      }
    } else if (company) {
      query.company = company;
    }

    if (status) query.status = status;
    if (shipType) query.shipType = shipType;
    if (destination) query['destination.port'] = { $regex: destination, $options: 'i' };
    
    if (minSpeed || maxSpeed) {
      query['currentPosition.speed'] = {};
      if (minSpeed) query['currentPosition.speed'].$gte = parseFloat(minSpeed);
      if (maxSpeed) query['currentPosition.speed'].$lte = parseFloat(maxSpeed);
    }

    if (search) {
      query.$or = [
        { name: { $regex: search, $options: 'i' } },
        { imo: { $regex: search, $options: 'i' } },
        { mmsi: { $regex: search, $options: 'i' } }
      ];
    }

    const vessels = await Vessel.find(query)
      .limit(limit * 1)
      .skip((page - 1) * limit)
      .sort({ 'metadata.aisLastUpdate': -1 });

    const count = await Vessel.countDocuments(query);

    res.status(200).json({
      success: true,
      count,
      totalPages: Math.ceil(count / limit),
      currentPage: parseInt(page),
      vessels
    });
  })
);

// @route   GET /api/vessels/:id
// @desc    Get vessel by ID
// @access  Private
router.get('/:id',
  protect,
  checkVesselAccess,
  asyncHandler(async (req, res) => {
    const vessel = await Vessel.findById(req.params.id)
      .populate('operationalNotes.addedBy', 'firstName lastName email');

    if (!vessel) {
      return res.status(404).json({ message: 'Vessel not found' });
    }

    res.status(200).json({
      success: true,
      vessel
    });
  })
);

// @route   GET /api/vessels/:id/track
// @desc    Get vessel position history
// @access  Private (Analyst+)
router.get('/:id/track',
  protect,
  authorize('analyst', 'admin'),
  checkVesselAccess,
  asyncHandler(async (req, res) => {
    const { startDate, endDate, limit = 1000 } = req.query;

    const vessel = await Vessel.findById(req.params.id);
    if (!vessel) {
      return res.status(404).json({ message: 'Vessel not found' });
    }

    const query = { mmsi: vessel.mmsi };

    if (startDate || endDate) {
      query.startTime = {};
      if (startDate) query.startTime.$gte = new Date(startDate);
      if (endDate) query.startTime.$lte = new Date(endDate);
    }

    const tracks = await VesselTrack.find(query)
      .sort({ startTime: -1 })
      .limit(parseInt(limit));

    res.status(200).json({
      success: true,
      count: tracks.length,
      tracks
    });
  })
);

// @route   POST /api/vessels/:id/notes
// @desc    Add operational note to vessel
// @access  Private
router.post('/:id/notes',
  protect,
  checkVesselAccess,
  vesselValidation.addNote,
  validate,
  asyncHandler(async (req, res) => {
    const { note } = req.body;

    const vessel = await Vessel.findById(req.params.id);

    if (!vessel) {
      return res.status(404).json({ message: 'Vessel not found' });
    }

    vessel.operationalNotes.push({
      note,
      addedBy: req.user._id,
      timestamp: new Date()
    });

    await vessel.save();

    logger.info(`Note added to vessel ${vessel.name} by ${req.user.email}`);

    // Emit real-time update
    const io = req.app.get('io');
    io.to('vessels').emit('vessel:note:added', {
      vesselId: vessel._id,
      note: vessel.operationalNotes[vessel.operationalNotes.length - 1]
    });

    res.status(201).json({
      success: true,
      message: 'Note added successfully',
      note: vessel.operationalNotes[vessel.operationalNotes.length - 1]
    });
  })
);

// @route   GET /api/vessels/:id/notes
// @desc    Get vessel operational notes
// @access  Private
router.get('/:id/notes',
  protect,
  checkVesselAccess,
  asyncHandler(async (req, res) => {
    const vessel = await Vessel.findById(req.params.id)
      .select('operationalNotes')
      .populate('operationalNotes.addedBy', 'firstName lastName email');

    if (!vessel) {
      return res.status(404).json({ message: 'Vessel not found' });
    }

    res.status(200).json({
      success: true,
      notes: vessel.operationalNotes
    });
  })
);

// @route   GET /api/vessels/map/live
// @desc    Get live vessel positions for map
// @access  Private
router.get('/map/live',
  protect,
  asyncHandler(async (req, res) => {
    const { bounds } = req.query; // Format: "minLat,minLng,maxLat,maxLng"

    const query = {};

    // Filter by company based on role
    if (req.user.role !== 'admin') {
      if (req.user.permissions.vessels.includes('all')) {
        query.company = req.user.company;
      } else {
        query._id = { $in: req.user.permissions.vessels };
      }
    }

    // Filter by map bounds if provided
    if (bounds) {
      const [minLat, minLng, maxLat, maxLng] = bounds.split(',').map(parseFloat);
      query['currentPosition.latitude'] = { $gte: minLat, $lte: maxLat };
      query['currentPosition.longitude'] = { $gte: minLng, $lte: maxLng };
    }

    const vessels = await Vessel.find(query)
      .select('name mmsi imo currentPosition status shipType company')
      .limit(500);

    res.status(200).json({
      success: true,
      count: vessels.length,
      vessels
    });
  })
);

module.exports = router;
