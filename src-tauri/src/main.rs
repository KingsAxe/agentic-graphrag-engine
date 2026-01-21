use tauri::api::process::{Command, CommandEvent};
use tauri::Manager;

fn main() {
  tauri::Builder::default()
    .setup(|app| {
      // Use app dir as working directory (helps relative paths in packaged mode)
      let app_dir = app
        .path_resolver()
        .app_dir()
        .expect("failed to resolve app dir");

      let (mut rx, _child) = Command::new_sidecar("research-engine")
        .expect("Failed to create sidecar command")
        .current_dir(app_dir)
        .spawn()
        .expect("Failed to spawn sidecar");

      // Print both stdout + stderr
      tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
          match event {
            CommandEvent::Stdout(line) => println!("Python Engine: {}", line),
            CommandEvent::Stderr(line) => eprintln!("Python Engine [ERR]: {}", line),
            _ => {}
          }
        }
      });

      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
