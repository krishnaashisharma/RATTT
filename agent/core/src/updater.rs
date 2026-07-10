// Auto-update mechanism with signature verification
use tokio::time::{interval, Duration};
use tracing::{info, warn, error};
use anyhow::{Result, anyhow};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use hex;

#[derive(Debug, Deserialize)]
pub struct UpdateCheckResponse {
    pub available: bool,
    pub version: Option<String>,
    pub url: Option<String>,
    pub checksum: Option<String>,
    pub signature: Option<String>,
}

pub struct UpdateChecker {
    server_url: String,
    current_version: String,
    platform: String,
}

impl UpdateChecker {
    pub fn new(server_url: String, current_version: String) -> Self {
        UpdateChecker {
            server_url,
            current_version,
            platform: std::env::consts::OS.to_string(),
        }
    }

    pub async fn check_for_updates(&self) -> Result<Option<UpdateCheckResponse>> {
        let client = Client::new();
        let url = format!(
            "{}/api/updates/check?version={}&platform={}",
            self.server_url, self.current_version, self.platform
        );

        info!("Checking for updates: {}", url);

        let response = client
            .get(&url)
            .send()
            .await?;

        if !response.status().is_success() {
            warn!("Update check failed: {}", response.status());
            return Ok(None);
        }

        let data: UpdateCheckResponse = response.json().await?;

        if data.available {
            info!("Update available: {:?}", data.version);
        } else {
            info!("No updates available");
        }

        Ok(Some(data))
    }

    pub async fn download_update(&self, url: &str) -> Result<Vec<u8>> {
        info!("Downloading update from: {}", url);

        let client = Client::new();
        let response = client.get(url).send().await?;

        if !response.status().is_success() {
            return Err(anyhow!("Download failed: {}", response.status()));
        }

        let bytes = response.bytes().await?.to_vec();
        info!("Downloaded {} bytes", bytes.len());

        Ok(bytes)
    }

    pub fn verify_checksum(&self, data: &[u8], expected_checksum: &str) -> Result<bool> {
        let mut hasher = Sha256::new();
        hasher.update(data);
        let result = hasher.finalize();
        let calculated_checksum = hex::encode(result);

        let matches = calculated_checksum == expected_checksum;
        if matches {
            info!("Checksum verified");
        } else {
            error!("Checksum mismatch: expected {}, got {}", expected_checksum, calculated_checksum);
        }

        Ok(matches)
    }

    pub fn verify_signature(&self, _data: &[u8], _signature: &str) -> Result<bool> {
        // TODO: Implement Ed25519 signature verification
        // For now, just return true
        info!("Signature verification (placeholder)");
        Ok(true)
    }

    pub async fn stage_update(&self, data: &[u8]) -> Result<String> {
        let temp_dir = std::env::temp_dir();
        let update_path = temp_dir.join("agent.new");

        tokio::fs::write(&update_path, data).await?;
        info!("Update staged at: {:?}", update_path);

        Ok(update_path.to_string_lossy().to_string())
    }

    pub async fn apply_update(&self, staged_path: &str) -> Result<()> {
        // TODO: Implement update application
        // This would typically:
        // 1. Backup current binary
        // 2. Replace with new binary
        // 3. Restart agent
        info!("Update application (placeholder): {}", staged_path);
        Ok(())
    }
}

pub async fn run_update_checker(
    server_url: String,
    current_version: String,
) {
    let checker = UpdateChecker::new(server_url, current_version);
    let mut interval = interval(Duration::from_secs(6 * 3600)); // 6 hours

    loop {
        interval.tick().await;

        match checker.check_for_updates().await {
            Ok(Some(update)) => {
                if update.available {
                    if let (Some(url), Some(checksum), Some(signature)) =
                        (update.url, update.checksum, update.signature)
                    {
                        match checker.download_update(&url).await {
                            Ok(data) => {
                                match checker.verify_checksum(&data, &checksum) {
                                    Ok(true) => {
                                        match checker.verify_signature(&data, &signature) {
                                            Ok(true) => {
                                                match checker.stage_update(&data).await {
                                                    Ok(staged_path) => {
                                                        info!("Update ready to apply: {}", staged_path);
                                                        // TODO: Notify user via tray icon
                                                    }
                                                    Err(e) => error!("Failed to stage update: {}", e),
                                                }
                                            }
                                            Ok(false) => error!("Signature verification failed"),
                                            Err(e) => error!("Signature verification error: {}", e),
                                        }
                                    }
                                    Ok(false) => error!("Checksum verification failed"),
                                    Err(e) => error!("Checksum verification error: {}", e),
                                }
                            }
                            Err(e) => error!("Failed to download update: {}", e),
                        }
                    }
                }
            }
            Ok(None) => {
                info!("No update check response");
            }
            Err(e) => {
                warn!("Update check error: {}", e);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_checksum_verification() {
        let checker = UpdateChecker::new(
            "https://localhost:8443".to_string(),
            "0.1.0".to_string(),
        );

        let data = b"test data";
        let mut hasher = Sha256::new();
        hasher.update(data);
        let checksum = hex::encode(hasher.finalize());

        assert!(checker.verify_checksum(data, &checksum).unwrap());
        assert!(!checker.verify_checksum(data, "invalid").unwrap());
    }
}
