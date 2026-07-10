// Device enrolment flow
use anyhow::{Result, anyhow};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use tracing::info;
use crate::config::SecureConfig;

#[derive(Debug, Serialize)]
pub struct RegisterDeviceRequest {
    pub device_id: String,
    pub os: String,
    pub hostname: String,
    pub enrolment_token: String,
    pub public_key: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct RegisterDeviceResponse {
    pub device_token: String,
}

pub async fn enrol_device(
    server_url: &str,
    device_id: &str,
    enrolment_token: &str,
) -> Result<String> {
    let hostname = hostname::get()
        .ok()
        .and_then(|h| h.into_string().ok())
        .unwrap_or_else(|| "unknown".to_string());

    let request = RegisterDeviceRequest {
        device_id: device_id.to_string(),
        os: std::env::consts::OS.to_string(),
        hostname,
        enrolment_token: enrolment_token.to_string(),
        public_key: None, // TODO: Generate and include public key
    };

    let client = Client::new();
    let url = format!("{}/api/devices/register", server_url);

    info!("Registering device at {}", url);

    let response = client
        .post(&url)
        .json(&request)
        .send()
        .await?;

    if !response.status().is_success() {
        return Err(anyhow!("Registration failed: {}", response.status()));
    }

    let data: RegisterDeviceResponse = response.json().await?;
    info!("Device registered successfully");

    Ok(data.device_token)
}

pub async fn save_device_token(config: &mut SecureConfig, token: &str) -> Result<()> {
    config.device_token = token.to_string();
    config.save().await?;
    info!("Device token saved to secure storage");
    Ok(())
}
