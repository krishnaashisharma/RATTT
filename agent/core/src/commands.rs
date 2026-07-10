// Command execution handlers
use serde::{Deserialize, Serialize};
use sysinfo::System;
use anyhow::Result;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "command")]
pub enum Command {
    #[serde(rename = "ping")]
    Ping,
    #[serde(rename = "get_system_info")]
    GetSystemInfo,
    #[serde(rename = "list_processes")]
    ListProcesses { limit: Option<usize> },
    #[serde(rename = "file_transfer")]
    FileTransfer { path: String },
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CommandResponse {
    pub command: String,
    pub status: String,
    pub result: serde_json::Value,
}

pub async fn execute(cmd: Command) -> Result<CommandResponse> {
    match cmd {
        Command::Ping => execute_ping().await,
        Command::GetSystemInfo => execute_system_info().await,
        Command::ListProcesses { limit } => execute_list_processes(limit).await,
        Command::FileTransfer { path } => execute_file_transfer(&path).await,
    }
}

async fn execute_ping() -> Result<CommandResponse> {
    Ok(CommandResponse {
        command: "ping".to_string(),
        status: "success".to_string(),
        result: serde_json::json!({
            "message": "pong"
        }),
    })
}

async fn execute_system_info() -> Result<CommandResponse> {
    let mut sys = System::new_all();
    sys.refresh_all();

    let result = serde_json::json!({
        "os": std::env::consts::OS,
        "arch": std::env::consts::ARCH,
        "hostname": hostname::get()
            .ok()
            .and_then(|h| h.into_string().ok())
            .unwrap_or_else(|| "unknown".to_string()),
        "cpu_count": sys.cpus().len(),
        "total_memory_mb": sys.total_memory() / 1024,
        "available_memory_mb": sys.available_memory() / 1024,
        "uptime_seconds": System::uptime(),
    });

    Ok(CommandResponse {
        command: "get_system_info".to_string(),
        status: "success".to_string(),
        result,
    })
}

async fn execute_list_processes(limit: Option<usize>) -> Result<CommandResponse> {
    let mut sys = System::new_all();
    sys.refresh_processes();

    let limit = limit.unwrap_or(20);
    let mut processes: Vec<_> = sys
        .processes()
        .values()
        .map(|p| {
            serde_json::json!({
                "pid": p.pid().as_u32(),
                "name": p.name(),
                "cpu_usage": p.cpu_usage(),
                "memory_mb": p.memory() / 1024,
            })
        })
        .collect();

    // Sort by CPU usage (descending)
    processes.sort_by(|a, b| {
        let cpu_a = a["cpu_usage"].as_f64().unwrap_or(0.0);
        let cpu_b = b["cpu_usage"].as_f64().unwrap_or(0.0);
        cpu_b.partial_cmp(&cpu_a).unwrap_or(std::cmp::Ordering::Equal)
    });

    processes.truncate(limit);

    Ok(CommandResponse {
        command: "list_processes".to_string(),
        status: "success".to_string(),
        result: serde_json::json!({
            "processes": processes,
            "total_count": sys.processes().len(),
        }),
    })
}

async fn execute_file_transfer(path: &str) -> Result<CommandResponse> {
    // Check if file exists
    if !std::path::Path::new(path).exists() {
        return Ok(CommandResponse {
            command: "file_transfer".to_string(),
            status: "error".to_string(),
            result: serde_json::json!({
                "error": "File not found"
            }),
        });
    }

    // Get file metadata
    let metadata = tokio::fs::metadata(path).await?;
    let file_size = metadata.len();

    Ok(CommandResponse {
        command: "file_transfer".to_string(),
        status: "success".to_string(),
        result: serde_json::json!({
            "path": path,
            "size_bytes": file_size,
            "ready_for_transfer": true,
        }),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_ping() {
        let cmd = Command::Ping;
        let response = execute(cmd).await.unwrap();
        assert_eq!(response.command, "ping");
        assert_eq!(response.status, "success");
    }

    #[tokio::test]
    async fn test_system_info() {
        let cmd = Command::GetSystemInfo;
        let response = execute(cmd).await.unwrap();
        assert_eq!(response.command, "get_system_info");
        assert_eq!(response.status, "success");
        assert!(response.result.get("os").is_some());
    }

    #[tokio::test]
    async fn test_list_processes() {
        let cmd = Command::ListProcesses { limit: Some(5) };
        let response = execute(cmd).await.unwrap();
        assert_eq!(response.command, "list_processes");
        assert_eq!(response.status, "success");
    }
}
