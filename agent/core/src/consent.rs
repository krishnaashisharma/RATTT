// System-tray consent UI and activity log
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::info;
use anyhow::Result;
use chrono::Utc;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum ConsentState {
    Connected,
    Paused,
    Revoked,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActivityLogEntry {
    pub timestamp: String,
    pub action: String,
    pub details: Option<String>,
}

pub struct ConsentManager {
    state: Arc<RwLock<ConsentState>>,
    activity_log: Arc<RwLock<Vec<ActivityLogEntry>>>,
}

impl ConsentManager {
    pub fn new() -> Self {
        ConsentManager {
            state: Arc::new(RwLock::new(ConsentState::Connected)),
            activity_log: Arc::new(RwLock::new(Vec::new())),
        }
    }

    pub async fn get_state(&self) -> ConsentState {
        *self.state.read().await
    }

    pub async fn set_state(&self, state: ConsentState) {
        *self.state.write().await = state;
        
        let action = match state {
            ConsentState::Connected => "connected",
            ConsentState::Paused => "paused",
            ConsentState::Revoked => "revoked",
        };
        
        let _ = self.log_activity(action, None).await;
        info!("Consent: {}", action);
    }

    pub async fn pause(&self) {
        self.set_state(ConsentState::Paused).await;
    }

    pub async fn resume(&self) {
        self.set_state(ConsentState::Connected).await;
    }

    pub async fn revoke(&self) {
        self.set_state(ConsentState::Revoked).await;
    }

    pub async fn is_paused(&self) -> bool {
        self.get_state().await == ConsentState::Paused
    }

    pub async fn is_revoked(&self) -> bool {
        self.get_state().await == ConsentState::Revoked
    }

    pub async fn log_activity(&self, action: &str, details: Option<String>) -> Result<()> {
        let entry = ActivityLogEntry {
            timestamp: Utc::now().to_rfc3339(),
            action: action.to_string(),
            details,
        };

        let mut log = self.activity_log.write().await;
        log.push(entry);

        // Keep only last 50 entries
        if log.len() > 50 {
            log.remove(0);
        }

        Ok(())
    }

    pub async fn get_recent_activity(&self, limit: usize) -> Vec<ActivityLogEntry> {
        let log = self.activity_log.read().await;
        log.iter()
            .rev()
            .take(limit)
            .cloned()
            .collect()
    }

    pub async fn clear_activity(&self) -> Result<()> {
        self.activity_log.write().await.clear();
        Ok(())
    }

    pub async fn get_status_summary(&self) -> serde_json::Value {
        let state = self.get_state().await;
        let state_str = match state {
            ConsentState::Connected => "connected",
            ConsentState::Paused => "paused",
            ConsentState::Revoked => "revoked",
        };

        let recent_activity = self.get_recent_activity(10).await;

        serde_json::json!({
            "state": state_str,
            "recent_activity": recent_activity,
        })
    }
}

pub async fn spawn_consent_ui() -> Result<ConsentManager> {
    // TODO: Implement system-tray UI
    // For now, just return a manager that can be used programmatically
    let manager = ConsentManager::new();
    
    // Log initial state
    manager.log_activity("agent_started", None).await?;
    
    info!("Consent UI initialized (system-tray not available in sandbox)");
    Ok(manager)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_consent_state() {
        let manager = ConsentManager::new();
        
        assert_eq!(manager.get_state().await, ConsentState::Connected);
        
        manager.pause().await;
        assert!(manager.is_paused().await);
        
        manager.resume().await;
        assert!(!manager.is_paused().await);
        
        manager.revoke().await;
        assert!(manager.is_revoked().await);
    }

    #[tokio::test]
    async fn test_activity_log() {
        let manager = ConsentManager::new();
        
        manager.log_activity("test_action", Some("details".to_string())).await.unwrap();
        manager.log_activity("another_action", None).await.unwrap();
        
        let activity = manager.get_recent_activity(10).await;
        assert!(activity.len() >= 2);
        assert_eq!(activity[0].action, "another_action");
    }

    #[tokio::test]
    async fn test_activity_log_limit() {
        let manager = ConsentManager::new();
        
        // Add 60 entries
        for i in 0..60 {
            manager.log_activity(&format!("action_{}", i), None).await.unwrap();
        }
        
        let activity = manager.get_recent_activity(100).await;
        // Should only have 50 (limit)
        assert_eq!(activity.len(), 50);
    }
}
