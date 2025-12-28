const mongoose = require('mongoose');

const alertSchema = new mongoose.Schema({
  type: {
    type: String,
    enum: ['piracy', 'weather', 'congestion', 'safety', 'operational'],
    required: true
  },
  severity: {
    type: String,
    enum: ['info', 'warning', 'critical'],
    default: 'info'
  },
  title: {
    type: String,
    required: true
  },
  message: {
    type: String,
    required: true
  },
  affectedVessels: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Vessel'
  }],
  affectedPorts: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Port'
  }],
  location: {
    latitude: Number,
    longitude: Number
  },
  targetUsers: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  }],
  targetRoles: [{
    type: String,
    enum: ['operator', 'analyst', 'admin']
  }],
  targetCompanies: [String],
  status: {
    type: String,
    enum: ['active', 'resolved', 'expired'],
    default: 'active'
  },
  expiresAt: Date,
  notifications: {
    email: { type: Boolean, default: false },
    sms: { type: Boolean, default: false },
    inApp: { type: Boolean, default: true }
  },
  metadata: {
    source: String,
    externalId: String
  }
}, {
  timestamps: true
});

alertSchema.index({ status: 1, createdAt: -1 });
alertSchema.index({ targetUsers: 1, status: 1 });
alertSchema.index({ targetCompanies: 1, status: 1 });

module.exports = mongoose.model('Alert', alertSchema);
