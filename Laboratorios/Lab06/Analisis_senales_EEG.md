# Análisis de las señales del Lab06

El script [analizar_senales_eeg.py](analizar_senales_eeg.py) genera una figura por condición con los 10 segundos centrales del intervalo en el dominio del tiempo y el espectro de frecuencia calculado sobre el intervalo completo. Aplica un filtro Butterworth pasa-banda de octavo orden y fase cero entre 0.3-48 Hz, más un notch de 60 Hz para reducir la interferencia de red. La traza temporal se suaviza 25 ms solo para visualizarla; el espectro y los porcentajes de potencia por banda se calculan con la señal filtrada completa antes de ese suavizado. Las bandas dentro del rango EEG se marcan en la gráfica. Las imágenes se guardan en `Graficas_EEG/`.

Para ejecutar el análisis desde la raíz del repositorio:

```bash
py -m pip install -r Laboratorios/Lab06/requirements.txt
py Laboratorios/Lab06/analizar_senales_eeg.py
```

Se analizan las versiones `_converted.txt` para evitar graficar dos veces cada registro junto con su archivo original. El encabezado indica una frecuencia de muestreo de 1000 Hz y una columna de señal `A3`.

## Condiciones del experimento

Las gráficas siguen el orden de las cinco condiciones indicadas: basal, ojos abiertos/cerrados, reflexión sobre una pregunta, música tranquila y música movida. La vista temporal muestra los 10 segundos centrales de cada intervalo; el PSD usa todo el registro, o el segmento musical completo correspondiente. Los dos tipos de música se separaron en el segundo 58 del archivo disponible.

### 1. Basal

Registro basal descrito en el informe como una condición de descanso. La gráfica permite observar la variación de la señal durante esta condición.

![Señal basal en tiempo y frecuencia](Graficas_EEG/EEG_Basal2.0_converted.png)

### 2. Ojos abiertos y cerrados

Durante esta condición se alternó entre abrir y cerrar los ojos para concentrarse en un punto. La infografía plantea como expectativa que la actividad alfa (8-12 Hz) pueda ser mayor con los ojos cerrados y atenuarse al abrirlos; debe comprobarse en estos datos y no asumirse de antemano.

![Señal con ojos abiertos y cerrados en tiempo y frecuencia](Graficas_EEG/Abrirycerar_EEG2.0_converted.png)

### 3. Pregunta reflexionada

Registro recibido mientras la persona pensaba la respuesta. La infografía propone que una tarea mental podría reflejarse en actividad beta (12-25 Hz); esta es una hipótesis de comparación, no una conclusión automática de la gráfica.

![Señal durante la pregunta en tiempo y frecuencia](Graficas_EEG/Preguntas2.0_EEG_converted.png)

### 4. Música tranquila

Primeros 58 segundos del registro de música.

![Señal durante música tranquila en tiempo y frecuencia](Graficas_EEG/musica_eeg2.0_converted.png)

### 5. Música movida

Desde el segundo 58 hasta el final del mismo registro de música.

![Señal durante música movida en tiempo y frecuencia](Graficas_EEG/musica_eeg2.0_converted_movida.png)

## Comparación con la teoría

La siguiente tabla muestra la potencia relativa integrada en cada banda, como porcentaje de la potencia total entre 0.3 y 48 Hz. Se calculó sobre cada intervalo completo ya filtrado; en música se usan los segmentos 0-58 s y 58 s hasta el final, no solo los 10 segundos centrales mostrados en el panel temporal.

| Condición | Delta | Theta | Alfa | Beta | Gamma |
|---|---:|---:|---:|---:|---:|
| Basal | 95.3% | 1.8% | 0.9% | 1.1% | 0.5% |
| Ojos abiertos/cerrados | 90.7% | 3.0% | 1.2% | 2.2% | 2.3% |
| Pregunta reflexionada | 85.0% | 3.9% | 2.2% | 4.1% | 3.9% |
| Música tranquila | 71.5% | 12.2% | 4.9% | 6.3% | 3.4% |
| Música movida | 75.0% | 8.5% | 4.3% | 6.4% | 4.0% |

El aumento relativo de beta durante la pregunta (4.1% frente a 1.1% basal) va en la dirección que propone la infografía para una tarea mental, pero no basta para confirmar causalidad. La proporción alfa en el registro de ojos abiertos/cerrados es 1.2% frente a 0.9% basal; como el archivo mezcla ambas fases y no tiene marcas temporales que las separen, no permite probar que alfa aumente con los ojos cerrados. Las proporciones de alfa y beta son parecidas entre música tranquila y movida. En las cinco condiciones domina delta y el máximo espectral está cerca de 0.49 Hz, lo que también puede reflejar deriva o artefactos de baja frecuencia.

**Conclusión:** los datos solo coinciden parcialmente con las expectativas teóricas; no las confirman de forma concluyente. Las diferencias son descriptivas, no una prueba estadística, y deben interpretarse con cautela por los artefactos y la identificación del sensor/canal en los metadatos.

## Bandas de referencia

La infografía presenta estas bandas para orientar el análisis: delta (0-4 Hz), theta (4-8 Hz), alfa (8-12 Hz), beta (12-25 Hz) y gamma (>25 Hz). Se sombrean en el espectro para facilitar la comparación. Como el filtro corta en 48 Hz, solo se muestra la parte de gamma entre 25 y 48 Hz.

La referencia también advierte sobre artefactos por parpadeos y movimiento ocular, tensión de mandíbula/cuello, movimiento de cables e interferencia eléctrica de 50/60 Hz. En la señal cruda se observó un pico cerca de 60 Hz y excursiones abruptas que alcanzan aproximadamente +/-1.5 unidades; podrían deberse a interferencia, movimiento o saturación y no deben atribuirse directamente a actividad cerebral. El pasa-banda y el notch reducen la interferencia de 60 Hz; el espectro mostrado se limita además a 0.3-48 Hz. El filtrado no corrige artefactos de movimiento ni saturación.

## Alcance de la interpretación

Los metadatos de OpenSignals identifican el sensor como `ECGBIT` y el canal como `A3`; los archivos tampoco especifican una unidad física. Aunque el informe y la infografía describen el laboratorio como EEG, las gráficas representan los valores guardados y no deben interpretarse como amplitudes calibradas en microvoltios. Las bandas coloreadas son referencias: para afirmar que una condición modificó una banda habría que comparar potencia por banda con una señal EEG validada y controlar los artefactos.