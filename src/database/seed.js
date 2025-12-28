const mongoose = require('mongoose');
const User = require('../models/User');
const Vessel = require('../models/Vessel');
const Port = require('../models/Port');
const SafetyZone = require('../models/SafetyZone');
require('dotenv').config();

const seedDatabase = async () => {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('MongoDB connected');

    // Clear existing data
    await User.deleteMany({});
    await Vessel.deleteMany({});
    await Port.deleteMany({});
    await SafetyZone.deleteMany({});

    console.log('Existing data cleared');

    // Create admin user
    const admin = await User.create({
      email: 'admin@vesseltracking.com',
      password: 'Admin@123456',
      firstName: 'System',
      lastName: 'Administrator',
      role: 'admin',
      company: 'VesselTrack Corp',
      organizationType: 'other',
      permissions: {
        vessels: ['all'],
        ports: ['all'],
        regions: ['all']
      }
    });

    // Create analyst user
    const analyst = await User.create({
      email: 'analyst@shipping.com',
      password: 'Analyst@123',
      firstName: 'John',
      lastName: 'Analyst',
      role: 'analyst',
      company: 'Global Shipping Inc',
      organizationType: 'shipping_company',
      permissions: {
        vessels: ['all'],
        ports: ['all'],
        regions: ['all']
      }
    });

    // Create operator user
    const operator = await User.create({
      email: 'operator@shipping.com',
      password: 'Operator@123',
      firstName: 'Jane',
      lastName: 'Operator',
      role: 'operator',
      company: 'Global Shipping Inc',
      organizationType: 'shipping_company',
      permissions: {
        vessels: ['all'],
        ports: [],
        regions: []
      }
    });

    console.log('Users created');

    // Create sample vessels
    const vessels = await Vessel.create([
      {
        imo: '9234567',
        mmsi: '123456789',
        name: 'Ocean Pioneer',
        shipType: 'container',
        flag: 'USA',
        company: 'Global Shipping Inc',
        currentPosition: {
          latitude: 40.7128,
          longitude: -74.0060,
          heading: 45,
          speed: 12.5,
          course: 50,
          timestamp: new Date()
        },
        status: 'underway',
        destination: {
          port: 'Port of Rotterdam',
          eta: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000)
        },
        lastPort: {
          name: 'Port of New York',
          departureTime: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)
        },
        cargo: {
          type: 'containers',
          description: 'Mixed cargo containers',
          quantity: 5000,
          unit: 'TEU'
        },
        metadata: {
          aisLastUpdate: new Date(),
          dataQuality: 'high'
        }
      },
      {
        imo: '9345678',
        mmsi: '234567890',
        name: 'Pacific Star',
        shipType: 'tanker',
        flag: 'Singapore',
        company: 'Pacific Maritime',
        currentPosition: {
          latitude: 1.3521,
          longitude: 103.8198,
          heading: 180,
          speed: 10.0,
          course: 175,
          timestamp: new Date()
        },
        status: 'at_anchor',
        destination: {
          port: 'Port of Singapore',
          eta: new Date()
        },
        cargo: {
          type: 'crude_oil',
          description: 'Crude oil',
          quantity: 100000,
          unit: 'barrels'
        },
        metadata: {
          aisLastUpdate: new Date(),
          dataQuality: 'high'
        }
      },
      {
        imo: '9456789',
        mmsi: '345678901',
        name: 'Atlantic Voyager',
        shipType: 'bulk_carrier',
        flag: 'Greece',
        company: 'Global Shipping Inc',
        currentPosition: {
          latitude: 51.5074,
          longitude: -0.1278,
          heading: 90,
          speed: 11.5,
          course: 95,
          timestamp: new Date()
        },
        status: 'underway',
        destination: {
          port: 'Port of Hamburg',
          eta: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000)
        },
        cargo: {
          type: 'grain',
          description: 'Wheat',
          quantity: 50000,
          unit: 'tonnes'
        },
        metadata: {
          aisLastUpdate: new Date(),
          dataQuality: 'medium'
        }
      }
    ]);

    console.log('Vessels created');

    // Create sample ports
    const ports = await Port.create([
      {
        code: 'USNYC',
        name: 'Port of New York',
        country: 'USA',
        region: 'North America',
        location: {
          latitude: 40.6895,
          longitude: -74.0445
        },
        capacity: {
          maxVessels: 50,
          berthCount: 20
        },
        currentCongestion: {
          status: 'green',
          vesselsWaiting: 3,
          averageWaitTime: 2.5,
          lastUpdated: new Date()
        }
      },
      {
        code: 'NLRTM',
        name: 'Port of Rotterdam',
        country: 'Netherlands',
        region: 'Europe',
        location: {
          latitude: 51.9244,
          longitude: 4.4777
        },
        capacity: {
          maxVessels: 100,
          berthCount: 40
        },
        currentCongestion: {
          status: 'yellow',
          vesselsWaiting: 15,
          averageWaitTime: 8.5,
          lastUpdated: new Date()
        }
      },
      {
        code: 'SGSIN',
        name: 'Port of Singapore',
        country: 'Singapore',
        region: 'Asia',
        location: {
          latitude: 1.2644,
          longitude: 103.8220
        },
        capacity: {
          maxVessels: 150,
          berthCount: 60
        },
        currentCongestion: {
          status: 'red',
          vesselsWaiting: 25,
          averageWaitTime: 15.0,
          lastUpdated: new Date()
        }
      },
      {
        code: 'DEHAM',
        name: 'Port of Hamburg',
        country: 'Germany',
        region: 'Europe',
        location: {
          latitude: 53.5511,
          longitude: 9.9937
        },
        capacity: {
          maxVessels: 80,
          berthCount: 35
        },
        currentCongestion: {
          status: 'green',
          vesselsWaiting: 5,
          averageWaitTime: 3.0,
          lastUpdated: new Date()
        }
      }
    ]);

    console.log('Ports created');

    // Create sample safety zones
    const safetyZones = await SafetyZone.create([
      {
        type: 'piracy',
        severity: 'high',
        title: 'Gulf of Aden Piracy Zone',
        description: 'High risk of piracy in this area',
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [43.0, 12.0],
            [43.0, 14.0],
            [51.0, 14.0],
            [51.0, 12.0],
            [43.0, 12.0]
          ]]
        },
        metadata: {
          source: 'IMB Piracy Reporting Centre'
        },
        isActive: true
      },
      {
        type: 'storm',
        severity: 'critical',
        title: 'Tropical Storm in South China Sea',
        description: 'Severe tropical storm with winds up to 70 knots',
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [110.0, 15.0],
            [110.0, 20.0],
            [115.0, 20.0],
            [115.0, 15.0],
            [110.0, 15.0]
          ]]
        },
        metadata: {
          source: 'NOAA',
          incidentDate: new Date()
        },
        isActive: true,
        startDate: new Date(),
        endDate: new Date(Date.now() + 72 * 60 * 60 * 1000) // 3 days
      }
    ]);

    console.log('Safety zones created');

    console.log('\n=== Database Seeded Successfully ===');
    console.log('\nTest Users:');
    console.log('Admin:    admin@vesseltracking.com / Admin@123456');
    console.log('Analyst:  analyst@shipping.com / Analyst@123');
    console.log('Operator: operator@shipping.com / Operator@123');
    console.log('\n=== Summary ===');
    console.log(`Users: ${await User.countDocuments()}`);
    console.log(`Vessels: ${await Vessel.countDocuments()}`);
    console.log(`Ports: ${await Port.countDocuments()}`);
    console.log(`Safety Zones: ${await SafetyZone.countDocuments()}`);

    process.exit(0);
  } catch (error) {
    console.error('Error seeding database:', error);
    process.exit(1);
  }
};

seedDatabase();
