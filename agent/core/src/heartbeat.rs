// Periodic heartbeat task
use tokio::time::{interval, Duration};
use futures_util::SinkExt;
use tokio_tungstenite::tungstenite::Message;
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::info;

pub async fn heartbeat_loop(
    tx: Arc<Mutex<futures_util::stream::SplitSink<
        crate::ws_client::WsStream,
        Message,
    >>>,
    device_id: String,
) {
    let mut interval = interval(Duration::from_secs(30));

    loop {
        interval.tick().await;

        let heartbeat_msg = serde_json::json!({
            "type": "heartbeat",
            "device_id": device_id,
            "timestamp": chrono::Utc::now().to_rfc3339(),
        });

        let msg = Message::Text(heartbeat_msg.to_string());
        
        let mut tx = tx.lock().await;
        if let Err(e) = tx.send(msg).await {
            eprintln!("Failed to send heartbeat: {}", e);
            break;
        }

        info!("Heartbeat sent");
    }
}
