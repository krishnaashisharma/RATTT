// Metrics reporter task
use tokio::time::{interval, Duration};
use futures_util::SinkExt;
use tokio_tungstenite::tungstenite::Message;
use std::sync::Arc;
use tokio::sync::Mutex;
use sysinfo::System;
use tracing::info;

pub async fn metric_reporter(
    tx: Arc<Mutex<futures_util::stream::SplitSink<
        crate::ws_client::WsStream,
        Message,
    >>>,
    device_id: String,
) {
    let mut interval = interval(Duration::from_secs(60));
    let mut sys = System::new_all();

    loop {
        interval.tick().await;

        sys.refresh_all();

        let metrics = serde_json::json!({
            "type": "metrics",
            "device_id": device_id,
            "cpu_usage": sys.cpus().iter().map(|c| c.cpu_usage()).collect::<Vec<_>>(),
            "memory_used_mb": sys.used_memory() / 1024,
            "memory_total_mb": sys.total_memory() / 1024,
            "uptime_seconds": System::uptime(),
            "timestamp": chrono::Utc::now().to_rfc3339(),
        });

        let msg = Message::Text(metrics.to_string());
        
        let mut tx = tx.lock().await;
        if let Err(e) = tx.send(msg).await {
            eprintln!("Failed to send metrics: {}", e);
            break;
        }

        info!("Metrics reported");
    }
}
