mod config;
mod crypto;
mod ws_client;
mod commands;
mod heartbeat;
mod metrics;
mod updater;
mod consent;
mod audit_log;
mod enrolment;
mod secure_storage;

use anyhow::Result;
use tracing::{info, error, warn};
use futures_util::{SinkExt, StreamExt};
use tokio_tungstenite::tungstenite::Message;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::path::PathBuf;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("agent_core=info".parse()?),
        )
        .init();

    info!("Remote Device Management Agent starting...");

    // Load configuration
    let config = config::SecureConfig::load().await?;
    info!("Configuration loaded: device_id={}", config.device_id);

    // Initialize audit log
    let log_path = if cfg!(target_os = "macos") {
        PathBuf::from(format!("{}/.local/share/remote-device-mgmt/audit.log", 
            std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string())))
    } else if cfg!(target_os = "windows") {
        PathBuf::from(format!("{}\\AppData\\Local\\remote-device-mgmt\\audit.log",
            std::env::var("APPDATA").unwrap_or_else(|_| "C:\\".to_string())))
    } else {
        PathBuf::from(format!("{}/.local/share/remote-device-mgmt/audit.log",
            std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string())))
    };
    let audit_log = audit_log::AuditLog::new(log_path);

    // Initialize consent manager
    let consent_manager = consent::spawn_consent_ui().await?;

    // Build WebSocket URL
    let ws_url = format!(
        "wss://{}:{}/ws/agent?token={}",
        config.server_host, config.server_port, config.device_token
    );

    info!("Connecting to backend: {}", ws_url);

    // Create WebSocket client
    let ws_client = ws_client::WebSocketClient::new(
        &ws_url,
        &config.ca_cert_path,
        &config.client_cert_path,
        &config.client_key_path,
    )
    .await?;

    // Connect to backend
    let ws_stream = ws_client.connect().await?;
    let (mut write, mut read) = ws_stream.split();

    // Send authentication message
    let auth_msg = serde_json::json!({
        "type": "auth",
        "device_token": &config.device_token,
        "device_id": &config.device_id,
    });
    write.send(Message::Text(auth_msg.to_string())).await?;
    info!("Authentication message sent");

    // Wrap write for sharing across tasks
    let write = Arc::new(Mutex::new(write));

    // Spawn background tasks
    let write_hb = write.clone();
    let device_id_hb = config.device_id.clone();
    let heartbeat_handle = tokio::spawn(async move {
        heartbeat::heartbeat_loop(write_hb, device_id_hb).await;
    });

    let write_metrics = write.clone();
    let device_id_metrics = config.device_id.clone();
    let metrics_handle = tokio::spawn(async move {
        metrics::metric_reporter(write_metrics, device_id_metrics).await;
    });

    // Main command processing loop
    info!("Agent initialized, waiting for commands...");
    
    while let Some(msg_result) = read.next().await {
        match msg_result {
            Ok(Message::Text(text)) => {
                if let Ok(cmd_data) = serde_json::from_str::<serde_json::Value>(&text) {
                    let msg_type = cmd_data.get("type").and_then(|v| v.as_str());

                    match msg_type {
                        Some("command") => {
                            // Check consent state
                            if consent_manager.is_paused().await {
                                warn!("Command received but agent is paused");
                                continue;
                            }

                            if consent_manager.is_revoked().await {
                                error!("Command received but consent revoked");
                                break;
                            }

                            // Parse and execute command
                            if let Ok(cmd) = serde_json::from_value::<commands::Command>(
                                cmd_data.get("command").cloned().unwrap_or_default()
                            ) {
                                match commands::execute(cmd).await {
                                    Ok(response) => {
                                        let response_msg = serde_json::json!({
                                            "type": "command_response",
                                            "id": cmd_data.get("id"),
                                            "command": &response.command,
                                            "status": &response.status,
                                            "result": &response.result,
                                        });

                                        let mut w = write.lock().await;
                                        if let Err(e) = w.send(Message::Text(response_msg.to_string())).await {
                                            error!("Failed to send response: {}", e);
                                        }

                                        // Log to audit trail
                                        let _ = audit_log.log_action(
                                            &response.command,
                                            &response.status,
                                            Some(response.result),
                                        ).await;
                                    }
                                    Err(e) => {
                                        error!("Command execution failed: {}", e);
                                        let error_msg = serde_json::json!({
                                            "type": "command_response",
                                            "id": cmd_data.get("id"),
                                            "status": "error",
                                            "error": e.to_string(),
                                        });

                                        let mut w = write.lock().await;
                                        let _ = w.send(Message::Text(error_msg.to_string())).await;
                                    }
                                }
                            }
                        }

                        Some("token_refresh") => {
                            if let Some(_new_token) = cmd_data.get("new_token").and_then(|v| v.as_str()) {
                                info!("Token refreshed");
                                // TODO: Update config with new token
                            }
                        }

                        Some("pause") => {
                            consent_manager.pause().await;
                            info!("Agent paused");
                        }

                        Some("resume") => {
                            consent_manager.resume().await;
                            info!("Agent resumed");
                        }

                        Some("revoke") => {
                            consent_manager.revoke().await;
                            error!("Consent revoked, shutting down");
                            break;
                        }

                        _ => {
                            warn!("Unknown message type: {:?}", msg_type);
                        }
                    }
                }
            }

            Ok(Message::Binary(_)) => {
                // TODO: Handle binary frames for file transfers
            }

            Ok(Message::Close(_)) => {
                warn!("WebSocket closed by server");
                break;
            }

            Err(e) => {
                error!("WebSocket error: {}", e);
                break;
            }

            _ => {}
        }
    }

    // Cleanup
    info!("Agent shutting down...");
    heartbeat_handle.abort();
    metrics_handle.abort();

    Ok(())
}
