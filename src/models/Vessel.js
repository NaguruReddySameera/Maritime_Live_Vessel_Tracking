const mongoose = require('mongoose');

const vesselSchema = new mongoose.Schema({
  imo: {
    type: String,
    required: true,
    unique: true
  },
  mmsi: {
    type: String,
    required: true,
    unique: true
  },
  name: {
    type: String,
    required: true
  },
  shipType: {
    type: String,
    enum: ['cargo', 'tanker', 'container', 'bulk_carrier', 'passenger', 'fishing', 'other']
  },
  flag: String,
  callSign: String,
  length: Number,
  width: Number,
  draft: Number,
  deadweight: Number,
  grossTonnage: Number,
  builtYear: Number,
  company: {
    type: String,
    required: true
  },
  currentPosition: {
    latitude: Number,
    longitude: Number,
    heading: Number,
    speed: Number,
    course: Number,
    timestamp: Date
  },
  status: {
    type: String,
    enum: ['underway', 'at_anchor', 'moored', 'not_under_command', 'restricted_maneuverability', 'engaged_in_fishing', 'under_way_sailing'],
    default: 'underway'
  },
  destination: {
    port: String,
    eta: Date
  },
  lastPort: {
    name: String,
    departureTime: Date
  },
  cargo: {
    type: String,
    description: String,
    quantity: Number,
    unit: String
  },
  route: {
    plannedWaypoints: [{
      latitude: Number,
      longitude: Number,
      order: Number
    }]
  },
  operationalNotes: [{
    note: String,
    addedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User'
    },
    timestamp: {
      type: Date,
      default: Date.now
    }
  }],
  metadata: {
    aisLastUpdate: Date,
    dataQuality: {
      type: String,
      enum: ['high', 'medium', 'low']
    }
  }
}, {
  timestamps: true
});

// Indexes for efficient queries
vesselSchema.index({ company: 1 });
vesselSchema.index({ 'currentPosition.latitude': 1, 'currentPosition.longitude': 1 });
vesselSchema.index({ status: 1 });
vesselSchema.index({ mmsi: 1 });

module.exports = mongoose.model('Vessel', vesselSchema);
