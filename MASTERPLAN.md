# 🎯 MASTERPLAN v1.0 — Lady Nuggets Enterprise

> Unifica: `PLAN_ESTRATEGICO_CLAUDE.md` + `PLAN_NEGOCIO_AUTOMATIZADO.md` + investigación de mercado real.

---

## La verdad sobre este negocio

### ¿Sirve? Datos reales, no suposiciones.

| Dato | Fuente | Relevancia |
|------|--------|------------|
| "My AI Waifu" gana **$585-2000/mes** con 276 subs | Graphtreon | Prueba que AI waifu x Patreon funciona |
| Creator en Fanvue gana **$1100/mes** con 60 subs a $10 | Reddit (verificado) | 60 personas pagando = $1000 |
| Mercado AI Art crece a **$8.6 billion para 2033** | GodOfPrompt research | El mercado está en expansión |
| Promedio Patreon: **$52/fan/año** | Hypebot 2025 | Tu meta: 230 fans pagando = $1000/mes |

### ¿Cambiaría este negocio? No.

Con 5.9K watchers en DA y tráfico US, ya tenés más audiencia base que la mayoría de los que logran $1000/mes. **El problema nunca fue la audiencia — fue la consistencia de publicación.**

---

## Estrategia: SFW+Ecchi público → NSFW privado

### Por qué este modelo y no otro

```
┌────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  PÚBLICO       │    │  MEDIO           │    │  PRIVADO         │
│  (gratis)      │ ──>│  (Discord free)  │ ──>│  (pago)          │
│                │    │                  │    │                  │
│  DA / Twitter  │    │  Ecchi + Preview  │    │  Patreon / Fanvue│
│  SFW + Ecchi   │    │  Comunidad        │    │  NSFW + Hires    │
│  Watermark     │    │  Votaciones       │    │  Sin watermark   │
│  Baja res      │    │  Packs gratis     │    │  Packs exclusivos│
└────────────────┘    └──────────────────┘    └──────────────────┘
     5.9K DA               51 Discord            Meta: 100 subs
```

**Regla de oro:** Lo que se ve gratis genera deseo. Lo que se paga genera ingresos.

### Plataformas (investigado)

| Plataforma | Uso | AI NSFW? | Comisión |
|------------|-----|----------|----------|
| **Patreon** | Suscripciones principales | ✅ Anime/ilustrado OK | 5-12% |
| **Fanvue** | Segundo ingreso NSFW | ✅ Explícitamente permite AI | 15-20% |
| **SubscribeStar** | Backup anti-ban | ✅ Sin restricciones | 10% |
| DeviantArt | Tráfico gratuito (embudo) | ⚠️ Solo SFW/Ecchi | Gratis |
| Twitter/X | Viralidad + alcance | ⚠️ Ecchi OK, NSFW limitado | Gratis |
| ~~Gumroad~~ | ❌ **YA NO SIRVE** | ❌ Prohibió NSFW | — |

---

## Tiers de monetización

### Patreon (cuenta Adult/18+)

| Tier | Precio | Qué incluye | Meta subs |
|------|--------|-------------|-----------|
| **Nugget Fan** | $5 USD | Pack semanal HD sin watermark (8-10 img), acceso Discord VIP | 100 |
| **Gold Nugget** | $15 USD | Todo lo anterior + NSFW exclusivo + votación de temas | 30 |
| **Diamond** | $30 USD | Todo + custom requests (1 por mes, tu OC o cualquier personaje) | 10 |

### Proyección realista (mes 3-4)

```
100 × $5  = $500
 30 × $15 = $450
 10 × $30 = $300
─────────────────
TOTAL     = $1,250/mes
Menos Patreon (8%) = $1,150/mes neto
Menos RunPod (~$15/mes) = $1,135/mes
```

---

## Las 4 fases de implementación

### FASE 0: Pipeline funcional (AHORA — esta semana)
> Ya estamos en esto. Que el script no crashee.

- [x] Fix WAI download (versionId correcto)
- [x] Fix Forge SD_DIR detection
- [x] Fix port retry (90s wait)
- [ ] **Verificar 1 batch exitoso de 10 imágenes**
- [ ] Confirmar calidad visual aceptable

### FASE 1: Contenido automático (Semana 2)
> Sin contenido constante, no hay negocio. Los 3 subs se fueron por esto.

**Scripts a construir:**

1. **`curator.py`** — Filtro de calidad automático
   - Envía cada imagen generada a Gemini Vision / GPT-4o
   - Evalúa: anatomía, estética, composición (1-10)
   - Solo las ≥7 pasan a publicación
   - Las ≥9 se marcan "Premium" (exclusivas Patreon)

2. **`social_poster.py`** — Publicación automática diaria
   - DA: Post diario SFW/Ecchi + tags + link Patreon
   - Twitter/X: 2-3 posts diarios con preview + CTA
   - Formato: imagen + caption generado por LLM

3. **`watermark.py`** — Protección de contenido
   - Versión gratis: 720p + watermark sutil
   - Versión Patreon: Full HD sin watermark

**Meta:** 3-5 imágenes publicadas diarias, 100% automático.

### FASE 2: Comunidad (Semana 3-4)
> Discord es retención. Sin retención, los subs se van.

1. **Bot Discord** — Daily Waifu + votaciones
   - Cada mañana postea una imagen curada en #general
   - Los miembros votan el tema del próximo batch (poll)
   - Canal #nsfw-preview para subs $15+ (verificado por rol)

2. **Welcome Flow** — Onboarding automático
   - DM de bienvenida con guía y link Patreon
   - Auto-asignar roles según tier de Patreon

3. **Canal #requests** — Solo tier Diamond
   - El usuario pide un personaje/escena
   - Tu pipeline lo genera con --random-char o custom LoRA
   - Entrega en 24h

### FASE 3: Escalar (Mes 2-3)
> Más plataformas, más ingresos, menos trabajo.

1. **Fanvue** — Segundo canal NSFW (para contenido que Patreon no permite)
2. **Packs temáticos** — Colecciones mensuales (Valentine, Halloween, Summer)
3. **Training LoRAs custom** — $50-100 por personaje custom
4. **Cross-posting** — Pixiv, Rule34, Danbooru (tráfico pasivo gratis)

---

## Por qué VA a funcionar (y por qué antes no)

### Lo que salió mal
| Problema | Causa | Solución |
|----------|-------|----------|
| 3 subs se fueron | No había contenido nuevo | Auto-posting diario |
| Publicación inconsistente | Era manual, daba burnout | `social_poster.py` lo hace solo |
| Calidad irregular | No había filtro | `curator.py` descarta las malas |
| Solo Lady Nuggets | Monotemático | `--random-char` = 15+ personajes |
| No había funnel | DA → nada | DA(SFW) → Discord(preview) → Patreon(HD+NSFW) |

### Lo que es diferente ahora
1. **Pipeline automatizado** — generar es gratis (costo: ~$0.50/hr RunPod)
2. **Variedad** — 20 temas × 15 personajes × 6 artist mixes = **1,800 combinaciones únicas**
3. **Funnel claro** — cada plataforma tiene un rol definido
4. **Consistencia forzada** — el bot publica sin importar si vos tenés ganas o no

---

## Costos reales

| Concepto | Costo mensual |
|----------|---------------|
| RunPod RTX 4090 (~2 sesiones de 3hrs) | ~$15 USD |
| APIs (Groq + OpenRouter free tier) | $0 |
| Patreon comisión (8%) | Variable |
| CivitAI (modelos) | $0 (gratis) |
| **Total fijo** | **~$15/mes** |

**ROI:** Con 20 subs a $5 = $100 - $15 = **$85 de ganancia** solo para cubrir costos.
Con la meta de 140 subs mixtos = **$1,135 neto**.

---

## Siguiente paso inmediato

1. ✅ Verificar que el pipeline funcione (git pull + test en RunPod)
2. 🔲 Generar batch de prueba de 10 imágenes
3. 🔲 Construir `curator.py`
4. 🔲 Construir `social_poster.py`
5. 🔲 Configurar Patreon tiers
6. 🔲 Activar posting diario automático

**¿Aprobás este plan para empezar a construir?**
