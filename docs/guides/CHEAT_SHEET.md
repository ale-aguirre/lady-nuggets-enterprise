# 📝 Cheat Sheet: Lady Nuggets Enterprise

Aquí tienes la guía rápida para tu app de notas.

## 1. Generación Masiva (El Motor)
**Script:** `scripts/runpod_ultra.sh`
**Uso:** Generar muchas imágenes de golpe.
```bash
# Generar 5 imágenes (modo normal)
./scripts/runpod_ultra.sh --count 5

# Forzar Lady Nuggets (si tienes el flag activado)
./scripts/runpod_ultra.sh --preset oc-forced --count 5

# Probar estilos (ej: Lencería, Playa, Gym)
./scripts/runpod_ultra.sh --theme "Bedroom (Lingerie)" --count 2
```

## 2. Branding y Logos
**Script:** `scripts/generate_logo.py`
**Uso:** Crear logos vectoriales para redes sociales.
```bash
python3 scripts/generate_logo.py
```
*Las imágenes se guardan en `content/logo_concepts`.*

## 3. El Bot de Discord (Community Manager)
**Script:** `scripts/discord_bot_v2.py`
**Uso:** Encender el bot para que hable y genere en tu servidor.
```bash
python3 scripts/discord_bot_v2.py
```
*Comandos en Discord: `!gen <prompt>`, `!style`, `!help`.*

## 4. Testing Seguro (Sin romper nada)
**Script:** `scripts/test_factory.sh`
**Uso:** Probar configuraciones nuevas antes de usarlas en serio.
```bash
./scripts/test_factory.sh
```
*Crea un entorno seguro, genera 2 imágenes y borra la config de prueba.*

---

### ⚠️ Nota de Seguridad
En tu nota vi que pusiste las API Keys directamente. **Es mejor usar el archivo `.env`**.
Si copias ese bloque en tu RunPod, asegúrate de que nadie más vea tu pantalla o tu historial de comandos si estás en streaming.
