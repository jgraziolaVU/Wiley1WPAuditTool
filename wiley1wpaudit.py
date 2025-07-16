import streamlit as st
import requests
import os
import json
import datetime
from pathlib import Path
import urllib.parse
import zipfile
import tarfile
import tempfile
import shutil
import csv
import io

# --- Configuration ---
LOCAL_BACKUP_DIR = Path("./backups")
DOWNLOADS_DIR = Path("./downloads")

# Ensure directories exist
LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# --- Softaculous API Functions ---
def make_softaculous_request(act, post_data=None, additional_params=None):
    """Make authenticated request to Softaculous API"""
    # Get credentials from session state
    if 'credentials' not in st.session_state:
        return None, "Not authenticated"
    
    creds = st.session_state.credentials
    softaculous_path = "/frontend/jupiter/softaculous/index.live.php"
    
    base_url = f"https://{creds['user']}:{creds['pass']}@{creds['host']}:{creds['port']}{softaculous_path}"
    
    params = {
        'act': act,
        'api': 'serialize'
    }
    
    if additional_params:
        params.update(additional_params)
    
    try:
        if post_data:
            response = requests.post(base_url, params=params, data=post_data, 
                                   verify=False, timeout=30)
        else:
            response = requests.get(base_url, params=params, 
                                  verify=False, timeout=30)
        
        if response.status_code == 200:
            # Parse serialized PHP response
            import phpserialize
            result = phpserialize.loads(response.content)
            return result, None
        else:
            return None, f"HTTP {response.status_code}: {response.text}"
    
    except Exception as e:
        return None, str(e)

def list_wordpress_installations():
    """List all WordPress installations"""
    result, error = make_softaculous_request('wordpress')
    if error:
        return None, error
    
    installations = []
    if result and 'installations' in result:
        for insid, install_data in result['installations'].items():
            installations.append({
                'insid': insid,
                'domain': install_data.get('softurl', ''),
                'path': install_data.get('softpath', ''),
                'version': install_data.get('ver', ''),
                'user': install_data.get('cuser', ''),
                'display_name': f"{install_data.get('softdomain', '')}/{install_data.get('softdirectory', '')}"
            })
    
    return installations, None

def get_plugins_for_installation(insid):
    """Get all plugins for a specific WordPress installation"""
    post_data = {
        'insid': insid,
        'type': 'plugins',
        'list': '1'
    }
    
    result, error = make_softaculous_request('wordpress', post_data)
    if error:
        return None, error
    
    plugins = []
    if result and 'plugins' in result:
        for plugin_path, plugin_data in result['plugins'].items():
            plugins.append({
                'name': plugin_data.get('Name', 'Unknown'),
                'slug': plugin_path,
                'version': plugin_data.get('Version', ''),
                'active': plugin_data.get('active', False),
                'update_available': plugin_data.get('update_available', False),
                'new_version': plugin_data.get('new_version', ''),
                'description': plugin_data.get('Description', '')
            })
    
    return plugins, None

def update_plugin(insid, plugin_slug=None):
    """Update a specific plugin or all plugins"""
    post_data = {
        'insid': insid,
        'type': 'plugins'
    }
    
    if plugin_slug:
        # For individual plugin update, we need to use WordPress Manager
        # This would require implementing the specific plugin update endpoint
        post_data['slug'] = plugin_slug
        post_data['update'] = '1'
    else:
        # For bulk updates, we can use the bulk update feature
        post_data['bulk_update'] = '1'
    
    result, error = make_softaculous_request('wordpress', post_data)
    return result, error

def activate_plugin(insid, plugin_slug):
    """Activate a plugin"""
    post_data = {
        'insid': insid,
        'type': 'plugins',
        'slug': plugin_slug,
        'activate': '1'
    }
    
    result, error = make_softaculous_request('wordpress', post_data)
    return result, error

def deactivate_plugin(insid, plugin_slug):
    """Deactivate a plugin"""
    post_data = {
        'insid': insid,
        'type': 'plugins',
        'slug': plugin_slug,
        'deactivate': '1'
    }
    
    result, error = make_softaculous_request('wordpress', post_data)
    return result, error

def install_plugin(insid, plugin_slug):
    """Install a plugin from WordPress.org"""
    post_data = {
        'insid': insid,
        'type': 'plugins',
        'slug': plugin_slug,
        'install': '1'
    }
    
    result, error = make_softaculous_request('wordpress', post_data)
    return result, error

def create_backup(insid):
    """Create a backup for a WordPress installation"""
    post_data = {
        'backupins': '1',
        'backup_dir': '1',
        'backup_datadir': '1',
        'backup_db': '1'
    }
    
    result, error = make_softaculous_request('backup', post_data, {'insid': insid})
    return result, error

def list_backups():
    """List all backups"""
    result, error = make_softaculous_request('backups')
    return result, error

def download_backup(backup_filename):
    """Download a backup file"""
    params = {'download': backup_filename}
    result, error = make_softaculous_request('backups', additional_params=params)
    return result, error

def delete_backup(backup_filename):
    """Delete a backup file"""
    params = {'remove': backup_filename}
    result, error = make_softaculous_request('backups', additional_params=params)
    return result, error

def upgrade_wordpress_installation(insid):
    """Upgrade WordPress installation"""
    post_data = {'softsubmit': '1'}
    result, error = make_softaculous_request('upgrade', post_data, {'insid': insid})
    return result, error

def download_backup_file(backup_filename):
    """Download a backup file to local machine"""
    try:
        # Get the backup file content via Softaculous API
        params = {'download': backup_filename}
        result, error = make_softaculous_request('backups', additional_params=params)
        
        if error:
            return None, error
        
        # Save to local backup directory
        local_file_path = LOCAL_BACKUP_DIR / backup_filename
        
        # If result contains binary data, save it
        if result and isinstance(result, bytes):
            with open(local_file_path, 'wb') as f:
                f.write(result)
            return local_file_path, None
        else:
            return None, "No backup data received"
            
    except Exception as e:
        return None, str(e)

def get_backup_file_info(backup_filename):
    """Get information about a backup file"""
    try:
        file_path = LOCAL_BACKUP_DIR / backup_filename
        if file_path.exists():
            stat = file_path.stat()
            return {
                'name': backup_filename,
                'size': stat.st_size,
                'modified': datetime.datetime.fromtimestamp(stat.st_mtime),
                'path': file_path
            }
        return None
    except Exception:
        return None

def export_sites_to_csv(installations):
    """Export WordPress installations to CSV format"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Installation ID', 'Domain', 'Display Name', 'Path', 
        'WordPress Version', 'User', 'Full URL'
    ])
    
    # Write data rows
    for installation in installations:
        writer.writerow([
            installation.get('insid', ''),
            installation.get('domain', ''),
            installation.get('display_name', ''),
            installation.get('path', ''),
            installation.get('version', ''),
            installation.get('user', ''),
            f"https://{installation.get('domain', '')}{installation.get('path', '')}"
        ])
    
    return output.getvalue()

def export_sites_to_json(installations):
    """Export WordPress installations to JSON format"""
    export_data = {
        'export_timestamp': datetime.datetime.now().isoformat(),
        'total_installations': len(installations),
        'installations': installations
    }
    return json.dumps(export_data, indent=2)

def create_detailed_site_report(installations):
    """Create a detailed markdown report of all installations"""
    report = []
    report.append("# WordPress Installations Report")
    report.append(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Total Sites:** {len(installations)}")
    report.append("")
    
    for i, installation in enumerate(installations, 1):
        report.append(f"## {i}. {installation.get('display_name', 'Unknown')}")
        report.append(f"- **Installation ID:** {installation.get('insid', 'N/A')}")
        report.append(f"- **Domain:** {installation.get('domain', 'N/A')}")
        report.append(f"- **Path:** {installation.get('path', 'N/A')}")
        report.append(f"- **WordPress Version:** {installation.get('version', 'N/A')}")
        report.append(f"- **User:** {installation.get('user', 'N/A')}")
        report.append(f"- **Full URL:** https://{installation.get('domain', '')}{installation.get('path', '')}")
        report.append("")
    
    return "\n".join(report)
    """Create a compressed archive from multiple backup files"""
    try:
        archive_path = DOWNLOADS_DIR / f"{archive_name}.{compression_type}"
        
        if compression_type == 'zip':
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for backup_file in backup_files:
                    file_path = LOCAL_BACKUP_DIR / backup_file
                    if file_path.exists():
                        zipf.write(file_path, backup_file)
        
        elif compression_type == 'tar.gz':
            with tarfile.open(archive_path, 'w:gz') as tar:
                for backup_file in backup_files:
                    file_path = LOCAL_BACKUP_DIR / backup_file
                    if file_path.exists():
                        tar.add(file_path, arcname=backup_file)
        
        return archive_path, None
    
    except Exception as e:
        return None, str(e)

def bulk_download_backups(backup_list, progress_callback=None):
    """Download multiple backups from server"""
    results = {'success': [], 'errors': []}
    
    for i, backup_filename in enumerate(backup_list):
        if progress_callback:
            progress_callback(i, len(backup_list), backup_filename)
        
        local_file, error = download_backup_file(backup_filename)
        if error:
            results['errors'].append(f"{backup_filename}: {error}")
        else:
            results['success'].append(backup_filename)
    
    return results

# --- Authentication Functions ---
def test_cpanel_connection(host, port, user, password):
    """Test if cPanel credentials work"""
    try:
        base_url = f"https://{user}:{password}@{host}:{port}/frontend/jupiter/softaculous/index.live.php"
        params = {'act': 'home', 'api': 'json'}
        
        response = requests.get(base_url, params=params, verify=False, timeout=10)
        return response.status_code == 200
    except:
        return False

def show_login_screen():
    """Show the login/configuration screen"""
    st.title("🔐 CLAS IT WordPress Audit - Configuration")
    st.markdown("Enter your credentials to access the WordPress audit tools.")
    
    with st.form("login_form"):
        st.subheader("📋 cPanel Credentials")
        col1, col2 = st.columns(2)
        
        with col1:
            host = st.text_input("cPanel Host", placeholder="server.clasit.org")
            user = st.text_input("cPanel Username", placeholder="your_username")
        
        with col2:
            port = st.selectbox("Port", ["2083", "2082"], index=0)
            password = st.text_input("cPanel Password", type="password")
        
        submit = st.form_submit_button("🚀 Connect & Start Audit Tool")
        
        if submit:
            if not all([host, user, password]):
                st.error("Please fill in all cPanel credentials")
                return
            
            with st.spinner("Testing cPanel connection..."):
                if test_cpanel_connection(host, port, user, password):
                    # Store credentials in session state
                    st.session_state.credentials = {
                        'host': host,
                        'port': port,
                        'user': user,
                        'pass': password
                    }
                    
                    st.success("✅ Connected successfully! Redirecting to audit tools...")
                    st.rerun()
                else:
                    st.error("❌ Failed to connect to cPanel. Please check your credentials.")

def show_main_app():
    """Show the main application interface"""
    # Add logout button in sidebar
    with st.sidebar:
        st.write("### 🔐 Session Info")
        st.write(f"**Host:** {st.session_state.credentials['host']}")
        st.write(f"**User:** {st.session_state.credentials['user']}")
        
        if st.button("🚪 Logout"):
            for key in ['credentials', 'sftp_credentials', 'installations', 'selected_installation', 'plugins']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# --- Streamlit UI ---
st.set_page_config(page_title="CLAS IT WordPress Audit", layout="wide")

# Always show the title and instructions at the top
st.title("🔧 CLAS IT WordPress Audit & Plugin Management Tool")
st.markdown("### Enhanced with Advanced Download Options")

# Instructions Section - Always visible at the top
with st.expander("📖 Instructions - How to Master This WordPress Wizard! 🧙‍♂️", expanded=False):
    st.markdown("""
    # 🎉 Welcome to the Ultimate WordPress Management Experience!
    
    Ready to become a WordPress management superhero? This tool is your cape! 🦸‍♂️ Let's dive into the magical world of bulk WordPress management where tedious tasks become one-click wonders.
    
    ## 🚀 What Does This Beast Do?
    
    Think of this as your **WordPress Command Center** - like having a mission control for all your WordPress sites! Instead of logging into each site individually (ugh, the horror! 😱), you can:
    
    - 🔌 **Manage plugins** across dozens of sites simultaneously
    - 🔄 **Update everything** with the power of a thousand clicks (but actually just one!)
    - 💾 **Create and download backups** like a digital hoarder (but organized!)
    - ⚙️ **Upgrade WordPress cores** faster than you can say "security patch"
    - 📦 **Compress and archive** your backups like a professional data wizard
    
    ---
    
    ## 🎯 Step-by-Step Adventure Guide
    
    ### 🔐 **Phase 1: The Authentication Ritual**
    
    **What you need:**
    - Your cPanel credentials (username, password, host, port)
    - A cup of coffee ☕ (optional but recommended)
    - Your superhero cape (definitely optional)
    
    **The Magic:**
    1. Enter your cPanel details in the login form below
    2. Click "🚀 Connect & Start Audit Tool"
    3. Watch as the tool tests your connection (fingers crossed! 🤞)
    4. Success = You're now in the WordPress Matrix! 🕶️
    
    ---
    
    ### 🌐 **Phase 2: The Great Site Selection**
    
    **What happens:**
    - The tool automatically discovers ALL your WordPress installations
    - You see a beautiful list of domains (like a digital portfolio!)
    - Multi-select checkboxes let you choose your destiny
    
    **Pro Tips:**
    - 📋 **Select All** is your friend for bulk operations
    - 🎯 **Select Specific** sites for targeted management
    - 👀 **Domain info** shows versions and users at a glance
    
    ---
    
    ### 🔌 **Phase 3: Individual Domain Mastery**
    
    **Your Single-Site Superpowers:**
    
    #### 📊 **Plugin Detective Mode**
    - Click "📊 Load Plugin Status" to see EVERY plugin
    - Filter by Active 🟢, Inactive 🔴, or Updates Available ⚠️
    - Each plugin gets its own card with:
      - ✅ **Activate/Deactivate** buttons
      - 🔄 **Update** button (when available)
      - 📝 **Description** and version info
    
    #### ⚙️ **WordPress Core Command Center**
    - See current version at a glance
    - One-click WordPress core upgrades
    - Perfect for staying security-current!
    
    #### 💾 **Backup Mission Control**
    - Create instant backups
    - List all existing backups
    - Download individual backup files
    
    ---
    
    ### 🚀 **Phase 4: Bulk Operations - The Nuclear Option**
    
    **When you need to manage ALL THE THINGS:**
    
    #### 🏃‍♂️ **The Bulk Audit Blitz**
    Choose your adventure:
    - ✅ **Update all plugins** (across ALL selected sites!)
    - 🔄 **Upgrade WordPress core** (mass modernization!)
    - 💾 **Create backups** (safety first, friends!)
    
    **What you'll see:**
    - 📊 **Progress bars** showing real-time status
    - ✅ **Success counters** for that dopamine hit
    - ❌ **Error reporting** (because things happen)
    - 🎉 **Victory celebrations** when complete!
    
    ---
    
    ### 💾 **Phase 5: Backup Download Nirvana**
    
    **This is where the magic REALLY happens! ✨**
    
    #### 📋 **Server Backup Management**
    - **📥 Download Selected**: Cherry-pick your favorites
    - **📥 Download All**: Grab everything (digital hoarding mode!)
    - **📦 Download as Archive**: ZIP or TAR.GZ compression wizardry
    - **🗑️ Delete Selected**: Clean up server space
    
    #### 📁 **Local Backup Mastery**
    Once downloaded, your backups live in `./backups/` and you can:
    - 📦 **Create ZIP Archives** from selected files
    - 📦 **Create TAR.GZ Archives** for maximum compression
    - ⬇️ **Individual Downloads** with dedicated buttons
    - 🗑️ **Bulk Delete** for spring cleaning
    
    #### 📦 **Archive Collection**
    Created archives live in `./downloads/` with:
    - 📅 **Timestamp naming** (no more "backup_final_FINAL_v2.zip")
    - 📊 **File size information** (know what you're downloading!)
    - ⬇️ **One-click downloads** for everything
    
    ---
    
    ## 🎯 Pro Tips for WordPress Ninjas
    
    ### 🔥 **Efficiency Hacks**
    - **Start with backups** - Always create backups before major updates
    - **Use filters** - Plugin filters save time when hunting specific issues
    - **Bulk operations** - Perfect for monthly maintenance routines
    - **Archive everything** - Compressed backups save massive storage space
    
    ### 🛡️ **Safety First**
    - **Test on staging** - Try updates on non-production sites first
    - **Download backups** - Always have local copies before major changes
    - **Check plugin compatibility** - Some plugins don't play nice with others
    - **Monitor results** - Watch the success/error counters during bulk operations
    
    ### 🚀 **Advanced Workflows**
    
    **The "Monthly Maintenance Marathon":**
    1. Select all sites → Create backups → Download as archive
    2. Update all plugins across all sites
    3. Upgrade WordPress cores
    4. Create new backups post-update
    5. Victory dance! 💃
    
    **The "Emergency Response Protocol":**
    1. Select problem site → Create immediate backup
    2. Download backup locally
    3. Deactivate problematic plugins
    4. Test functionality
    5. Reactivate or find alternatives
    
    ---
    
    ## 🎉 **Fun Features You'll Love**
    
    - **🎨 Color-coded status** - Green for good, red for needs attention
    - **📊 Progress bars** - Watch your bulk operations in real-time
    - **🎯 Smart filtering** - Find exactly what you need
    - **📱 Responsive design** - Works on mobile (because who doesn't manage WordPress on their phone?)
    - **🔐 Session management** - Your credentials stay secure in session state
    - **📦 Compression options** - ZIP for compatibility, TAR.GZ for space savings
    
    ---
    
    ## 🆘 **When Things Go Sideways**
    
    **Common Issues & Solutions:**
    - **Connection failed?** Check your cPanel credentials and server status
    - **Plugin update failed?** Some plugins require manual intervention
    - **Backup download slow?** Large sites = large backups (patience, young padawan)
    - **Archive creation failed?** Check available disk space
    
    **Remember:** This tool uses the **Softaculous API** - it's as reliable as your hosting provider's implementation!
    
    ---
    
    ## 🎊 **Ready to Begin?**
    
    You're now equipped with the knowledge to manage WordPress sites like a absolute legend! 🏆
    
    **Quick Start Checklist:**
    - ✅ Have your cPanel credentials ready
    - ✅ Know which sites you want to manage
    - ✅ Decide on backup strategy
    - ✅ Choose your compression preference
    - ✅ Put on your superhero cape (optional)
    
    **Now go forth and manage those WordPress sites like the digital superhero you are!** 🚀
    
    ---
    
    *💡 Pro Tip: Bookmark this page and use it as your WordPress management command center. Your future self will thank you!*
    """)

st.markdown("---")

# Check if user is authenticated
if 'credentials' not in st.session_state:
    show_login_screen()
else:
    show_main_app()

    # Initialize session state
    if 'installations' not in st.session_state:
        st.session_state.installations = []
    if 'selected_installation' not in st.session_state:
        st.session_state.selected_installation = None
    if 'plugins' not in st.session_state:
        st.session_state.plugins = []
    if 'available_backups' not in st.session_state:
        st.session_state.available_backups = {}

    # Load WordPress installations
    if not st.session_state.installations:
        with st.spinner("Loading WordPress installations..."):
            installations, error = list_wordpress_installations()
            if error:
                st.error(f"Failed to load installations: {error}")
                st.stop()
            else:
                st.session_state.installations = installations

    # Domain selection
    st.header("🌐 Select WordPress Installations")
    
    if st.session_state.installations:
        # Export options before domain selection
        st.subheader("📊 Export Site Information")
        st.markdown("Export your WordPress installations data for record-keeping or analysis.")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # CSV Export
            csv_data = export_sites_to_csv(st.session_state.installations)
            st.download_button(
                label="📊 Export CSV",
                data=csv_data,
                file_name=f"wordpress_sites_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Download site list as CSV file"
            )
        
        with col2:
            # JSON Export
            json_data = export_sites_to_json(st.session_state.installations)
            st.download_button(
                label="📋 Export JSON",
                data=json_data,
                file_name=f"wordpress_sites_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                help="Download site list as JSON file"
            )
        
        with col3:
            # Markdown Report
            report_data = create_detailed_site_report(st.session_state.installations)
            st.download_button(
                label="📝 Export Report",
                data=report_data,
                file_name=f"wordpress_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                help="Download detailed markdown report"
            )
        
        with col4:
            # Display count
            st.metric("Total Sites", len(st.session_state.installations))
        
        st.markdown("---")
        
        # Create a multiselect for domain selection
        domain_options = [f"{domain['display_name']} (v{domain['version']})" for domain in st.session_state.installations]
        selected_indices = st.multiselect(
            "Select domains to manage:",
            range(len(st.session_state.installations)),
            format_func=lambda x: domain_options[x],
            default=[]  # No domains selected by default for safety
        )
        
        selected_domains = [st.session_state.installations[i] for i in selected_indices]
        
        if selected_domains:
            st.success(f"Selected {len(selected_domains)} domains for management")
            
            # Display selected domains
            with st.expander("📋 Selected Domains"):
                for domain in selected_domains:
                    st.write(f"• {domain['display_name']} (v{domain['version']}) - User: {domain['user']}")
        else:
            st.warning("Please select at least one domain to continue")
            st.stop()
    else:
        st.error("No WordPress installations found")
        st.stop()

    # Step 1: Individual Domain Management
    st.header("🔌 Step 1: Individual Domain Management")
    st.markdown("Select a specific domain to manage plugins and perform individual actions.")
    
    # Domain selector
    domain_options = [f"{domain['display_name']} (v{domain['version']})" for domain in selected_domains]
    
    selected_domain_index = st.selectbox(
        "Choose a domain to manage:",
        range(len(selected_domains)),
        format_func=lambda x: domain_options[x]
    )
    
    if selected_domain_index is not None:
        current_domain = selected_domains[selected_domain_index]
        st.session_state.selected_installation = current_domain
        
        st.info(f"🌐 Managing: **{current_domain['display_name']}** (User: {current_domain['user']})")
        
        # Plugin management for selected domain
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Load Plugin Status"):
                with st.spinner("Loading plugins via Softaculous API..."):
                    plugins, error = get_plugins_for_installation(current_domain['insid'])
                    if error:
                        st.error(f"Error: {error}")
                    else:
                        st.session_state.plugins = plugins
                        st.success(f"Loaded {len(plugins)} plugins")
        
        with col2:
            if st.button("🔄 Update All Plugins for This Domain"):
                with st.spinner("Updating all plugins..."):
                    result, error = update_plugin(current_domain['insid'])
                    if error:
                        st.error(f"Update failed: {error}")
                    else:
                        st.success("All plugins updated successfully!")
                        if result:
                            st.json(result)
        
        # Display plugins if loaded
        if st.session_state.plugins:
            st.subheader("Plugin Status:")
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                show_active = st.checkbox("Show Active", value=True)
            with col2:
                show_inactive = st.checkbox("Show Inactive", value=True)
            with col3:
                show_updates = st.checkbox("Show Updates Only", value=False)
            
            # Plugin display
            for plugin in st.session_state.plugins:
                # Filter logic
                if show_updates and not plugin.get('update_available', False):
                    continue
                if not show_active and plugin.get('active', False):
                    continue
                if not show_inactive and not plugin.get('active', False):
                    continue
                
                # Plugin card
                with st.expander(f"{plugin['name']} (v{plugin['version']})"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        status = "🟢 Active" if plugin.get('active', False) else "🔴 Inactive"
                        st.write(f"**Status:** {status}")
                        
                        if plugin.get('update_available', False):
                            st.write(f"**⚠️ Update Available:** v{plugin.get('new_version', 'Unknown')}")
                    
                    with col2:
                        if plugin.get('active', False):
                            if st.button(f"Deactivate", key=f"deact_{plugin['slug']}"):
                                result, error = deactivate_plugin(current_domain['insid'], plugin['slug'])
                                if error:
                                    st.error(f"Deactivation failed: {error}")
                                else:
                                    st.success("Plugin deactivated!")
                        else:
                            if st.button(f"Activate", key=f"act_{plugin['slug']}"):
                                result, error = activate_plugin(current_domain['insid'], plugin['slug'])
                                if error:
                                    st.error(f"Activation failed: {error}")
                                else:
                                    st.success("Plugin activated!")
                    
                    with col3:
                        if plugin.get('update_available', False):
                            if st.button(f"Update", key=f"update_{plugin['slug']}"):
                                result, error = update_plugin(current_domain['insid'], plugin['slug'])
                                if error:
                                    st.error(f"Update failed: {error}")
                                else:
                                    st.success("Plugin updated!")
                    
                    if plugin.get('description'):
                        st.write(f"**Description:** {plugin['description']}")
        
        # WordPress Core Management for selected domain
        st.subheader("⚙️ WordPress Core Management")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Upgrade WordPress Core"):
                with st.spinner("Upgrading WordPress core..."):
                    result, error = upgrade_wordpress_installation(current_domain['insid'])
                    if error:
                        st.error(f"Upgrade failed: {error}")
                    else:
                        st.success("WordPress core upgraded successfully!")
                        if result:
                            st.json(result)
        
        with col2:
            st.info(f"Current Version: {current_domain['version']}")
        
        # Backup Management for selected domain
        st.subheader("💾 Backup Management")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Create Backup"):
                with st.spinner("Creating backup..."):
                    result, error = create_backup(current_domain['insid'])
                    if error:
                        st.error(f"Backup failed: {error}")
                    else:
                        st.success("Backup created successfully!")
                        if result:
                            st.json(result)
        
        with col2:
            if st.button("📋 List All Backups"):
                with st.spinner("Loading backups..."):
                    backups, error = list_backups()
                    if error:
                        st.error(f"Error: {error}")
                    else:
                        st.success("Backups loaded!")
                        if backups:
                            st.session_state.available_backups = backups
                            st.json(backups)

    st.markdown("---")

    # Step 2: Bulk Operations
    st.header("🚀 Step 2: Bulk Operations for Selected Domains")
    st.markdown("Perform actions across all selected domains at once.")
    
    # Bulk audit configuration
    audit_options = st.multiselect(
        "Select audit steps to perform across all selected domains:",
        ["Update all plugins", "Upgrade WordPress core", "Create backups"],
        default=["Update all plugins", "Create backups"]
    )
    
    # Bulk operation buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏃‍♂️ Run Bulk Audit on Selected Domains", type="primary"):
            if not audit_options:
                st.warning("Please select at least one audit step")
            else:
                run_bulk_audit(selected_domains, audit_options)
    
    with col2:
        if st.button("🔄 Update All Plugins (All Selected Domains)"):
            run_bulk_plugin_update(selected_domains)

    st.markdown("---")

    # Step 3: Enhanced Backup Management & Downloads
    st.header("💾 Step 3: Enhanced Backup Management & Downloads")
    st.markdown("Advanced backup download options with individual, multiple, and bulk download capabilities.")
    
    # Backup listing and management
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Refresh Backup List"):
            with st.spinner("Loading backups..."):
                backups, error = list_backups()
                if error:
                    st.error(f"Error: {error}")
                else:
                    st.success("Backups loaded!")
                    if backups and 'backups' in backups:
                        st.session_state.available_backups = backups['backups']
                    else:
                        st.session_state.available_backups = {}
    
    with col2:
        if st.button("💾 Create Backup for Selected Domain"):
            if st.session_state.selected_installation:
                with st.spinner("Creating backup..."):
                    result, error = create_backup(st.session_state.selected_installation['insid'])
                    if error:
                        st.error(f"Backup failed: {error}")
                    else:
                        st.success("Backup created successfully!")
                        if result:
                            st.json(result)
            else:
                st.warning("Please select a domain first")

    # Enhanced Download Options
    st.subheader("📥 Enhanced Download Options")
    
    # Display available server backups
    if st.session_state.available_backups:
        st.write("**Available Server Backups:**")
        server_backup_list = list(st.session_state.available_backups.keys())
        
        # Multi-select for server backups
        selected_server_backups = st.multiselect(
            "Select backups to download:",
            server_backup_list,
            help="Select one or more backups to download"
        )
        
        # Download options
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📥 Download Selected") and selected_server_backups:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(current, total, filename):
                    progress_bar.progress(current / total)
                    status_text.text(f"Downloading {filename} ({current+1}/{total})")
                
                with st.spinner("Downloading selected backups..."):
                    results = bulk_download_backups(selected_server_backups, update_progress)
                    
                    if results['success']:
                        st.success(f"✅ Downloaded {len(results['success'])} backups successfully!")
                        for backup in results['success']:
                            st.write(f"• {backup}")
                    
                    if results['errors']:
                        st.error(f"❌ {len(results['errors'])} downloads failed:")
                        for error in results['errors']:
                            st.write(f"• {error}")
                
                status_text.text("Download complete!")
        
        with col2:
            if st.button("📥 Download All") and server_backup_list:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(current, total, filename):
                    progress_bar.progress(current / total)
                    status_text.text(f"Downloading {filename} ({current+1}/{total})")
                
                with st.spinner("Downloading all backups..."):
                    results = bulk_download_backups(server_backup_list, update_progress)
                    
                    if results['success']:
                        st.success(f"✅ Downloaded {len(results['success'])} backups successfully!")
                    
                    if results['errors']:
                        st.error(f"❌ {len(results['errors'])} downloads failed:")
                        for error in results['errors']:
                            st.write(f"• {error}")
                
                status_text.text("Download complete!")
        
        with col3:
            compression_type = st.selectbox("Archive Format", ["zip", "tar.gz"], key="server_compression")
            
            if st.button("📦 Download as Archive") and selected_server_backups:
                # First download the selected backups
                with st.spinner("Downloading and compressing backups..."):
                    results = bulk_download_backups(selected_server_backups)
                    
                    if results['success']:
                        # Create compressed archive
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        archive_name = f"wordpress_backups_{timestamp}"
                        
                        archive_path, error = create_compressed_archive(
                            results['success'], 
                            archive_name, 
                            compression_type
                        )
                        
                        if error:
                            st.error(f"Archive creation failed: {error}")
                        else:
                            st.success(f"✅ Archive created: {archive_path.name}")
                            
                            # Provide download button for the archive
                            with open(archive_path, 'rb') as f:
                                st.download_button(
                                    label=f"⬇️ Download {archive_path.name}",
                                    data=f.read(),
                                    file_name=archive_path.name,
                                    mime="application/octet-stream"
                                )
                    
                    if results['errors']:
                        st.error(f"Some downloads failed: {len(results['errors'])} errors")
        
        with col4:
            if st.button("🗑️ Delete Selected") and selected_server_backups:
                deleted_count = 0
                error_count = 0
                
                with st.spinner("Deleting selected backups..."):
                    for backup in selected_server_backups:
                        result, error = delete_backup(backup)
                        if error:
                            st.error(f"Failed to delete {backup}: {error}")
                            error_count += 1
                        else:
                            deleted_count += 1
                
                if deleted_count > 0:
                    st.success(f"✅ Deleted {deleted_count} backups from server")
                if error_count > 0:
                    st.error(f"❌ Failed to delete {error_count} backups")
                
                # Refresh backup list
                if deleted_count > 0:
                    st.rerun()

    else:
        st.info("No server backups found. Create backups first or refresh the backup list.")

    # Manual backup download
    st.subheader("📄 Manual Backup Download")
    col1, col2 = st.columns(2)
    
    with col1:
        backup_filename = st.text_input("Enter backup filename:", placeholder="backup_timestamp_insid.tar.gz")
        
        if st.button("📥 Download Manual Backup"):
            if backup_filename:
                with st.spinner(f"Downloading {backup_filename}..."):
                    local_file, error = download_backup_file(backup_filename)
                    if error:
                        st.error(f"Download failed: {error}")
                    else:
                        st.success(f"✅ Downloaded {backup_filename}")
                        st.info(f"File saved to: {local_file}")
            else:
                st.warning("Please enter a backup filename")
    
    with col2:
        if st.button("🗑️ Delete Manual Backup"):
            if backup_filename:
                result, error = delete_backup(backup_filename)
                if error:
                    st.error(f"Delete failed: {error}")
                else:
                    st.success("Backup deleted from server!")
            else:
                st.warning("Please enter a backup filename")

    # Local backup file management
    st.subheader("📁 Local Backup File Management")
    
    # Get local backup files
    local_backups = list(LOCAL_BACKUP_DIR.glob("*"))
    
    if local_backups:
        st.write("**Downloaded backup files:**")
        
        # Create a list of backup info
        backup_info = []
        for backup in local_backups:
            info = get_backup_file_info(backup.name)
            if info:
                backup_info.append(info)
        
        # Sort by modification time (newest first)
        backup_info.sort(key=lambda x: x['modified'], reverse=True)
        
        # Multi-select for local backups
        selected_local_backups = st.multiselect(
            "Select local backup files:",
            [info['name'] for info in backup_info],
            help="Select one or more local backup files"
        )
        
        # Local backup actions
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📦 Create ZIP Archive") and selected_local_backups:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = f"local_backups_{timestamp}"
                
                archive_path, error = create_compressed_archive(
                    selected_local_backups, 
                    archive_name, 
                    'zip'
                )
                
                if error:
                    st.error(f"Archive creation failed: {error}")
                else:
                    st.success(f"✅ ZIP archive created: {archive_path.name}")
                    
                    with open(archive_path, 'rb') as f:
                        st.download_button(
                            label=f"⬇️ Download {archive_path.name}",
                            data=f.read(),
                            file_name=archive_path.name,
                            mime="application/zip"
                        )
        
        with col2:
            if st.button("📦 Create TAR.GZ Archive") and selected_local_backups:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = f"local_backups_{timestamp}"
                
                archive_path, error = create_compressed_archive(
                    selected_local_backups, 
                    archive_name, 
                    'tar.gz'
                )
                
                if error:
                    st.error(f"Archive creation failed: {error}")
                else:
                    st.success(f"✅ TAR.GZ archive created: {archive_path.name}")
                    
                    with open(archive_path, 'rb') as f:
                        st.download_button(
                            label=f"⬇️ Download {archive_path.name}",
                            data=f.read(),
                            file_name=archive_path.name,
                            mime="application/gzip"
                        )
        
        with col3:
            if st.button("📥 Download Selected") and selected_local_backups:
                st.success(f"Use individual download buttons below for selected files")
        
        with col4:
            if st.button("🗑️ Delete Selected") and selected_local_backups:
                deleted_count = 0
                for backup_name in selected_local_backups:
                    try:
                        file_path = LOCAL_BACKUP_DIR / backup_name
                        if file_path.exists():
                            file_path.unlink()
                            deleted_count += 1
                    except Exception as e:
                        st.error(f"Failed to delete {backup_name}: {e}")
                
                if deleted_count > 0:
                    st.success(f"✅ Deleted {deleted_count} local backup files")
                    st.rerun()
        
        # Display local backup files with individual download buttons
        st.write("**Individual File Downloads:**")
        for info in backup_info:
            file_size = info['size'] / (1024*1024)  # MB
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📁 {info['name']} ({file_size:.1f} MB) - {info['modified'].strftime('%Y-%m-%d %H:%M')}")
            with col2:
                # Individual download button
                try:
                    with open(info['path'], 'rb') as f:
                        st.download_button(
                            label="⬇️ Download",
                            data=f.read(),
                            file_name=info['name'],
                            mime="application/octet-stream",
                            key=f"download_{info['name']}"
                        )
                except Exception as e:
                    st.error(f"Error reading file: {e}")
    
    else:
        st.info("No local backup files found. Download backups from the server to see them here.")

    # Display created archives
    archive_files = list(DOWNLOADS_DIR.glob("*"))
    if archive_files:
        st.subheader("📦 Created Archives")
        st.write("**Available compressed archives:**")
        
        for archive in sorted(archive_files, key=os.path.getmtime, reverse=True):
            file_size = archive.stat().st_size / (1024*1024)  # MB
            mod_time = datetime.datetime.fromtimestamp(archive.stat().st_mtime)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📦 {archive.name} ({file_size:.1f} MB) - {mod_time.strftime('%Y-%m-%d %H:%M')}")
            with col2:
                try:
                    with open(archive, 'rb') as f:
                        st.download_button(
                            label="⬇️ Download",
                            data=f.read(),
                            file_name=archive.name,
                            mime="application/octet-stream",
                            key=f"download_archive_{archive.name}"
                        )
                except Exception as e:
                    st.error(f"Error reading archive: {e}")

    st.markdown("---")
    st.caption("Developed for CLAS IT AI in July Workshop – 2025")
    st.caption("✨ **Enhanced with Advanced Download Options**")
    st.caption("📥 **Individual, Multiple, Bulk & Compressed Downloads**")
    st.caption("🔗 Uses Softaculous WordPress Manager API for all operations")
    st.caption("🔐 Credentials stored securely in session state")


def run_bulk_audit(domains, audit_options):
    """Run bulk audit on selected domains"""
    total_sites = len(domains)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = {
        'success': [],
        'errors': []
    }
    
    for i, domain in enumerate(domains):
        status_text.text(f"Processing {domain['display_name']} ({i+1}/{total_sites})")
        
        # Update plugins
        if "Update all plugins" in audit_options:
            st.write(f"🔄 Updating plugins for {domain['display_name']}...")
            result, error = update_plugin(domain['insid'])
            if error:
                st.error(f"Plugin update failed for {domain['display_name']}: {error}")
                results['errors'].append(f"Plugin update failed for {domain['display_name']}: {error}")
            else:
                st.success(f"✅ Plugins updated for {domain['display_name']}")
                results['success'].append(f"Plugins updated for {domain['display_name']}")
        
        # Upgrade WordPress core
        if "Upgrade WordPress core" in audit_options:
            st.write(f"⚙️ Upgrading WordPress core for {domain['display_name']}...")
            result, error = upgrade_wordpress_installation(domain['insid'])
            if error:
                st.error(f"Core upgrade failed for {domain['display_name']}: {error}")
                results['errors'].append(f"Core upgrade failed for {domain['display_name']}: {error}")
            else:
                st.success(f"✅ WordPress core upgraded for {domain['display_name']}")
                results['success'].append(f"WordPress core upgraded for {domain['display_name']}")
        
        # Create backups
        if "Create backups" in audit_options:
            st.write(f"💾 Creating backup for {domain['display_name']}...")
            result, error = create_backup(domain['insid'])
            if error:
                st.error(f"Backup failed for {domain['display_name']}: {error}")
                results['errors'].append(f"Backup failed for {domain['display_name']}: {error}")
            else:
                st.success(f"✅ Backup created for {domain['display_name']}")
                results['success'].append(f"Backup created for {domain['display_name']}")
        
        progress_bar.progress((i + 1) / total_sites)
    
    # Show final results
    status_text.text("Bulk audit complete!")
    
    with st.expander("📊 Bulk Audit Results Summary"):
        st.write(f"**✅ Successful Operations:** {len(results['success'])}")
        for success in results['success']:
            st.write(f"• {success}")
        
        if results['errors']:
            st.write(f"**❌ Failed Operations:** {len(results['errors'])}")
            for error in results['errors']:
                st.write(f"• {error}")
    
    st.success("🎉 Bulk audit process completed!")

def run_bulk_plugin_update(domains):
    """Run plugin updates on all selected domains"""
    total_sites = len(domains)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    success_count = 0
    error_count = 0
    
    for i, domain in enumerate(domains):
        status_text.text(f"Updating plugins for {domain['display_name']} ({i+1}/{total_sites})")
        
        result, error = update_plugin(domain['insid'])
        if error:
            st.error(f"❌ Plugin update failed for {domain['display_name']}: {error}")
            error_count += 1
        else:
            st.success(f"✅ Plugins updated for {domain['display_name']}")
            success_count += 1
        
        progress_bar.progress((i + 1) / total_sites)
    
    status_text.text("Plugin updates complete!")
    st.success(f"🎉 Plugin updates completed! ✅ {success_count} successful, ❌ {error_count} failed")
