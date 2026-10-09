import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

try:
    from scipy.signal import butter, filtfilt
    import pywt
except ImportError:  # pragma: no cover
    butter = None
    filtfilt = None
    pywt = None

# Configuración general
base_dir = Path(__file__).resolve().parent
sensor_cols = [0, 8, 16, 24, 32, 40, 48, 56]
classe_names = {0: "rock", 1: "scissors", 2: "paper", 3: "ok"}
colors = {0: "crimson", 1: "darkorange", 2: "forestgreen", 3: "royalblue"}


def filter_emg(signal: np.ndarray, fs: float = 200.0) -> np.ndarray:
    signal = np.asarray(signal, dtype=float)
    if signal.size == 0:
        return signal

    # Filtro wavelet: buena opción para EMG porque reduce ruido y mantiene forma del pulso.
    if pywt is not None:
        try:
            coeffs = pywt.wavedec(signal, 'db4', level=3)
            coeffs = [np.zeros_like(c) if i == 0 else c for i, c in enumerate(coeffs)]
            # Se conserva el detalle medio-bajo y se atenúa el ruido de alta frecuencia
            coeffs[1:] = [np.clip(c, -np.std(c) * 3, np.std(c) * 3) for c in coeffs[1:]]
            filtered = pywt.waverec(coeffs, 'db4')[:len(signal)]
            return filtered - np.mean(filtered)
        except Exception:
            pass

    if butter is not None and filtfilt is not None:
        nyquist = 0.5 * fs
        low = 20 / nyquist
        high = 450 / nyquist
        b, a = butter(4, [low, high], btype='bandpass')
        filtered = filtfilt(b, a, signal)
        return filtered - np.mean(filtered)

    filtered = np.convolve(signal, np.ones(5) / 5.0, mode='same')
    return filtered - np.mean(filtered)


def flatten_sensor_1(df: pd.DataFrame, max_rows: int = 50) -> np.ndarray:
    rows = min(max_rows, len(df))
    signal = df.iloc[:rows, sensor_cols].values.flatten()
    return filter_emg(signal)


def flatten_all_sensors(df: pd.DataFrame, max_rows: int = 50) -> dict[int, np.ndarray]:
    rows = min(max_rows, len(df))
    signals = {}
    for sensor_index in range(8):
        cols = [sensor_index + 8 * k for k in range(8)]
        signal = df.iloc[:rows, cols].values.flatten()
        signals[sensor_index] = filter_emg(signal)
    return signals


def load_class_data() -> dict[int, pd.DataFrame]:
    # Caso 1: archivos separados por clase (0.csv, 1.csv, 2.csv, 3.csv)
    class_files = {cls: base_dir / f"{cls}.csv" for cls in range(4)}
    if all(path.exists() for path in class_files.values()):
        frames = {}
        for cls, path in class_files.items():
            frames[cls] = pd.read_csv(path, header=None)
        print("Se cargaron los archivos separados por clase.")
        return frames

    # Caso 2: un solo CSV con la última columna como etiqueta
    csv_path = base_dir / "emg_vr.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, header=None)
        print(f"Archivo único cargado: {df.shape[0]} filas, {df.shape[1]} columnas.")

        if df.shape[1] >= 2:
            last_col = df.iloc[:, -1]
            unique_classes = sorted(last_col.dropna().unique().tolist())
            print(f"Clases presentes en el CSV: {unique_classes}")
            if len(unique_classes) > 1:
                grouped = {}
                for cls in unique_classes:
                    grouped[int(cls)] = df.loc[df.iloc[:, -1] == cls].drop(columns=df.columns[-1]).copy()
                return grouped

        # Si el CSV tiene una sola clase, la tratamos como la clase 0
        return {0: df.copy()}

    raise FileNotFoundError("No se encontró '0.csv', '1.csv', '2.csv', '3.csv' ni 'emg_vr.csv' en la carpeta del proyecto.")


try:
    class_frames = load_class_data()
    if not class_frames:
        raise ValueError("No se encontraron datos para graficar.")

    print(f"Se van a graficar las clases: {sorted(class_frames.keys())}")

    classes_to_plot = sorted(class_frames.keys())
    total_plots = len(classes_to_plot)
    rows = int(np.ceil(total_plots / 2))
    cols = 2 if total_plots > 1 else 1

    # 1) Una imagen por clase, con los 8 sensores dentro de esa imagen, y con filtro EMG
    class_dir = base_dir / "graficas_por_clase"
    class_dir.mkdir(exist_ok=True)

    for old_plot in class_dir.glob("clase_*.png"):
        if not old_plot.name.endswith("_promedio.png"):
            old_plot.unlink()

    for cls in classes_to_plot:
        df_cls = class_frames[cls]
        signals = flatten_all_sensors(df_cls, max_rows=50)
        tiempo_total = np.arange(len(next(iter(signals.values())))) / 200.0

        # Promedio separado por clase con filtro aplicado
        avg_fig, avg_ax = plt.subplots(figsize=(12, 5))
        avg_signal = np.mean(np.vstack([signal for signal in signals.values()]), axis=0)
        avg_ax.plot(tiempo_total, avg_signal, color=colors.get(cls, "tab:blue"), linewidth=2)
        avg_ax.set_title(f"Promedio clase {cls} - {classe_names.get(cls, 'unknown')}")
        avg_ax.set_xlabel("Tiempo (s)")
        avg_ax.set_ylabel("Amplitud EMG promedio")
        avg_ax.grid(True, linestyle="--", alpha=0.6)
        avg_fig.tight_layout()
        avg_output = class_dir / f"clase_{cls}_promedio.png"
        avg_fig.savefig(avg_output, dpi=200)
        print(f"{avg_output.name} guardado en: {avg_output}")

    # 2) Gráfica individual por clase con solo sensor 1 (ya filtrado)
    fig, axes = plt.subplots(rows, cols, figsize=(14, 5 * rows), squeeze=False)
    axes_flat = axes.flatten()

    for i, cls in enumerate(classes_to_plot):
        ax = axes_flat[i]
        df_cls = class_frames[cls]
        signal = flatten_sensor_1(df_cls, max_rows=50)
        tiempo = np.arange(len(signal)) / 200.0

        ax.plot(tiempo, signal, color=colors.get(cls, "black"), linewidth=1.5)
        ax.set_title(f"Clase {cls} - {classe_names.get(cls, 'unknown')}")
        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Amplitud EMG")
        ax.grid(True, linestyle="--", alpha=0.6)

    for j in range(total_plots, len(axes_flat)):
        axes_flat[j].axis("off")

    fig.tight_layout()
    fig.savefig(base_dir / "todas_las_clases_emg_sensor1.png", dpi=200)
    print(f"Gráfica individual por clase guardada en: {base_dir / 'todas_las_clases_emg_sensor1.png'}")

except FileNotFoundError as e:
    print(f"Error: {e}")
except ValueError as e:
    print(f"Error de datos: {e}")