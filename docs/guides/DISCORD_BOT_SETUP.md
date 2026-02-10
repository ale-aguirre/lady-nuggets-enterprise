# 🤖 Guía: Cómo crear e "Instalar" tu Bot de Discord

No tienes que instalar nada en tu PC, solo en el Developer Portal.

## Paso 1: Crear la "Identidad" del Bot
1. Ve a [Discord Developer Portal](https://discord.com/developers/applications).
2. Click en **"New Application"** (arriba a la derecha).
3. Nombre: **"Lady Nuggets Manager"** (o lo que quieras).
4. Ve a la pestaña **"Bot"** (menú izquierdo).
5. Dale a **"Reset Token"** -> **COPIA ESTE CÓDIGO**.
   *   🔴 **IMPORTANTE**: Pégalo en tu archivo `config/.env` donde dice `DISCORD_TOKEN=...`
6. Bja un poco y activa estas casillas ("Privileged Gateway Intents"):
   *   ✅ **Presence Intent**
   *   ✅ **Server Members Intent**
   *   ✅ **Message Content Intent**
   *   *(Dale a Save Changes)*

## Paso 2: Invitar al Bot a tu Servidor
1. Ve a la pestaña **"OAuth2"** -> **"URL Generator"**.
2. En "Scopes", marca: `bot` y `applications.commands`.
3. En "Bot Permissions", marca: `Administrator` (para no liarnos con permisos ahora).
4. Copia la URL que se generó abajo ("Generated URL").
5. Pégala en tu navegador, selecciona tu servidor de Discord y dale a "Autorizar".

## Paso 3: Encender el Cerebro
Ahora que el "cuerpo" está en el servidor, necesitas conectar el "cerebro" (el script).

1. Abre tu terminal en la carpeta del proyecto.
2. Asegúrate de tener las librerías: `pip install discord.py python-dotenv websocket-client`
3. Ejecuta:
   ```bash
   python scripts/discord_bot_v2.py
   ```
4. Si sale "✨ Lady Nuggets Orchestrator Online", ¡ya está vivo! Ve a Discord y escribe `!gen hola`.
