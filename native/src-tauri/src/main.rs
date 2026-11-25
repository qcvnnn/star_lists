#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{net::Ipv4Addr, time::Duration};

#[tauri::command]
async fn load_catalog(host: &str) -> Result<serde_json::Value, String> {
    let address: Ipv4Addr = host.parse().map_err(|_| "Введите IPv4-адрес сервера")?;
    if !address.is_private() {
        return Err("Укажите адрес частной локальной сети".into());
    }
    let url = format!("http://{address}:8000/api/star_list/native/catalog");
    let client = reqwest::Client::builder()
        .no_proxy()
        .redirect(reqwest::redirect::Policy::none())
        .timeout(Duration::from_secs(8))
        .build()
        .map_err(|error| error.to_string())?;
    client.get(url).send().await
        .and_then(reqwest::Response::error_for_status)
        .map_err(|error| error.to_string())?
        .json().await.map_err(|error| error.to_string())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![load_catalog])
        .run(tauri::generate_context!())
        .expect("failed to start Star Lists");
}
