# Event Entry Guest Tracker System

![Event Management](https://img.shields.io/badge/Event-Management-blue)
![Guest Tracking](https://img.shields.io/badge/Guest-Tracking-green)
![Volunteer Management](https://img.shields.io/badge/Volunteer-Management-orange)
![Security](https://img.shields.io/badge/Security-OTP%20Auth-red)

A comprehensive event management system for tracking guest entries and exits with mandatory volunteer assistance, multi-factor authentication, and real-time analytics.

## 🎯 Project Overview

The Event Entry Guest Tracker is a sophisticated system designed for event organizers to manage guest attendance with enhanced security and accountability. The system ensures that all guest movements are properly recorded and authorized through a mandatory volunteer-assisted model.

### Key Problem Solved
Traditional event tracking systems allow self-check-in/check-out, which can lead to inaccurate attendance data and security issues. This system solves this by requiring mandatory volunteer assistance for all guest operations.

## ✨ Core Features

### 🔐 Authentication & Security
- **Multi-factor Authentication**: Login via email or phone with OTP verification
- **Phone Number Validation**: 10-digit numbers with 2-digit country code format
- **Role-based Access Control**: Three-tier hierarchy (Master → Volunteer → Guest)
- **First-time Setup**: Master user creation required on initial launch

### 👥 User Management
- **Master Users**: Full system administrators who approve volunteers
- **Volunteers**: Self-register but require master user approval
- **Guests**: Cannot self-register or self-check-in/out (mandatory volunteer assistance)

### 📋 Event Operations
- **Guest Registration**: Only by master users or approved volunteers
- **Check-in/Check-out**: Mandatory volunteer assistance required
- **Session Tracking**: Multi-session event support with duration tracking
- **Real-time Monitoring**: Live attendance statistics and location tracking

### 📊 Analytics & Reporting
- **Real-time Dashboards**: Current attendance, peak times, location traffic
- **Category Analysis**: Breakdown by guest type (VIP, Speaker, Sponsor, etc.)
- **Export Capabilities**: CSV, JSON, Excel, PDF formats
- **Guest Analytics**: Individual attendance patterns and preferences

## 🏗️ System Architecture

### User Roles Hierarchy
```
Master User (Admin)
    ↓
Volunteer (Approved by Master)
    ↓
Guest (Registered by Master/Volunteer)
```

### Mandatory Volunteer Assistance Model
- ❌ Guests **cannot** self-register
- ❌ Guests **cannot** self-check-in
- ❌ Guests **cannot** self-check-out
- ✅ All operations require volunteer mediation
- ✅ Full audit trail with volunteer accountability

## 📁 Repository Structure

```
aws-hackathon/
├── README.md                   # This file - Project overview
├── spec.md                     # Complete system specifications
├── constitution.md             # Project governance framework
├── projectprompttracker.md     # Development history & prompt tracking
├── strategy.docx              # Original strategy document
└── strategy_evententytracker.docx # Event tracker specifications
```

## 📋 Key Documents

### 1. [spec.md](spec.md) - System Specifications
Complete technical and functional specifications including:
- Detailed feature requirements
- Data models and architecture
- User workflows and scenarios
- Security considerations
- Deployment strategies

### 2. [constitution.md](constitution.md) - Project Governance
Establishes project rules and standards:
- **Rule 1**: Mandatory prompt tracking
- Update requirements for AI agents
- Quality standards and compliance
- Project management framework

### 3. [projectprompttracker.md](projectprompttracker.md) - Development History
Complete record of all development decisions:
- Every prompt and AI response
- Design decisions and rationale
- Project evolution timeline
- Compliance with governance rules

## 🚀 Getting Started

### For Developers
```bash
# Clone the repository
git clone https://github.com/himanshu-iit/aws-hackathon.git

# Explore the specifications
cd aws-hackathon
```

### Implementation Roadmap
1. **Phase 1**: Authentication system (Master/Volunteer OTP login)
2. **Phase 2**: Volunteer approval workflow
3. **Phase 3**: Guest registration and management
4. **Phase 4**: Check-in/check-out operations
5. **Phase 5**: Analytics and reporting dashboard

## 🔧 Technical Requirements

### Authentication
- OTP delivery via email/SMS
- Phone number format: +[CountryCode][10-digit number]
- Session management with automatic timeout
- Secure credential storage

### Data Models
- User accounts with role-based permissions
- Guest profiles with categories and special needs
- Event sessions with timing and location
- Attendance records with volunteer references

### Security
- Data encryption at rest and in transit
- Audit logging of all operations
- Compliance with data protection regulations
- Regular security reviews

## 📈 Use Cases

### Event Types Supported
- 🎤 Conferences and seminars
- 🎪 Festivals and exhibitions
- 🏢 Corporate events and meetings
- 🎓 Educational workshops
- 🏟️ Large public gatherings

### Organizational Benefits
- **Accurate Attendance**: No self-service errors
- **Enhanced Security**: Volunteer verification at all points
- **Real-time Insights**: Live dashboards for organizers
- **Volunteer Management**: Streamlined approval workflow
- **Compliance Ready**: Audit trails for all operations

## 👥 Target Users

### Event Organizers
- Master users who manage the entire system
- Configure events and permissions
- Approve volunteer registrations
- Generate comprehensive reports

### Volunteers
- Assist guests with check-in/check-out
- Register new guests
- Provide personal assistance
- Ensure proper attendance tracking

### Guests
- Enjoy seamless event experience
- Receive personal assistance
- Have accurate attendance records
- Special needs accommodated

## 🏆 Unique Selling Points

### 1. **Mandatory Volunteer Assistance**
Unlike other systems, this ensures 100% accurate attendance tracking through required volunteer mediation.

### 2. **Multi-factor Authentication**
Secure OTP-based login via both email and phone with strict phone number validation.

### 3. **Complete Audit Trail**
Every action is logged with user references, providing full accountability.

### 4. **Real-time Analytics**
Live dashboards showing current attendance, peak times, and location traffic.

### 5. **Scalable Architecture**
Designed to handle events of all sizes from small meetings to large festivals.

## 📊 Project Status

### ✅ Completed
- Complete system specification (spec.md)
- Project governance framework (constitution.md)
- Development history tracking (projectprompttracker.md)
- GitHub repository setup with version control

### 🚧 In Progress
- Technical implementation planning
- Architecture design
- Technology stack selection

### 📅 Planned
- Backend development
- Frontend interface
- Mobile applications
- Integration testing

## 🤝 Contributing

### Development Process
1. Review the [spec.md](spec.md) for requirements
2. Follow governance rules in [constitution.md](constitution.md)
3. Document all changes in [projectprompttracker.md](projectprompttracker.md)
4. Submit pull requests with detailed descriptions

### Code Standards
- Follow specifications exactly
- Maintain security standards
- Include comprehensive testing
- Document all changes

## 📞 Contact & Support

### Repository Owner
- **GitHub**: [himanshu-iit](https://github.com/himanshu-iit)
- **Email**: guptahim@msn.com

### Project Documentation
- Full specifications: [spec.md](spec.md)
- Governance rules: [constitution.md](constitution.md)
- Development history: [projectprompttracker.md](projectprompttracker.md)

## 📄 License

This project is developed for the AWS Hackathon. All documentation is open for review and collaboration.

---

**🌟 Star this repository if you find the project interesting!**

**🔔 Watch for updates as development progresses!**

**💬 Open issues for questions or suggestions!**