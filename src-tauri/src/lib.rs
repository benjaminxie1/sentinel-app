use std::sync::{Arc, Mutex};
use std::process::{Child, Command, Stdio};
use std::time::Duration;
use tauri::{AppHandle, Emitter, State};
use serde::{Deserialize, Serialize};
use anyhow::Result;

#[derive(Debug, Serialize, Deserialize)]
pub struct DashboardData {
    pub alerts: serde_json::Value,
    pub config: serde_json::Value,
    pub timestamp: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemStatus {
    pub backend_running: bool,
    pub python_pid: Option<u32>,
    pub last_update: f64,
}

#[derive(Clone)]
pub struct AppState {
    pub python_process: Arc<Mutex<Option<Child>>>,
    pub api_base_url: String,
    pub client: reqwest::Client,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            python_process: Arc::new(Mutex::new(None)),
            api_base_url: "http://localhost:8765".to_string(),
            client: reqwest::Client::new(),
        }
    }
}

// Internal function for backend startup (used in setup and command)
async fn start_python_backend_internal(state: Arc<AppState>) -> Result<bool, String> {
    let python_process = state.python_process.clone();
    
    // Check if already running
    {
        let mut process_guard = python_process.lock().unwrap();
        if let Some(ref mut child) = *process_guard {
            match child.try_wait() {
                Ok(Some(_)) => {
                    // Process has exited, clean up
                    *process_guard = None;
                }
                Ok(None) => {
                    // Process is still running
                    println!("Python backend already running with PID: {}", child.id());
                    return Ok(true);
                }
                Err(_) => {
                    *process_guard = None;
                }
            }
        }
    }

    // Additional check: test if port 8765 is already in use
    if let Ok(_) = std::net::TcpStream::connect("127.0.0.1:8765") {
        println!("Port 8765 already in use, backend likely already running");
        return Ok(true);
    }

    // Start Python backend with virtual environment
    println!("Starting Python backend from directory: {:?}", std::env::current_dir());
    println!("Attempting to run: venv/bin/python3 backend/api_server.py");
    
    let child = Command::new("../venv/bin/python3")
        .arg("-u")  // Unbuffered output
        .arg("../backend/api_server.py")
        .stdout(Stdio::inherit())  // Show output for debugging
        .stderr(Stdio::inherit())  // Show errors for debugging
        .spawn()
        .map_err(|e| {
            eprintln!("Failed to start Python backend: {}", e);
            eprintln!("Current working directory: {:?}", std::env::current_dir());
            format!("Failed to start Python backend: {}", e)
        })?;

    let pid = child.id();
    
    {
        let mut process_guard = python_process.lock().unwrap();
        *process_guard = Some(child);
    }
    
    // Give the backend time to start
    tokio::time::sleep(Duration::from_secs(3)).await;
    
    println!("Python backend started with PID: {}", pid);
    Ok(true)
}

#[tauri::command]
async fn start_python_backend(state: State<'_, AppState>) -> Result<bool, String> {
    // Create Arc from the managed state
    let state_arc = Arc::new(state.inner().clone());
    start_python_backend_internal(state_arc).await
}

#[tauri::command]
async fn stop_python_backend(state: State<'_, AppState>) -> Result<bool, String> {
    let mut process_guard = state.python_process.lock().unwrap();
    
    if let Some(mut child) = process_guard.take() {
        let _ = child.kill();
        let _ = child.wait();
        println!("Python backend stopped");
        Ok(true)
    } else {
        Ok(false)
    }
}

#[tauri::command]
async fn get_dashboard_data(state: State<'_, AppState>) -> Result<DashboardData, String> {
    let url = format!("{}/api/dashboard", state.api_base_url);
    
    let response = state.client
        .get(&url)
        .timeout(Duration::from_secs(5))
        .send()
        .await
        .map_err(|e| format!("Failed to fetch dashboard data: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("API error: {}", response.status()));
    }

    let data: DashboardData = response.json()
        .await
        .map_err(|e| format!("Failed to parse dashboard data: {}", e))?;

    Ok(data)
}

#[tauri::command(rename_all = "snake_case")]
async fn update_threshold(
    state: State<'_, AppState>,
    threshold_name: String,
    value: f64
) -> Result<bool, String> {
    let url = format!("{}/api/threshold", state.api_base_url);
    
    let payload = serde_json::json!({
        "threshold_name": threshold_name,
        "value": value
    });

    let response = state.client
        .post(&url)
        .json(&payload)
        .timeout(Duration::from_secs(5))
        .send()
        .await
        .map_err(|e| format!("Failed to update threshold: {}", e))?;

    if !response.status().is_success() {
        return Ok(false);
    }

    // Parse the JSON response to get the actual success value
    let response_data: serde_json::Value = response.json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    Ok(response_data.get("success").and_then(|v| v.as_bool()).unwrap_or(false))
}

#[tauri::command]
async fn acknowledge_alert(
    state: State<'_, AppState>,
    alert_id: String
) -> Result<bool, String> {
    let url = format!("{}/api/acknowledge", state.api_base_url);
    
    let payload = serde_json::json!({
        "alert_id": alert_id
    });

    let response = state.client
        .post(&url)
        .json(&payload)
        .timeout(Duration::from_secs(5))
        .send()
        .await
        .map_err(|e| format!("Failed to acknowledge alert: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("API error: {}", response.status()));
    }

    // Parse the JSON response to get the actual success value
    let response_data: serde_json::Value = response.json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    Ok(response_data.get("success").and_then(|v| v.as_bool()).unwrap_or(false))
}

#[tauri::command]
async fn get_camera_feeds(state: State<'_, AppState>) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/cameras", state.api_base_url);
    
    let response = state.client
        .get(&url)
        .timeout(Duration::from_secs(5))
        .send()
        .await
        .map_err(|e| format!("Failed to fetch camera feeds: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("API error: {}", response.status()));
    }

    let data: serde_json::Value = response.json()
        .await
        .map_err(|e| format!("Failed to parse camera data: {}", e))?;

    Ok(data)
}

#[tauri::command]
async fn get_system_status(state: State<'_, AppState>) -> Result<SystemStatus, String> {
    let process_guard = state.python_process.lock().unwrap();
    
    let (backend_running, python_pid) = if let Some(ref child) = *process_guard {
        (true, Some(child.id()))
    } else {
        (false, None)
    };

    Ok(SystemStatus {
        backend_running,
        python_pid,
        last_update: std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs_f64(),
    })
}

#[tauri::command]
async fn get_camera_frame(
    state: State<'_, AppState>,
    camera_id: String
) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/cameras/{}/frame", state.api_base_url, camera_id);
    
    let response = state.client
        .get(&url)
        .timeout(Duration::from_secs(5))
        .send()
        .await
        .map_err(|e| format!("Failed to fetch camera frame: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("API error: {}", response.status()));
    }

    let data: serde_json::Value = response.json()
        .await
        .map_err(|e| format!("Failed to parse camera frame data: {}", e))?;

    Ok(data)
}

#[tauri::command]
async fn get_system_metrics(state: State<'_, AppState>) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/metrics", state.api_base_url);
    
    let response = state.client
        .get(&url)
        .timeout(Duration::from_secs(5))
        .send()
        .await
        .map_err(|e| format!("Failed to fetch system metrics: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("API error: {}", response.status()));
    }

    let data: serde_json::Value = response.json()
        .await
        .map_err(|e| format!("Failed to parse system metrics: {}", e))?;

    Ok(data)
}

#[tauri::command]
async fn discover_cameras(
    state: State<'_, AppState>,
    timeout: Option<u32>
) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/cameras/discover", state.api_base_url);
    
    let payload = serde_json::json!({
        "timeout": timeout.unwrap_or(5)
    });

    let response = state.client
        .post(&url)
        .json(&payload)
        .timeout(Duration::from_secs(10))
        .send()
        .await
        .map_err(|e| format!("Failed to discover cameras: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("API error: {}", response.status()));
    }

    let data: serde_json::Value = response.json()
        .await
        .map_err(|e| format!("Failed to parse discovery data: {}", e))?;

    Ok(data)
}

#[tauri::command]
async fn add_camera(
    state: State<'_, AppState>,
    camera_id: String,
    rtsp_url: String,
    username: Option<String>,
    password: Option<String>
) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/cameras/add", state.api_base_url);
    
    let mut payload = serde_json::json!({
        "camera_id": camera_id,
        "rtsp_url": rtsp_url,
        "enabled": true
    });

    if let Some(user) = username {
        payload["username"] = serde_json::Value::String(user);
    }
    if let Some(pass) = password {
        payload["password"] = serde_json::Value::String(pass);
    }

    let response = state.client
        .post(&url)
        .json(&payload)
        .timeout(Duration::from_secs(10))
        .send()
        .await
        .map_err(|e| format!("Failed to add camera: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("API error: {}", response.status()));
    }

    let data: serde_json::Value = response.json()
        .await
        .map_err(|e| format!("Failed to parse add camera response: {}", e))?;

    Ok(data)
}

#[tauri::command]
async fn test_camera(
    state: State<'_, AppState>,
    camera_id: String,
    rtsp_url: String,
    username: Option<String>,
    password: Option<String>
) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/cameras/{}/test", state.api_base_url, camera_id);
    
    let mut payload = serde_json::json!({
        "rtsp_url": rtsp_url
    });

    if let Some(user) = username {
        payload["username"] = serde_json::Value::String(user);
    }
    if let Some(pass) = password {
        payload["password"] = serde_json::Value::String(pass);
    }

    let response = state.client
        .post(&url)
        .json(&payload)
        .timeout(Duration::from_secs(15))
        .send()
        .await
        .map_err(|e| format!("Failed to test camera: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("API error: {}", response.status()));
    }

    let data: serde_json::Value = response.json()
        .await
        .map_err(|e| format!("Failed to parse test camera response: {}", e))?;

    Ok(data)
}

#[tauri::command]
async fn remove_camera(
    state: State<'_, AppState>,
    camera_id: String
) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/cameras/{}/remove", state.api_base_url, camera_id);
    
    let response = state.client
        .delete(&url)
        .timeout(Duration::from_secs(10))
        .send()
        .await
        .map_err(|e| format!("Failed to remove camera: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("API error: {}", response.status()));
    }

    let data: serde_json::Value = response.json()
        .await
        .map_err(|e| format!("Failed to parse remove camera response: {}", e))?;

    Ok(data)
}

// Real-time data streaming setup
fn setup_real_time_data_stream(app_handle: AppHandle, state: Arc<AppState>) {
    // Use Tauri's async runtime instead of tokio::spawn
    tauri::async_runtime::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(5));
        
        loop {
            interval.tick().await;
            
            // Try to fetch dashboard data and emit update
            let url = format!("{}/api/dashboard", state.api_base_url);
            if let Ok(response) = state.client.get(&url).timeout(Duration::from_secs(5)).send().await {
                if let Ok(data) = response.json::<DashboardData>().await {
                    let _ = app_handle.emit("real-time-update", &data);
                }
            }
        }
    });
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app_state = AppState::new();
    let state_arc = Arc::new(app_state);

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_fs::init())
        .manage(state_arc.as_ref().clone())
        .setup(move |app| {
            let app_handle = app.handle().clone();
            let state_clone = state_arc.clone();
            
            // Auto-start Python backend
            let backend_state = state_clone.clone();
            tauri::async_runtime::spawn(async move {
                if let Err(e) = start_python_backend_internal(backend_state).await {
                    eprintln!("Failed to auto-start Python backend: {}", e);
                }
            });
            
            // Setup real-time data streaming
            setup_real_time_data_stream(app_handle, state_clone);
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            greet,
            start_python_backend,
            stop_python_backend,
            get_dashboard_data,
            update_threshold,
            acknowledge_alert,
            get_camera_feeds,
            get_camera_frame,
            discover_cameras,
            add_camera,
            test_camera,
            remove_camera,
            get_system_status,
            get_system_metrics
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}