const mongoose = require('mongoose');

const safetyZoneSchema = new mongoose.Schema({
  type: {
    type: String,
    enum: ['piracy', 'storm', 'accident', 'restricted_area'],
    required: true
  },
  severity: {
    type: String,
    enum: ['low', 'medium', 'high', 'critical'],
    default: 'medium'
  },
  title: {
    type: String,
    required: true
  },
  description: String,
  geometry: {
    type: {
      type: String,
      enum: ['Point', 'Polygon', 'LineString'],
      default: 'Polygon'
    },
    coordinates: {
      type: [[[Number]]], // For Polygon
      required: true
    }
  },
  metadata: {
    source: String,
    incidentDate: Date,
    reportedBy: String,
    casualties: Number,
    vesselInvolved: String
  },
  startDate: {
    type: Date,
    default: Date.now
  },
  endDate: Date,
  isActive: {
    type: Boolean,
    default: true
  }
}, {
  timestamps: true
});

// Geospatial index
safetyZoneSchema.index({ geometry: '2dsphere' });
safetyZoneSchema.index({ type: 1, isActive: 1 });

module.exports = mongoose.model('SafetyZone', safetyZoneSchema);
