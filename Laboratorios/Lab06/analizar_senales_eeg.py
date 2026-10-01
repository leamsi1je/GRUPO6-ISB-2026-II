"""Grafica las senales OpenSignals del Lab06 en tiempo y frecuencia."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, iirnotch, savgol_filter, sosfiltfilt, tf2sos


LAB_DIR = Path(__file__).resolve().parent
DATA_DIR = LAB_DIR / "EEG_señales"
OUTPUT_DIR = LAB_DIR / "Graficas_EEG"
MAX_TIME_POINTS = 20_000
TIME_WINDOW_SECONDS = 10
FILTER_LOW_HZ = 0.3
FILTER_HIGH_HZ = 48
FILTER_ORDER = 8
LINE_NOISE_HZ = 60
NOTCH_QUALITY = 30
DISPLAY_SMOOTHING_MS = 25
MAX_FREQUENCY_HZ = FILTER_HIGH_HZ
EEG_BANDS = [
    ("Delta", 0, 4, "#dce9e2"),
    ("Theta", 4, 8, "#f2e4ca"),
    ("Alfa", 8, 12, "#dce9f2"),
    ("Beta", 12, 25, "#f2ddda"),
    ("Gamma", 25, MAX_FREQUENCY_HZ, "#e6e2ef"),
]
BAND_POWER_LIMITS = [
    ("Delta", FILTER_LOW_HZ, 4),
    ("Theta", 4, 8),
    ("Alfa", 8, 12),
    ("Beta", 12, 25),
    ("Gamma", 25, FILTER_HIGH_HZ),
]


def read_opensignals_file(file_path):
    """Retorna las muestras, la frecuencia y la etiqueta desde un archivo OpenSignals."""
    with file_path.open("r", encoding="utf-8-sig") as file:
        file.readline()
        header_line = file.readline()

    metadata_by_device = json.loads(header_line.lstrip("# "))
    metadata = next(iter(metadata_by_device.values()))
    columns = metadata["column"]
    signal_label = metadata["label"][0]
    signal_column = columns.index(signal_label)
    sampling_rate = float(metadata["sampling rate"])
    samples = np.loadtxt(file_path, comments="#", usecols=signal_column)

    return samples, sampling_rate, signal_label


def filter_eeg(samples, sampling_rate):
    """Aplica pasa-banda EEG y notch de 60 Hz, ambos en fase cero."""
    if sampling_rate / 2 <= FILTER_HIGH_HZ:
        raise ValueError("La frecuencia de muestreo debe ser mayor que 96 Hz")
    if sampling_rate / 2 <= LINE_NOISE_HZ:
        raise ValueError("La frecuencia de Nyquist debe superar los 60 Hz")

    bandpass_sections = butter(
        FILTER_ORDER,
        [FILTER_LOW_HZ, FILTER_HIGH_HZ],
        btype="bandpass",
        fs=sampling_rate,
        output="sos",
    )
    notch_numerator, notch_denominator = iirnotch(
        LINE_NOISE_HZ, Q=NOTCH_QUALITY, fs=sampling_rate
    )
    notch_sections = tf2sos(notch_numerator, notch_denominator)
    sections = np.vstack((notch_sections, bandpass_sections))
    return sosfiltfilt(sections, samples)


def welch_power(samples, sampling_rate, segment_length):
    """Estima la densidad espectral promediando segmentos Hann solapados."""
    overlap = segment_length // 2
    step = segment_length - overlap
    window = np.hanning(segment_length)
    normalization = sampling_rate * np.sum(window**2)
    power = np.zeros(segment_length // 2 + 1)
    segment_count = 0

    for start in range(0, samples.size - segment_length + 1, step):
        segment = samples[start : start + segment_length]
        spectrum = np.fft.rfft((segment - np.mean(segment)) * window)
        periodogram = np.abs(spectrum) ** 2 / normalization
        if segment_length % 2 == 0:
            periodogram[1:-1] *= 2
        else:
            periodogram[1:] *= 2
        power += periodogram
        segment_count += 1

    frequencies = np.fft.rfftfreq(segment_length, d=1 / sampling_rate)
    return frequencies, power / segment_count


def relative_band_power(frequencies, power):
    """Calcula el porcentaje de potencia integrado en cada banda EEG visible."""
    total_mask = (frequencies >= FILTER_LOW_HZ) & (frequencies <= FILTER_HIGH_HZ)
    total_power = np.trapezoid(power[total_mask], frequencies[total_mask])
    return {
        name: 100
        * np.trapezoid(
            power[(frequencies >= low) & (frequencies < high)],
            frequencies[(frequencies >= low) & (frequencies < high)],
        )
        / total_power
        for name, low, high in BAND_POWER_LIMITS
    }


def plot_recording(
    file_path, title, output_stem, start_seconds=None, end_seconds=None
):
    samples, sampling_rate, signal_label = read_opensignals_file(file_path)
    samples = filter_eeg(samples, sampling_rate)
    first_sample = int(round((start_seconds or 0) * sampling_rate))
    last_sample = (
        int(round(end_seconds * sampling_rate))
        if end_seconds is not None
        else samples.size
    )
    if first_sample < 0 or last_sample > samples.size or last_sample - first_sample < 2:
        raise ValueError(f"Intervalo no valido para {file_path.name}")

    selected_samples = samples[first_sample:last_sample]
    time = np.arange(first_sample, last_sample) / sampling_rate
    segment_length = min(4096, selected_samples.size)
    frequencies, power = welch_power(selected_samples, sampling_rate, segment_length)
    band_power = relative_band_power(frequencies, power)
    smoothing_window = max(3, int(round(sampling_rate * DISPLAY_SMOOTHING_MS / 1000)))
    if smoothing_window % 2 == 0:
        smoothing_window += 1
    display_window = min(
        smoothing_window,
        selected_samples.size if selected_samples.size % 2 else selected_samples.size - 1,
    )
    display_samples = savgol_filter(selected_samples, display_window, polyorder=2)
    time_sample_count = min(
        selected_samples.size, int(round(TIME_WINDOW_SECONDS * sampling_rate))
    )
    time_window_start = (selected_samples.size - time_sample_count) // 2
    time_window_end = time_window_start + time_sample_count
    stride = max(1, int(np.ceil(time_sample_count / MAX_TIME_POINTS)))

    figure, (time_axis, frequency_axis) = plt.subplots(2, 1, figsize=(12, 8))
    figure.suptitle(
        f"{title} (pasa-banda {FILTER_LOW_HZ}-{FILTER_HIGH_HZ} Hz, notch 60 Hz)",
        fontsize=14,
    )

    time_axis.plot(
        time[time_window_start:time_window_end:stride],
        display_samples[time_window_start:time_window_end:stride],
        linewidth=0.8,
    )
    time_axis.set_title(
        f"Dominio del tiempo ({TIME_WINDOW_SECONDS} s centrales del intervalo; "
        f"suavizado {DISPLAY_SMOOTHING_MS} ms)"
    )
    time_axis.set_xlabel("Tiempo (s)")
    time_axis.set_ylabel(f"Amplitud ({signal_label}, unidad del archivo)")
    time_axis.grid(True, alpha=0.3)

    visible_frequencies = (frequencies >= FILTER_LOW_HZ) & (
        frequencies <= min(MAX_FREQUENCY_HZ, sampling_rate / 2)
    )
    frequency_min = frequencies[visible_frequencies][0]
    frequency_max = min(MAX_FREQUENCY_HZ, sampling_rate / 2)
    for band_name, band_start, band_end, band_color in EEG_BANDS:
        visible_start = max(band_start, frequency_min)
        visible_end = min(band_end, frequency_max)
        if visible_start < visible_end:
            frequency_axis.axvspan(
                visible_start, visible_end, color=band_color, alpha=0.65, zorder=0
            )
            frequency_axis.text(
                (visible_start + visible_end) / 2,
                0.97,
                band_name,
                transform=frequency_axis.get_xaxis_transform(),
                ha="center",
                va="top",
                fontsize=8,
            )
    frequency_axis.semilogy(
        frequencies[visible_frequencies],
        np.maximum(power[visible_frequencies], np.finfo(float).tiny),
        color="#176b63",
        linewidth=0.9,
        zorder=2,
    )
    frequency_axis.set_title(
        "Densidad espectral de potencia (Welch; intervalo completo)"
    )
    frequency_axis.set_xlabel("Frecuencia (Hz)")
    frequency_axis.set_ylabel("Densidad espectral (unidad de amplitud^2/Hz)")
    frequency_axis.set_xlim(frequency_min, frequency_max)
    frequency_axis.grid(True, alpha=0.3)

    figure.tight_layout()
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"{output_stem}.png"
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    duration = selected_samples.size / sampling_rate
    displayed_duration = time_sample_count / sampling_rate
    print(
        f"{title}: PSD de {duration:.2f} s; tiempo muestra {displayed_duration:.2f} s "
        f"({time[time_window_start]:.2f}-{time[time_window_end - 1]:.2f} s) "
        f"-> {output_path}"
    )
    print(
        "Potencia relativa por banda: "
        + ", ".join(f"{name}={value:.1f}%" for name, value in band_power.items())
    )


def find_recording(stem):
    for suffix in ("_converted.txt", ".txt"):
        file_path = DATA_DIR / f"{stem}{suffix}"
        if file_path.exists():
            return file_path
    raise FileNotFoundError(f"No se encontro el registro {stem} en {DATA_DIR}")


def main():
    plot_recording(
        find_recording("EEG_Basal2.0"),
        "EEG - condición basal",
        "EEG_Basal2.0_converted",
    )
    plot_recording(
        find_recording("Abrirycerar_EEG2.0"),
        "EEG - ojos abiertos y cerrados (atención en un punto)",
        "Abrirycerar_EEG2.0_converted",
    )
    plot_recording(
        find_recording("Preguntas2.0_EEG"),
        "EEG - pregunta recibida y reflexionada",
        "Preguntas2.0_EEG_converted",
    )
    music_file = find_recording("musica_eeg2.0")
    plot_recording(
        music_file,
        "EEG - música tranquila (0-58 s)",
        "musica_eeg2.0_converted",
        start_seconds=0,
        end_seconds=58,
    )
    plot_recording(
        music_file,
        "EEG - música movida (58 s hasta el final)",
        "musica_eeg2.0_converted_movida",
        start_seconds=58,
    )


if __name__ == "__main__":
    main()