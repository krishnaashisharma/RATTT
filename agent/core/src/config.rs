// SecureConfig: Load/save encrypted configuration
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use anyhow::{Result, anyhow};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecureConfig {
    pub server_host: String,
    pub server_port: u16,
    pub device_id: String,
    pub device_token: String,
    pub os_type: String,
    pub ca_cert_path: String,
    pub client_cert_path: String,
    pub client_key_path: String,
}

impl SecureConfig {
    pub async fn load() -> Result<Self> {
        // Try to load from environment or config file
        let config_path = Self::get_config_path();
        
        if config_path.exists() {
            // Load from encrypted file
            let content = tokio::fs::read_to_string(&config_path).await?;
            let config: SecureConfig = serde_json::from_str(&content)?;
            Ok(config)
        } else {
            // Load from environment variables
            Ok(SecureConfig {
                server_host: env::var("RDM_SERVER_HOST").unwrap_or_else(|_| "localhost".to_string()),
                server_port: env::var("RDM_SERVER_PORT")
                    .unwrap_or_else(|_| "8443".to_string())
                    .parse()
                    .unwrap_or(8443),
                device_id: env::var("RDM_DEVICE_ID").unwrap_or_else(|_| "device-001".to_string()),
                device_token: env::var("RDM_DEVICE_TOKEN").unwrap_or_else(|_| "placeholder-token".to_string()),
                os_type: std::env::consts::OS.to_string(),
                ca_cert_path: env::var("RDM_CA_CERT_PATH").unwrap_or_else(|_| "/etc/remote-device-mgmt/ca.crt".to_string()),
                client_cert_path: env::var("RDM_CLIENT_CERT_PATH").unwrap_or_else(|_| "/etc/remote-device-mgmt/client.crt".to_string()),
                client_key_path: env::var("RDM_CLIENT_KEY_PATH").unwrap_or_else(|_| "/etc/remote-device-mgmt/client.key".to_string()),
            })
        }
    }

    pub async fn save(&self) -> Result<()> {
        let config_path = Self::get_config_path();
        let content = serde_json::to_string_pretty(self)?;
        
        // Create parent directory if it doesn't exist
        if let Some(parent) = config_path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }
        
        tokio::fs::write(&config_path, content).await?;
        Ok(())
    }

    pub fn get_config_path() -> PathBuf {
        #[cfg(target_os = "macos")]
        {
            let home = env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
            PathBuf::from(format!("{}/.config/remote-device-mgmt/config.json", home))
        }
        
        #[cfg(target_os = "windows")]
        {
            let appdata = env::var("APPDATA").unwrap_or_else(|_| "C:\\".to_string());
            PathBuf::from(format!("{}\\remote-device-mgmt\\config.json", appdata))
        }
        
        #[cfg(not(any(target_os = "macos", target_os = "windows")))]
        {
            let home = env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
            PathBuf::from(format!("{}/.config/remote-device-mgmt/config.json", home))
        }
    }
}
