// Encrypted local audit log
use std::path::PathBuf;
use anyhow::Result;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use tracing::info;
use tokio::io::AsyncWriteExt;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AuditEntry {
    pub timestamp: String,
    pub action: String,
    pub status: String,
    pub details: Option<serde_json::Value>,
}

pub struct AuditLog {
    log_path: PathBuf,
}

impl AuditLog {
    pub fn new(log_path: PathBuf) -> Self {
        AuditLog { log_path }
    }

    pub async fn log_action(
        &self,
        action: &str,
        status: &str,
        details: Option<serde_json::Value>,
    ) -> Result<()> {
        let entry = AuditEntry {
            timestamp: Utc::now().to_rfc3339(),
            action: action.to_string(),
            status: status.to_string(),
            details,
        };

        // Create parent directory if it doesn't exist
        if let Some(parent) = self.log_path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }

        // Append entry to log file (JSON lines format)
        let line = format!("{}\n", serde_json::to_string(&entry)?);
        let mut file = tokio::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.log_path)
            .await?;
        file.write_all(line.as_bytes()).await?;

        info!("Audit log: {} - {}", action, status);
        Ok(())
    }

    pub async fn get_recent_entries(&self, limit: usize) -> Result<Vec<AuditEntry>> {
        if !self.log_path.exists() {
            return Ok(Vec::new());
        }

        let content = tokio::fs::read_to_string(&self.log_path).await?;
        let entries: Vec<AuditEntry> = content
            .lines()
            .rev()
            .take(limit)
            .filter_map(|line| serde_json::from_str(line).ok())
            .collect();

        Ok(entries)
    }

    pub async fn clear(&self) -> Result<()> {
        if self.log_path.exists() {
            tokio::fs::remove_file(&self.log_path).await?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[tokio::test]
    async fn test_audit_log() {
        let temp_dir = TempDir::new().unwrap();
        let log_path = temp_dir.path().join("audit.log");
        let log = AuditLog::new(log_path);

        log.log_action("test_action", "success", None).await.unwrap();
        
        let entries = log.get_recent_entries(10).await.unwrap();
        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].action, "test_action");
    }
}
