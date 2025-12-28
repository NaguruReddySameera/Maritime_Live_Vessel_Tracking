const mongoose = require('mongoose');

const dashboardSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true
  },
  description: String,
  owner: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  isDefault: {
    type: Boolean,
    default: false
  },
  sharedWith: [{
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User'
    },
    permission: {
      type: String,
      enum: ['view', 'edit'],
      default: 'view'
    }
  }],
  layout: [{
    widgetType: {
      type: String,
      enum: ['map', 'chart', 'table', 'kpi', 'list', 'gauge'],
      required: true
    },
    position: {
      x: Number,
      y: Number,
      width: Number,
      height: Number
    },
    config: {
      title: String,
      dataSource: String,
      filters: mongoose.Schema.Types.Mixed,
      chartType: String, // for chart widgets
      metrics: [String],
      refreshInterval: Number
    }
  }],
  filters: {
    dateRange: {
      start: Date,
      end: Date
    },
    vessels: [String],
    ports: [String],
    companies: [String]
  },
  scheduledReports: [{
    frequency: {
      type: String,
      enum: ['daily', 'weekly', 'monthly']
    },
    recipients: [String],
    format: {
      type: String,
      enum: ['pdf', 'excel', 'csv']
    },
    lastSent: Date,
    isActive: Boolean
  }]
}, {
  timestamps: true
});

dashboardSchema.index({ owner: 1 });
dashboardSchema.index({ 'sharedWith.user': 1 });

module.exports = mongoose.model('Dashboard', dashboardSchema);
