const mongoose = require('mongoose');

const portSchema = new mongoose.Schema({
  code: {
    type: String,
    required: true,
    unique: true
  },
  name: {
    type: String,
    required: true
  },
  country: String,
  region: String,
  location: {
    latitude: Number,
    longitude: Number
  },
  capacity: {
    maxVessels: Number,
    berthCount: Number
  },
  currentCongestion: {
    status: {
      type: String,
      enum: ['green', 'yellow', 'red'],
      default: 'green'
    },
    vesselsWaiting: Number,
    averageWaitTime: Number, // in hours
    lastUpdated: Date
  },
  congestionHistory: [{
    timestamp: Date,
    vesselsWaiting: Number,
    averageWaitTime: Number,
    status: String
  }],
  services: [String],
  contact: {
    authority: String,
    email: String,
    phone: String
  }
}, {
  timestamps: true
});

// Index for geospatial queries
portSchema.index({ 'location.latitude': 1, 'location.longitude': 1 });
portSchema.index({ region: 1 });

module.exports = mongoose.model('Port', portSchema);
