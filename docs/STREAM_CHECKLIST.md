# Stream Checklist — The Hobbit Journey

**Stream target:** 26 de abril (o la fecha que elijas)  
**Duration:** ~7h 30m (full audiobook) or partial  
**URL:** `http://localhost:5000/book`

---

## ✅ Requisitos Previos

- [ ] **OBS Studio** instalado (https://obsproject.com/)
- [ ] **Cuenta de YouTube** con streaming habilitado (o Twitch)
- [ ] **Navegador Chrome/Edge/Firefox** actualizado
- [ ] **Python 3** instalado en la máquina que hará el stream
- [ ] **Conexión estable** (mínimo 5 Mbps de upload para 1080p)

---

## 🚀 Día del Stream — Pasos

### 1. Iniciar el Servidor (Terminal)

```bash
cd /home/didi/code/hobbit
./start_server.sh
```

Deberías ver algo como:
```
[Generative] Content generator started
[Server] Generative content engine initialized
 * Running on http://127.0.0.1:5000
```

> ⚠️ **No cierres esta terminal.** El servidor debe quedar corriendo. Si se cierra, el stream se congela.

---

### 2. Abrir el Stream Client (Navegador)

1. Abre tu navegador
2. Ve a: **`http://localhost:5000/book`**
3. Espera a que cargue (aparece "Loading Middle-earth...")
4. Verás el overlay **"The Hobbit: An Unexpected Journey — Click anywhere to begin"**
5. **Haz clic** en el overlay o en el botón **"BEGIN JOURNEY"**
6. El audio empezará y el stream avanzará solo

> 💡 **Tip:** Abre el navegador en una ventana dedicada, sin otras pestañas. Ponlo en **pantalla completa** (F11).

---

### 3. Configurar OBS

#### Fuente de Pantalla/Ventana
1. En OBS, haz clic en **+** en Fuentes
2. Elige **"Captura de ventana"** (Window Capture) o **"Captura de pantalla"** (Display Capture)
3. Selecciona la ventana del navegador con `stream_book.html`
4. Ajusta el tamaño a **1920x1080** (o la resolución de tu stream)

#### Audio
1. En **Mezclador de audio**, asegúrate de capturar el audio del **navegador**
   - Si usas **Display Capture**, capturará todo el audio del escritorio
   - Si usas **Window Capture**, puede que necesites agregar una fuente de audio separada: **"Audio de entrada de aplicación"** (Application Audio Capture) y seleccionar el navegador
2. Ajusta el volumen para que no distorsione (mantén el pico por debajo de -3 dB)

#### Overlay opcional (cámara/webcam)
Si querés mostrar tu cara o comentar:
1. Agregá una fuente **"Dispositivo de captura de vídeo"** (Video Capture Device)
2. Posicionala en una esquina (esquina inferior derecha recomendada)
3. Agregá un borde o sombra para que no se confunda con el fondo

---

### 4. Conectar a YouTube/Twitch

#### YouTube
1. En YouTube Studio, andá a **"Crear" → "Transmitir en directo"**
2. Copiá la **URL del servidor de transmisión** y la **Clave de retransmisión**
3. En OBS, andá a **Ajustes → Transmisión**
4. Servicio: **YouTube / YouTube - RTMPS**
5. Pegá la clave de retransmisión
6. Dale a **"Iniciar transmisión"**

#### Twitch
1. En Twitch Creator Dashboard, andá a **Settings → Stream**
2. Copiá la **Primary Stream key**
3. En OBS, andá a **Ajustes → Transmision**
4. Servicio: **Twitch**
5. Pegá la clave
6. Dale a **"Iniciar transmisión"**

---

### 5. Durante el Stream

El stream es **100% automático** una vez iniciado:
- Avanza de escena sola
- Reproduce audio TTS en escenas canónicas
- Muestra texto generado en gaps (sin audio)
- El timeline se actualiza solo

**Si necesitás pausar:**
- Podés hacer clic en el botón **PAUSE** del stream client
- O pausar la transmisión desde OBS

**Atajos de teclado del stream client:**
- `Espacio` — Play/Pause
- `→` — Siguiente escena
- `←` — Escena anterior

---

## 🧪 Prueba de Fuego (Recomendado hacer antes del 26)

Hacé una prueba de 30-60 minutos:

```bash
# 1. Iniciar servidor
./start_server.sh

# 2. Abrir http://localhost:5000/book en navegador
# 3. Hacer clic en BEGIN JOURNEY
# 4. En OBS, iniciar transmisión de prueba (puede ser privada en YouTube)
# 5. Dejar corriendo 30 minutos y verificar:
#    - ¿El audio se escucha bien?
#    - ¿Las escenas avanzan solas?
#    - ¿No hay lag en OBS?
#    - ¿El stream no se corta?
```

---

## ⚠️ Troubleshooting

| Problema | Solución |
|----------|----------|
| "Loading Middle-earth..." no desaparece | Recargá la página (F5). Si persiste, revisá que el servidor esté corriendo en la terminal. |
| No se escucha audio | Asegurate de haber hecho **clic en el overlay** al inicio. Los navegadores bloquean autoplay hasta la primera interacción. Verificá el volumen del navegador y de OBS. |
| OBS no captura el navegador | Probá con **Display Capture** en lugar de Window Capture. O usá **Browser Source** apuntando a `http://localhost:5000/book` (tamaño 1920x1080). |
| El servidor se murió | Reinicialo con `./start_server.sh`. El stream client se reconectará al recargar. |
| Las escenas no avanzan | Verificá que aparezca el botón "PAUSE" (significa que está en play). Si está en "PLAY", hacé clic. |
| Audio se corta al cambiar de capítulo | Es normal. Cada capítulo tiene su archivo de audio. El nuevo capítulo empezará automáticamente. |
| El stream se ve lento/lag | Bajá la resolución de salida en OBS a 720p. O cerrá otras aplicaciones. |

---

## 📊 Datos Útiles

| Dato | Valor |
|------|-------|
| Escenas totales | 170 (96 canónicas + 74 generadas) |
| Audio total | ~7h 30m |
| Capítulos con audio | 19 (todos) |
| Duración típica por escena | 20-50 minutos (factor 0.2) |
| Gaps generados | 74 (sin audio, solo texto) |

---

## 🎨 Personalización Rápida

### Cambiar el pacing (velocidad)
En `data/stream_config.json`, modificá:
```json
{
  "pacing": {"value": 0.2}
}
```
- **0.1** = más lento (escenas duran el doble)
- **0.5** = más rápido (escenas duran la mitad)
- **1.0** = tiempo real (muy rápido, ~3h de stream total)

> Requiere reiniciar el servidor después de cambiar.

### Cambiar la escena inicial
Hacé clic en cualquier marcador del timeline en la parte inferior del stream client, o usá los atajos de teclado.

---

## 🔒 Notas Importantes

1. **No cierres el navegador ni la terminal del servidor** durante el stream.
2. **Desactivá el salvapantallas** y el **apagado automático** de tu computadora.
3. **Desactivá notificaciones** del sistema operativo.
4. Si usás **WiFi**, conectate por **cable Ethernet** para mayor estabilidad.
5. El servidor Flask está diseñado para durar muchas horas, pero si tu máquina se apaga o reinicia, perdés el stream.

---

**¡Buena suerte en el stream!** 🧙‍♂️🍃
