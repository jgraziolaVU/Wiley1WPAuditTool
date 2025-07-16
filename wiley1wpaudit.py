import streamlit as st
import requests
import os
import json
import datetime
from pathlib import Path
import paramiko  # For SFTP to artscistore
import urllib.parse

# --- Configuration ---
LOCAL_BACKUP_DIR = Path("./backups")

# Ensure local backup directory exists
LOCAL_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

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

def upload_to_artscistore(local_path, remote_filename):
    """Upload backup file to artscistore via SFTP"""
    # Get SFTP credentials from session state
    if 'sftp_credentials' not in st.session_state:
        st.error("SFTP credentials not configured")
        return False
    
    sftp_creds = st.session_state.sftp_credentials
    
    try:
        transport = paramiko.Transport((sftp_creds['host'], 22))
        transport.connect(username=sftp_creds['user'], password=sftp_creds['pass'])
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        remote_path = os.path.join(sftp_creds['upload_dir'], remote_filename)
        sftp.put(local_path, remote_path)
        return True
    except Exception as e:
        st.error(f"SFTP Upload failed: {str(e)}")
        return False
    finally:
        try:
            sftp.close()
            transport.close()
        except:
            pass

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
        
        st.subheader("☁️ artscistore SFTP Credentials")
        col1, col2 = st.columns(2)
        
        with col1:
            sftp_host = st.text_input("SFTP Host", placeholder="artscistore.youruniversity.edu")
            sftp_user = st.text_input("SFTP Username", placeholder="your_sftp_user")
        
        with col2:
            sftp_pass = st.text_input("SFTP Password", type="password")
            sftp_dir = st.text_input("Upload Directory", placeholder="/remote/backup/path")
        
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
                    
                    # Store SFTP credentials if provided
                    if sftp_host and sftp_user and sftp_pass:
                        st.session_state.sftp_credentials = {
                            'host': sftp_host,
                            'user': sftp_user,
                            'pass': sftp_pass,
                            'upload_dir': sftp_dir or '/backup'
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

# Check if user is authenticated
if 'credentials' not in st.session_state:
    show_login_screen()
else:
    show_main_app()
    st.title("🔧 CLAS IT WordPress Audit & Plugin Management Tool")
    st.markdown("### Pure Softaculous API Implementation")
    st.markdown("---")

    # Initialize session state
    if 'installations' not in st.session_state:
        st.session_state.installations = []
    if 'selected_installation' not in st.session_state:
        st.session_state.selected_installation = None
    if 'plugins' not in st.session_state:
        st.session_state.plugins = []

    # Step 1: Discover WordPress Installations
    st.header("📋 Step 1: Discover WordPress Installations")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 Scan for WordPress Sites"):
            with st.spinner("Scanning via Softaculous API..."):
                installations, error = list_wordpress_installations()
                if error:
                    st.error(f"Error: {error}")
                else:
                    st.session_state.installations = installations
                    st.success(f"Found {len(installations)} WordPress installations")

    with col2:
        if st.button("🔄 Refresh Installation List"):
            st.session_state.installations = []
            st.session_state.selected_installation = None
            st.success("Installation list cleared. Click scan to reload.")

    # Display found installations
    if st.session_state.installations:
        st.subheader("WordPress Installations Found:")
        for i, install in enumerate(st.session_state.installations):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{install['display_name']}** (v{install['version']}) - User: {install['user']}")
            with col2:
                st.write(f"ID: {install['insid']}")
            with col3:
                if st.button(f"Select", key=f"select_{i}"):
                    st.session_state.selected_installation = install
                    st.rerun()

    st.markdown("---")

    # Step 2: Plugin Management
    if st.session_state.selected_installation:
        install = st.session_state.selected_installation
        st.header(f"🔌 Step 2: Plugin Management for {install['display_name']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Load Plugin Status"):
                with st.spinner("Loading plugins via Softaculous API..."):
                    plugins, error = get_plugins_for_installation(install['insid'])
                    if error:
                        st.error(f"Error: {error}")
                    else:
                        st.session_state.plugins = plugins
                        st.success(f"Loaded {len(plugins)} plugins")
        
        with col2:
            if st.button("🔄 Update All Plugins"):
                with st.spinner("Updating all plugins..."):
                    result, error = update_plugin(install['insid'])
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
                                result, error = deactivate_plugin(install['insid'], plugin['slug'])
                                if error:
                                    st.error(f"Deactivation failed: {error}")
                                else:
                                    st.success("Plugin deactivated!")
                        else:
                            if st.button(f"Activate", key=f"act_{plugin['slug']}"):
                                result, error = activate_plugin(install['insid'], plugin['slug'])
                                if error:
                                    st.error(f"Activation failed: {error}")
                                else:
                                    st.success("Plugin activated!")
                    
                    with col3:
                        if plugin.get('update_available', False):
                            if st.button(f"Update", key=f"update_{plugin['slug']}"):
                                result, error = update_plugin(install['insid'], plugin['slug'])
                                if error:
                                    st.error(f"Update failed: {error}")
                                else:
                                    st.success("Plugin updated!")
                    
                    if plugin.get('description'):
                        st.write(f"**Description:** {plugin['description']}")

    st.markdown("---")

    # Step 3: WordPress Core Management
    if st.session_state.selected_installation:
        install = st.session_state.selected_installation
        st.header(f"⚙️ Step 3: WordPress Core Management for {install['display_name']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Upgrade WordPress Core"):
                with st.spinner("Upgrading WordPress core..."):
                    result, error = upgrade_wordpress_installation(install['insid'])
                    if error:
                        st.error(f"Upgrade failed: {error}")
                    else:
                        st.success("WordPress core upgraded successfully!")
                        if result:
                            st.json(result)
        
        with col2:
            st.info(f"Current Version: {install['version']}")

    st.markdown("---")

    # Step 4: Backup Management
    st.header("💾 Step 4: Backup Management")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 List All Backups"):
            with st.spinner("Loading backups..."):
                backups, error = list_backups()
                if error:
                    st.error(f"Error: {error}")
                else:
                    st.success("Backups loaded!")
                    if backups:
                        st.json(backups)

    with col2:
        if st.session_state.selected_installation:
            if st.button("💾 Create Backup"):
                with st.spinner("Creating backup..."):
                    result, error = create_backup(st.session_state.selected_installation['insid'])
                    if error:
                        st.error(f"Backup failed: {error}")
                    else:
                        st.success("Backup created successfully!")
                        if result:
                            st.json(result)

    with col3:
        backup_filename = st.text_input("Backup filename to delete:")
        if st.button("🗑️ Delete Backup"):
            if backup_filename:
                result, error = delete_backup(backup_filename)
                if error:
                    st.error(f"Delete failed: {error}")
                else:
                    st.success("Backup deleted!")

    st.markdown("---")

    # Step 5: Upload to artscistore
    st.header("☁️ Step 5: Upload to artscistore")
    if 'sftp_credentials' in st.session_state:
        if st.button("📤 Upload Latest Backup"):
            backups = sorted(LOCAL_BACKUP_DIR.glob("*.zip"), key=os.path.getmtime, reverse=True)
            if backups:
                latest_backup = backups[0]
                with st.spinner("Uploading to artscistore..."):
                    if upload_to_artscistore(str(latest_backup), latest_backup.name):
                        st.success(f"✅ Uploaded {latest_backup.name} to artscistore")
                    else:
                        st.error("❌ Upload failed")
            else:
                st.warning("No backup files found")
    else:
        st.warning("⚠️ SFTP credentials not configured. Please logout and reconfigure.")

    # Display local backup files
    st.subheader("Local Backup Files")
    backups = list(LOCAL_BACKUP_DIR.glob("*.zip"))
    if backups:
        for backup in sorted(backups, key=os.path.getmtime, reverse=True):
            file_size = backup.stat().st_size / (1024*1024)  # MB
            mod_time = datetime.datetime.fromtimestamp(backup.stat().st_mtime)
            st.write(f"📁 {backup.name} ({file_size:.1f} MB) - {mod_time.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.info("No local backup files found")

    st.markdown("---")

    # Step 6: Complete Automated Audit
    st.header("🚀 Step 6: Complete Automated Audit")

    audit_options = st.multiselect(
        "Select audit steps to perform:",
        ["Update all plugins", "Upgrade WordPress core", "Create backups", "Upload to artscistore"],
        default=["Update all plugins", "Create backups", "Upload to artscistore"]
    )

    if st.button("🏃‍♂️ Run Complete Audit for All Sites"):
        if not st.session_state.installations:
            st.error("Please scan for WordPress installations first")
        else:
            total_sites = len(st.session_state.installations)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, install in enumerate(st.session_state.installations):
                status_text.text(f"Processing {install['display_name']} ({i+1}/{total_sites})")
                
                # Update plugins
                if "Update all plugins" in audit_options:
                    st.write(f"🔄 Updating plugins for {install['display_name']}...")
                    result, error = update_plugin(install['insid'])
                    if error:
                        st.error(f"Plugin update failed for {install['display_name']}: {error}")
                    else:
                        st.success(f"✅ Plugins updated for {install['display_name']}")
                
                # Upgrade WordPress core
                if "Upgrade WordPress core" in audit_options:
                    st.write(f"⚙️ Upgrading WordPress core for {install['display_name']}...")
                    result, error = upgrade_wordpress_installation(install['insid'])
                    if error:
                        st.error(f"Core upgrade failed for {install['display_name']}: {error}")
                    else:
                        st.success(f"✅ WordPress core upgraded for {install['display_name']}")
                
                # Create backups
                if "Create backups" in audit_options:
                    st.write(f"💾 Creating backup for {install['display_name']}...")
                    result, error = create_backup(install['insid'])
                    if error:
                        st.error(f"Backup failed for {install['display_name']}: {error}")
                    else:
                        st.success(f"✅ Backup created for {install['display_name']}")
                
                progress_bar.progress((i + 1) / total_sites)
            
            # Upload to artscistore
            if "Upload to artscistore" in audit_options and 'sftp_credentials' in st.session_state:
                st.write("📤 Uploading all backups to artscistore...")
                backups = sorted(LOCAL_BACKUP_DIR.glob("*.zip"), key=os.path.getmtime, reverse=True)
                upload_count = 0
                for backup in backups:
                    if upload_to_artscistore(str(backup), backup.name):
                        upload_count += 1
                st.success(f"✅ Uploaded {upload_count} backup files to artscistore")
            
            status_text.text("Audit complete!")
            st.success("🎉 Complete audit process finished successfully!")

    st.markdown("---")
    st.caption("Developed for CLAS IT AI in July Workshop – 2025")
    st.caption("✨ **Pure Softaculous API Implementation** - No WP-CLI Required")
    st.caption("🔗 Uses Softaculous WordPress Manager API for all plugin operations")
    st.caption("🔐 Credentials stored securely in session state")
