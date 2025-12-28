const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true
  },
  password: {
    type: String,
    required: true,
    minlength: 8
  },
  firstName: {
    type: String,
    required: true,
    trim: true
  },
  lastName: {
    type: String,
    required: true,
    trim: true
  },
  role: {
    type: String,
    enum: ['operator', 'analyst', 'admin'],
    default: 'operator'
  },
  company: {
    type: String,
    required: true
  },
  organizationType: {
    type: String,
    enum: ['shipping_company', 'port_authority', 'insurer', 'other'],
    required: true
  },
  isActive: {
    type: Boolean,
    default: true
  },
  isLocked: {
    type: Boolean,
    default: false
  },
  loginAttempts: {
    type: Number,
    default: 0
  },
  lockoutUntil: {
    type: Date
  },
  lastLogin: {
    type: Date
  },
  preferences: {
    mapProvider: {
      type: String,
      enum: ['openstreetmap', 'mapbox'],
      default: 'openstreetmap'
    },
    refreshInterval: {
      type: Number,
      default: 30000
    },
    notifications: {
      email: { type: Boolean, default: true },
      inApp: { type: Boolean, default: true }
    }
  },
  permissions: {
    vessels: [{ type: String }], // Array of vessel IDs or 'all'
    ports: [{ type: String }], // Array of port IDs or 'all'
    regions: [{ type: String }] // Geographic regions
  }
}, {
  timestamps: true
});

// Hash password before saving
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  
  try {
    const salt = await bcrypt.genSalt(10);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (error) {
    next(error);
  }
});

// Compare password method
userSchema.methods.comparePassword = async function(candidatePassword) {
  return await bcrypt.compare(candidatePassword, this.password);
};

// Increment login attempts
userSchema.methods.incrementLoginAttempts = function() {
  if (this.lockoutUntil && this.lockoutUntil < Date.now()) {
    return this.updateOne({
      $set: { loginAttempts: 1 },
      $unset: { lockoutUntil: 1 }
    });
  }

  const updates = { $inc: { loginAttempts: 1 } };
  const maxAttempts = parseInt(process.env.MAX_LOGIN_ATTEMPTS) || 5;
  const lockoutTime = parseInt(process.env.LOCKOUT_TIME) || 900000; // 15 minutes

  if (this.loginAttempts + 1 >= maxAttempts && !this.isLocked) {
    updates.$set = { lockoutUntil: Date.now() + lockoutTime };
  }

  return this.updateOne(updates);
};

// Reset login attempts
userSchema.methods.resetLoginAttempts = function() {
  return this.updateOne({
    $set: { loginAttempts: 0 },
    $unset: { lockoutUntil: 1 }
  });
};

// Remove password from JSON output
userSchema.methods.toJSON = function() {
  const obj = this.toObject();
  delete obj.password;
  delete obj.loginAttempts;
  delete obj.lockoutUntil;
  return obj;
};

module.exports = mongoose.model('User', userSchema);
