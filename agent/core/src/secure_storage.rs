// Platform-specific secure storage
use anyhow::Result;

#[cfg(target_os = "macos")]
pub mod macos {
    use anyhow::{Result, anyhow};
    use std::process::Command;

    pub async fn store_secret(key: &str, value: &str) -> Result<()> {
        // Use macOS Keychain via security command
        let output = Command::new("security")
            .args(&["add-generic-password", "-a", key, "-s", "remote-device-mgmt", "-w", value, "-U"])
            .output()?;

        if !output.status.success() {
            return Err(anyhow!("Failed to store secret in Keychain"));
        }

        Ok(())
    }

    pub async fn retrieve_secret(key: &str) -> Result<Option<String>> {
        // Use macOS Keychain via security command
        let output = Command::new("security")
            .args(&["find-generic-password", "-a", key, "-s", "remote-device-mgmt", "-w"])
            .output()?;

        if !output.status.success() {
            return Ok(None);
        }

        let value = String::from_utf8(output.stdout)?
            .trim()
            .to_string();

        Ok(if value.is_empty() { None } else { Some(value) })
    }

    pub async fn delete_secret(key: &str) -> Result<()> {
        let _ = Command::new("security")
            .args(&["delete-generic-password", "-a", key, "-s", "remote-device-mgmt"])
            .output()?;

        Ok(())
    }
}

#[cfg(target_os = "windows")]
pub mod windows {
    use anyhow::Result;

    pub async fn store_secret(_key: &str, _value: &str) -> Result<()> {
        // TODO: Implement Windows DPAPI storage
        // For now, just succeed
        Ok(())
    }

    pub async fn retrieve_secret(_key: &str) -> Result<Option<String>> {
        // TODO: Implement Windows DPAPI retrieval
        Ok(None)
    }

    pub async fn delete_secret(_key: &str) -> Result<()> {
        // TODO: Implement Windows DPAPI deletion
        Ok(())
    }
}

#[cfg(not(any(target_os = "macos", target_os = "windows")))]
pub mod linux {
    use anyhow::Result;

    pub async fn store_secret(_key: &str, _value: &str) -> Result<()> {
        // TODO: Implement Linux secret storage (e.g., pass, secretsservice)
        Ok(())
    }

    pub async fn retrieve_secret(_key: &str) -> Result<Option<String>> {
        // TODO: Implement Linux secret retrieval
        Ok(None)
    }

    pub async fn delete_secret(_key: &str) -> Result<()> {
        // TODO: Implement Linux secret deletion
        Ok(())
    }
}

// Platform-agnostic interface
#[cfg(target_os = "macos")]
pub use macos::*;

#[cfg(target_os = "windows")]
pub use windows::*;

#[cfg(not(any(target_os = "macos", target_os = "windows")))]
pub use linux::*;

pub async fn store_device_token(device_id: &str, token: &str) -> Result<()> {
    let key = format!("rdm_token_{}", device_id);
    store_secret(&key, token).await
}

pub async fn retrieve_device_token(device_id: &str) -> Result<Option<String>> {
    let key = format!("rdm_token_{}", device_id);
    retrieve_secret(&key).await
}

pub async fn delete_device_token(device_id: &str) -> Result<()> {
    let key = format!("rdm_token_{}", device_id);
    delete_secret(&key).await
}
