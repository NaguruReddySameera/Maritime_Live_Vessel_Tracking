const mongoose = require('mongoose');

const vesselTrackSchema = new mongoose.Schema({
  vessel: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Vessel',
    required: true
  },
  mmsi: {
    type: String,
    required: true,
    index: true
  },
  positions: [{
    latitude: Number,
    longitude: Number,
    heading: Number,
    speed: Number,
    course: Number,
    timestamp: Date,
    status: String
  }],
  voyageId: {
    type: String,
    index: true
  },
  startTime: {
    type: Date,
    required: true
  },
  endTime: Date,
  retentionDate: {
    type: Date,
    index: true
  }
}, {
  timestamps: true
});

// TTL index for automatic data cleanup based on retention policy
vesselTrackSchema.index({ retentionDate: 1 }, { expireAfterSeconds: 0 });

// Compound index for efficient queries
vesselTrackSchema.index({ mmsi: 1, startTime: -1 });

module.exports = mongoose.model('VesselTrack', vesselTrackSchema);
