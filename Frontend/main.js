const { app, BrowserWindow } = require('electron');
const path = require('path');

let mainWindow;

const createWindow = () => {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1024,
        minHeight: 700,
        title: 'TransControl - Sistema de Gestión',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
        },
    });

    // Cargar el Login (index.html está DENTRO de Frontend/)
    mainWindow.loadFile(path.join('Frontend', 'index.html'));

    // Quitar la barra de menú
    mainWindow.setMenuBarVisibility(false);

    // Abrir DevTools en desarrollo (quitar en producción)
    // mainWindow.webContents.openDevTools();

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
};

// Cuando Electron esté listo
app.whenReady().then(() => {
    createWindow();

    // En macOS, recrear ventana si no hay ninguna
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

// Salir cuando todas las ventanas estén cerradas
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});