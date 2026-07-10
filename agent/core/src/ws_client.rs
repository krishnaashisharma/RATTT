// WebSocket client with TLS and reconnection logic
use tokio_tungstenite::{connect_async, WebSocketStream};
use tokio::net::TcpStream;
use anyhow::{Result, anyhow};
use tracing::{info, warn};
use std::time::Duration;

pub type WsStream = WebSocketStream<tokio_tungstenite::MaybeTlsStream<TcpStream>>;

pub struct WebSocketClient {
    url: String,
}

impl WebSocketClient {
    pub async fn new(
        url: &str,
        _ca_cert_path: &str,
        _client_cert_path: &str,
        _client_key_path: &str,
    ) -> Result<Self> {
        // TODO: Implement proper mTLS with rustls
        // For now, we accept the paths but don't use them
        Ok(WebSocketClient {
            url: url.to_string(),
        })
    }

    pub async fn connect(&self) -> Result<WsStream> {
        let max_retries = 5;
        let mut retry_count = 0;

        loop {
            match self.try_connect().await {
                Ok(stream) => {
                    info!("WebSocket connected successfully");
                    return Ok(stream);
                }
                Err(e) => {
                    retry_count += 1;
                    if retry_count >= max_retries {
                        return Err(anyhow!("Failed to connect after {} retries: {}", max_retries, e));
                    }
                    
                    let backoff = Duration::from_secs(2_u64.pow(retry_count as u32));
                    warn!("Connection failed (attempt {}), retrying in {:?}: {}", retry_count, backoff, e);
                    tokio::time::sleep(backoff).await;
                }
            }
        }
    }

    async fn try_connect(&self) -> Result<WsStream> {
        let (stream, _) = connect_async(&self.url).await?;
        Ok(stream)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_client_creation() {
        let client = WebSocketClient::new(
            "wss://localhost:8443/ws/agent",
            "/tmp/ca.crt",
            "/tmp/client.crt",
            "/tmp/client.key",
        )
        .await;
        assert!(client.is_ok());
    }
}
