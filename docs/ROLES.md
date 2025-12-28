# Role-Based Access Control

## Overview

The Vessel Tracking System implements a three-tier role system with granular permissions for different user types.

## Roles

### 1. Operator 👷
**Purpose:** Day-to-day vessel operations

**Capabilities:**
- ✅ View live vessel map
- ✅ Filter and search vessels
- ✅ View vessel details (name, IMO, MMSI, position, status, cargo)
- ✅ Add operational notes to vessels
- ✅ View port congestion status (basic)
- ✅ Receive safety alerts and warnings
- ✅ View own profile and update settings

**Restrictions:**
- ❌ Cannot access advanced analytics
- ❌ Cannot export data
- ❌ Cannot create custom dashboards
- ❌ Cannot view historical voyage data
- ❌ Cannot manage users or system settings

**Data Access:**
- Limited to their own company's vessels
- Can only see vessels they're assigned to (based on permissions)

---

### 2. Analyst 📊
**Purpose:** Analytics, reporting, and optimization

**Inherits all Operator capabilities, plus:**

**Additional Capabilities:**
- ✅ Advanced filtering (region, time window, risk level)
- ✅ Historical voyage replay and analysis
- ✅ Route optimization analytics
- ✅ Export data (CSV/Excel)
- ✅ Port congestion trends and comparisons
- ✅ Create and customize dashboards
- ✅ Schedule automated reports
- ✅ Risk assessment and correlation analysis
- ✅ Safety incident analytics

**Key Features:**
- Access to full analytics module
- Can build and save custom views
- Generate reports for management
- Compare multiple voyages/routes/ports
- Fuel usage analysis (if available)

**Restrictions:**
- ❌ Cannot create or manage users
- ❌ Cannot change system configuration
- ❌ Cannot access admin tools

**Data Access:**
- Full access to company data
- Can view historical data based on retention policy
- May request role changes (workflow only, no actual permission)

---

### 3. Admin 🛡️
**Purpose:** Full system administration and control

**Inherits all Analyst capabilities, plus:**

**Additional Capabilities:**
- ✅ Create, modify, and delete user accounts
- ✅ Assign and change user roles
- ✅ Lock/unlock user accounts
- ✅ Reset user passwords
- ✅ Configure security policies (password rules, session timeout)
- ✅ Manage external data sources (AIS, weather, piracy APIs)
- ✅ Configure data refresh intervals
- ✅ Set data retention policies
- ✅ Access full audit logs
- ✅ Monitor API health and system status
- ✅ Manage dashboard templates
- ✅ Control feature flags per tenant
- ✅ View all company data across tenants

**Admin Console Features:**
- System health monitoring
- API status and uptime tracking
- Error logs and debugging
- User activity audit trail
- Manual data sync triggers
- Multi-tenant configuration

---

## Permission Matrix

| Feature | Operator | Analyst | Admin |
|---------|----------|---------|-------|
| **Authentication & Profile** |
| Login / Logout | ✅ | ✅ | ✅ |
| Update own profile | ✅ | ✅ | ✅ |
| Change own password | ✅ | ✅ | ✅ |
| **Vessel Tracking** |
| View live map | ✅ | ✅ | ✅ |
| View vessel list | ✅ | ✅ | ✅ |
| View vessel details | ✅ | ✅ | ✅ |
| Add operational notes | ✅ | ✅ | ✅ |
| Advanced filters | ❌ | ✅ | ✅ |
| Export vessel data | ❌ | ✅ | ✅ |
| **Historical Data** |
| View voyage history | ❌ | ✅ | ✅ |
| Voyage replay | ❌ | ✅ | ✅ |
| Route analysis | ❌ | ✅ | ✅ |
| **Port Congestion** |
| View basic status | ✅ | ✅ | ✅ |
| View historical trends | ❌ | ✅ | ✅ |
| Compare ports | ❌ | ✅ | ✅ |
| Update congestion data | ❌ | ❌ | ✅ |
| **Safety** |
| View safety overlays | ✅ | ✅ | ✅ |
| Receive alerts | ✅ | ✅ | ✅ |
| Safety analytics | ❌ | ✅ | ✅ |
| Manage safety zones | ❌ | ❌ | ✅ |
| **Dashboards** |
| View shared dashboards | ✅ | ✅ | ✅ |
| Create dashboards | ❌ | ✅ | ✅ |
| Share dashboards | ❌ | ✅ | ✅ |
| Schedule reports | ❌ | ✅ | ✅ |
| Manage templates | ❌ | ❌ | ✅ |
| **User Management** |
| View users | ❌ | ❌ | ✅ |
| Create users | ❌ | ❌ | ✅ |
| Modify users | ❌ | ❌ | ✅ |
| Delete users | ❌ | ❌ | ✅ |
| Change roles | ❌ | ❌ | ✅ |
| Lock accounts | ❌ | ❌ | ✅ |
| **System Admin** |
| View system health | ❌ | ❌ | ✅ |
| Access logs | ❌ | ❌ | ✅ |
| Audit trail | ❌ | ❌ | ✅ |
| Configure APIs | ❌ | ❌ | ✅ |
| System settings | ❌ | ❌ | ✅ |
| Manual sync | ❌ | ❌ | ✅ |

---

## Data Isolation

### Multi-Tenant Architecture

Each organization type has isolated data views:

**Shipping Companies:**
- See their own fleet only
- Can add notes to their vessels
- Custom dashboards for fleet management

**Port Authorities:**
- See vessels in their port area
- View arrivals and berthing schedules
- Port congestion management

**Insurers:**
- View insured vessels only (if allowed)
- Risk assessments for covered assets
- Claims correlation with incidents

### Permission Scopes

Users can have granular permissions:

```javascript
permissions: {
  vessels: ['all'] or ['vessel_id_1', 'vessel_id_2'],
  ports: ['all'] or ['port_id_1', 'port_id_2'],
  regions: ['North America', 'Europe']
}
```

---

## Security Features

### Password Policies (Admin Configurable)
- Minimum 8 characters
- Require uppercase, lowercase, numbers, special characters
- Password expiration (optional)
- Password history (prevent reuse)

### Account Protection
- Max 5 login attempts
- 15-minute lockout after failed attempts
- Admin can manually lock/unlock accounts
- Session timeout (configurable)

### Audit Logging
- All user actions logged
- IP address and user agent tracked
- Changes tracked (before/after)
- 2-year retention (configurable)

---

## API Authorization

### JWT Token-Based Auth
```javascript
// Protected endpoint example
router.get('/vessels',
  protect,           // Verify JWT token
  authorize('operator', 'analyst', 'admin'),  // Check role
  checkVesselAccess, // Verify vessel permissions
  handler
);
```

### Token Refresh
- Access token: 7 days
- Refresh token: 30 days
- Automatic renewal on API calls

---

## Role Assignment Workflow

### Creating New Users (Admin Only)

1. Admin navigates to User Management
2. Clicks "Create User"
3. Fills in user details:
   - Email
   - Name
   - Company
   - Organization Type
   - **Role selection**
   - Permission settings
4. User receives credentials
5. Logged in audit trail

### Changing Roles

1. Admin selects user
2. Chooses new role from dropdown
3. Confirms change
4. User's permissions updated immediately
5. User may need to re-login for full effect

### Role Change Requests (Analyst)

Analysts can *request* role changes, but have no actual power to approve them. This is a workflow feature for organizational processes.

---

## Best Practices

### For Operators
- Only access vessels you're responsible for
- Add detailed operational notes for better tracking
- Review alerts regularly

### For Analysts
- Create reusable dashboards for common reports
- Schedule automated reports to reduce manual work
- Use historical data for trend analysis

### For Admins
- Review audit logs regularly
- Keep user permissions up to date
- Monitor system health daily
- Configure appropriate retention policies
- Regular security policy reviews

---

## Compliance & Privacy

- **GDPR Compliant:** User data can be exported/deleted
- **Audit Trail:** Full traceability of all actions
- **Data Retention:** Configurable cleanup policies
- **Role Segregation:** Principle of least privilege
- **Session Management:** Automatic timeout for security
