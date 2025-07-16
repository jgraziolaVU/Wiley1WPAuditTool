# 🔧 CLAS IT WordPress Audit & Plugin Management Tool

### 🚀 The Ultimate WordPress Management Superhero Tool!

> Transform from a humble WordPress admin into a **digital superhero** managing dozens of WordPress sites with the power of a single click! 🦸‍♂️

[![Made with Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-FF6B6B.svg)](https://streamlit.io/)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/your-username/wordpress-management-tool/graphs/commit-activity)

---

## 🎉 What Does This Magical Beast Do?

Ever wished you could manage ALL your WordPress sites from one place? **Welcome to the WordPress Matrix!** 🕶️

This tool is your **digital command center** - think NASA mission control, but for WordPress management! Instead of logging into each site individually (ugh, the horror! 😱), you can:

- 🔌 **Manage plugins** across dozens of sites simultaneously
- 🔄 **Update everything** with the power of a thousand clicks (but actually just one!)
- 💾 **Create and download backups** like a professional data wizard
- ⚙️ **Upgrade WordPress cores** faster than you can say "security patch"
- 📦 **Compress and archive** your backups with professional-grade compression
- 📊 **Export site inventories** for reporting and documentation

**No more tedious one-by-one site management!** This is bulk WordPress operations at their finest! 🎯

---

## 🎭 Features That'll Make You Say "WOW!"

### 🌟 **Core Superpowers**
- **🔐 Secure cPanel Integration** - Uses your existing hosting credentials
- **📊 Automatic Site Discovery** - Finds ALL your WordPress installations instantly
- **🎯 Granular Control** - Manage individual sites OR go nuclear with bulk operations
- **🛡️ Safety First** - No accidental site deletions (backup management only!)
- **📱 Responsive Design** - Works on desktop, tablet, and mobile

### 🚀 **Plugin Management Mastery**
- **Real-time Status** - See active/inactive plugins across all sites
- **One-Click Updates** - Update individual plugins or ALL plugins on ALL sites
- **Smart Filtering** - Show only plugins that need updates
- **Bulk Operations** - Activate, deactivate, or update across multiple sites
- **Detailed Information** - Plugin descriptions, versions, and compatibility

### 💾 **Backup Download Nirvana**
- **Individual Downloads** - Cherry-pick specific backups
- **Bulk Downloads** - Grab multiple backups at once
- **Archive Creation** - ZIP or TAR.GZ compression with timestamps
- **Local Management** - Organize and manage downloaded backups
- **Progress Tracking** - Watch your downloads in real-time

### 📊 **Export & Reporting**
- **CSV Export** - Perfect for spreadsheet analysis
- **JSON Export** - API-ready structured data
- **Markdown Reports** - Beautiful documentation-ready reports
- **Live Metrics** - Real-time site counts and statistics

---

## 🛠️ Installation & Setup

### **Prerequisites**
- Python 3.8+ (because we're not savages! 😄)
- cPanel hosting account with Softaculous
- A sense of adventure and a cup of coffee ☕

---

## 🎯 How to Use This Beast

### **Phase 1: The Authentication Ritual** 🔐
- Enter your cPanel credentials (host, username, password, port)
- Click "🚀 Connect & Start Audit Tool"
- Watch as the tool discovers ALL your WordPress sites

### **Phase 2: The Great Site Selection** 🌐
- Review your discovered WordPress installations
- Select which sites you want to manage (safety first!)
- Export your site inventory for record-keeping

### **Phase 3: Choose Your Adventure** 🎮

#### **🔌 Individual Domain Management**
Perfect for targeted operations:
- Load plugin status for specific sites
- Update individual plugins or all plugins on one site
- Upgrade WordPress core for specific installations
- Create backups for individual sites

#### **🚀 Bulk Operations (The Nuclear Option)**
When you need to manage ALL THE THINGS:
- Update plugins across ALL selected sites
- Upgrade WordPress cores in bulk
- Create backups for multiple sites simultaneously
- Watch progress bars and success counters in real-time

#### **💾 Backup Management & Downloads**
Your data safety command center:
- Download individual backups or multiple at once
- Create compressed archives (ZIP or TAR.GZ)
- Manage local backup files
- Export and organize your backup collection

---

## 🔧 Configuration & Advanced Usage

### **Environment Variables (Optional)**
Create a `.env` file for easier credential management:
```env
CPANEL_HOST=your-server.com
CPANEL_PORT=2083
CPANEL_USER=your-username
CPANEL_PASS=your-password
```

### **Custom Backup Directory**
Modify the backup directory in the code:
```python
LOCAL_BACKUP_DIR = Path("./your-custom-backup-folder")
```

### **Advanced Workflows**

#### **The "Monthly Maintenance Marathon"**
1. Select all sites → Create backups → Download as archive
2. Update all plugins across all sites
3. Upgrade WordPress cores
4. Create new backups post-update
5. Victory dance! 💃

#### **The "Emergency Response Protocol"**
1. Select problem site → Create immediate backup
2. Download backup locally
3. Deactivate problematic plugins
4. Test functionality
5. Reactivate or find alternatives

---

## 🛡️ Security & Safety

### **What This Tool CAN Do (Safe Operations)**
- ✅ Update plugins and WordPress cores
- ✅ Activate/deactivate plugins
- ✅ Create and download backups
- ✅ Export site information
- ✅ Manage local backup files

### **What This Tool CANNOT Do (Your Sites Are Safe!)**
- ❌ Delete WordPress installations
- ❌ Remove domains or databases
- ❌ Delete files from WordPress sites
- ❌ Modify site content or settings

**Your WordPress sites are protected!** This tool only manages plugins, updates, and backups. 🛡️

---

## 🚀 Technical Details

### **Built With**
- **Streamlit** - Beautiful web interface
- **Requests** - HTTP magic for API calls
- **PHPSerialize** - Handle Softaculous API responses
- **Python Standard Library** - File operations, compression, CSV/JSON export

### **API Integration**
- **Softaculous API** - WordPress installation management
- **cPanel Integration** - Secure credential handling
- **Real-time Updates** - Live progress tracking

### **File Structure**
```
wordpress-management-tool/
├── app.py                 # Main application
├── requirements.txt       # Dependencies
├── README.md             # This awesome file!
├── backups/              # Downloaded backup files
└── downloads/            # Created archives
```

---

## 🎯 Use Cases & Success Stories

### **For Hosting Providers**
- Manage hundreds of client WordPress sites
- Bulk security updates across all installations
- Automated backup and maintenance routines

### **For Agencies**
- Client site maintenance made simple
- Bulk plugin updates for all client sites
- Professional backup and reporting

### **For Developers**
- Staging and production environment management
- Quick updates across development sites
- Backup management for multiple projects

### **For Solo WordPress Managers**
- Personal site portfolio management
- Efficient maintenance routines
- Professional backup strategies

---

## 🏆 Roadmap & Future Features

### **Coming Soon™**
- 🔌 **Plugin Installation** - Install plugins from WordPress.org
- 📊 **Advanced Analytics** - Site performance metrics
- 🔄 **Scheduled Operations** - Automated maintenance routines
- 📱 **Mobile App** - Native mobile management
- 🎨 **Custom Themes** - Personalize your dashboard

### **Long-term Vision**
- **Multi-hosting Support** - Beyond just cPanel/Softaculous
- **Team Collaboration** - Multi-user management
- **Advanced Reporting** - Executive dashboards
- **API Endpoints** - Integrate with other tools

---

## 🙏 Acknowledgments

### **Special Thanks**
- **CLAS IT Team** - For the original vision and requirements
- **Streamlit Team** - For the amazing framework
- **WordPress Community** - For making the web better
- **Coffee** - For making this project possible ☕

### **Inspiration**
This tool was born from the frustration of managing multiple WordPress sites manually. If you've ever logged into 20+ WordPress dashboards just to update plugins, you know the pain! 😅

---

## 🎊 Get Started Today!

Ready to transform your WordPress management experience? **Let's go!** 🚀

1. **⭐ Star this repo** (it makes us happy!)
2. **🍴 Fork it** (make it your own!)
3. **📥 Clone it** (get the code!)
4. **🚀 Run it** (experience the magic!)
5. **🎉 Enjoy** (never manage WordPress sites the old way again!)

---

<div align="center">

### Made with ❤️ by the CLAS IT Team

**Remember: With great WordPress power comes great responsibility!** 🕷️

*Now go forth and manage those WordPress sites like the digital superhero you are!* 🦸‍♂️

---

**[⬆ Back to Top](#-clas-it-wordpress-audit--plugin-management-tool)**

</div>
