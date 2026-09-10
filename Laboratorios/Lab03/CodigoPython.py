from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


archivo = Path(__file__).with_name("leve_final.txt")
columnas = ["nSeq", "I1", "I2", "O1", "O2", "A1"]

# El formato OpenSignals tiene tres líneas de cabecera y un tabulador final.
df = pd.read_csv(
	archivo,
	sep="\t",
	skiprows=3,
	header=None,
	names=columnas,
	usecols=range(len(columnas)),
)

# nSeq cuenta muestras; la frecuencia del encabezado es 1000 Hz.
df["tiempo"] = df["nSeq"] / 1000

print(df.head())

plt.figure(figsize=(12, 5))
plt.plot(df["tiempo"], df["A1"], label="EMG (A1)")
plt.xlabel("Tiempo (s)")
plt.ylabel("Amplitud")
plt.title("Señal EMG de leve_final.txt")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()

salida = archivo.with_name("leve_final.png")
plt.savefig(salida, dpi=150)
print(f"Gráfica guardada en: {salida}")
plt.show()

