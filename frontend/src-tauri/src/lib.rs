use std::sync::Mutex;
use tauri::{Manager, RunEvent};
use tauri_plugin_shell::{process::CommandChild, process::CommandEvent, ShellExt};

struct SidecarState(Mutex<Option<CommandChild>>);

fn spawn_sidecar(app: &tauri::AppHandle) {
    let (mut rx, child) = app
        .shell()
        .sidecar("asbizdev-crawler")
        .expect("failed to create sidecar command")
        .spawn()
        .expect("failed to spawn crawler sidecar");

    if let Some(state) = app.try_state::<SidecarState>() {
        *state.0.lock().unwrap() = Some(child);
    }

    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    log::info!("[crawler] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Stderr(line) => {
                    log::warn!("[crawler] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Error(err) => {
                    log::error!("[crawler] sidecar error: {}", err);
                }
                CommandEvent::Terminated(payload) => {
                    log::warn!("[crawler] sidecar exited: {:?}", payload);
                }
                _ => {}
            }
        }
    });
}

fn kill_sidecar(app: &tauri::AppHandle) {
    if let Some(state) = app.try_state::<SidecarState>() {
        if let Some(child) = state.0.lock().unwrap().take() {
            let pid = child.pid();

            // PyInstaller's onefile bootloader on Windows launches the real
            // interpreter as a child process, so killing only the tracked
            // process leaves that child (and uvicorn) running. `taskkill /T`
            // kills the whole tree instead.
            #[cfg(windows)]
            {
                use std::os::windows::process::CommandExt;
                const CREATE_NO_WINDOW: u32 = 0x08000000;
                let _ = std::process::Command::new("taskkill")
                    .args(["/F", "/T", "/PID", &pid.to_string()])
                    .creation_flags(CREATE_NO_WINDOW)
                    .output();
            }

            #[cfg(not(windows))]
            {
                // PyInstaller's onefile bootloader forks the real interpreter
                // as a child process on macOS/Linux too, so killing only the
                // tracked process would leave it (and uvicorn) running.
                // `pkill -P` kills that child first, then the bootloader itself.
                let _ = std::process::Command::new("pkill")
                    .args(["-P", &pid.to_string()])
                    .output();
                let _ = child.kill();
            }
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            // A second launch attempt: focus the existing window instead of
            // starting a duplicate crawler sidecar.
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_shell::init())
        .manage(SidecarState(Mutex::new(None)))
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            spawn_sidecar(&app.handle());

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let RunEvent::ExitRequested { .. } | RunEvent::Exit = event {
                kill_sidecar(app_handle);
            }
        });
}
