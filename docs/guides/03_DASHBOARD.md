# 📊 Guía 03: Dashboard Web

> **Objetivo:** Interfaz web para ver, filtrar, aprobar imágenes y ajustar parámetros desde el browser.
> **Prioridad:** #3 - Control visual sin necesidad de terminal
> **Stack:** Next.js + Tailwind CSS + Lucide Icons (dark mode)

---

## Problema Actual

Para ver las imágenes generadas hay que:
1. Conectarse por terminal a RunPod
2. Descargar el ZIP
3. Descomprimir y revisar una por una

---

## Funcionalidades

### MVP (Fase 1)
1. **Galería** - Grid de imágenes generadas con thumbnails
2. **Detalle** - Click en imagen → ver full size + prompt + score + metadata
3. **Filtros** - Por score, tema, estilo, fecha
4. **Acciones** - Aprobar / Rechazar / Marcar premium
5. **Config** - Ajustar parámetros de generación (steps, CFG, resolución)

### Fase 2
6. **Generación en vivo** - Botón "Generar" que dispara el pipeline desde el browser
7. **Progreso** - Ver estado en tiempo real (generando, evaluando, empaquetando)
8. **Export** - Descargar packs aprobados como ZIP

### Fase 3
9. **Analytics** - Temas con mejor score, tendencias, producción diaria
10. **Programación** - Agendar generaciones automáticas

---

## Estructura del Proyecto

```
web/
├── package.json
├── next.config.js
├── tailwind.config.js
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Dark mode layout base
│   │   ├── page.tsx            # Dashboard principal
│   │   ├── gallery/
│   │   │   └── page.tsx        # Galería de imágenes
│   │   ├── generate/
│   │   │   └── page.tsx        # Panel de generación
│   │   └── api/
│   │       ├── images/
│   │       │   └── route.ts    # API: listar imágenes
│   │       ├── generate/
│   │       │   └── route.ts    # API: iniciar generación
│   │       └── approve/
│   │           └── route.ts    # API: aprobar/rechazar
│   ├── components/
│   │   ├── Sidebar.tsx         # Navegación lateral
│   │   ├── ImageCard.tsx       # Card de imagen en grid
│   │   ├── ImageModal.tsx      # Modal fullscreen
│   │   ├── ScoreBadge.tsx      # Badge de score con color
│   │   ├── FilterBar.tsx       # Barra de filtros
│   │   ├── GenerationPanel.tsx # Panel de configuración
│   │   └── StatsCard.tsx       # Card de estadísticas
│   └── lib/
│       ├── api.ts              # Funciones API client
│       └── types.ts            # TypeScript types
```

---

## Backend API

El dashboard necesita un backend API que se conecte al filesystem de imágenes.

### Endpoints:

```typescript
// GET /api/images?batch=latest&status=approved&min_score=7
// Retorna lista de imágenes con metadata

// POST /api/generate
// Body: { count: 10, theme: "Cyberpunk", style: "manhwa" }
// Inicia pipeline en background

// POST /api/approve
// Body: { image_id: "xxx", action: "approve" | "reject" | "premium" }
// Mueve imagen entre directorios

// GET /api/stats
// Retorna estadísticas de producción
```

### Estructura de datos:

```typescript
interface GeneratedImage {
  id: string;
  filename: string;
  path: string;
  thumbnail: string;       // Ruta a thumbnail 300px
  prompt: string;
  negative_prompt: string;
  theme: string;
  style: string;
  score: number | null;    // null si no evaluado
  status: 'pending' | 'approved' | 'rejected' | 'premium';
  created_at: string;
  batch_id: string;
  metadata: {
    model: string;
    steps: number;
    cfg: number;
    sampler: string;
    seed: number;
    width: number;
    height: number;
  };
}
```

---

## Diseño UI

### Estética
- **Dark mode** obligatorio (background: #0a0a0a)
- Glassmorphism en cards (backdrop-blur)
- Gradientes sutiles purple → blue (brand colors)
- Animaciones hover suaves
- Grid responsive (4 cols desktop, 2 mobile)

### Paleta de colores
```css
--bg-primary: #0a0a0a;
--bg-card: rgba(255,255,255,0.05);
--accent-purple: #8b5cf6;
--accent-blue: #3b82f6;
--success: #22c55e;
--warning: #eab308;
--danger: #ef4444;
--text-primary: #f5f5f5;
--text-secondary: #a3a3a3;
```

### Score Badge colores
- Score 9-10: Dorado (premium) ⭐
- Score 7-8: Verde (aprobado) ✅
- Score 5-6: Amarillo (regular) ⚠️
- Score <5: Rojo (rechazado) ❌

---

## Setup Inicial

```bash
cd web/
npx -y create-next-app@latest ./ --typescript --tailwind --eslint --app --src-dir --no-import-alias
npm install lucide-react
```

---

## Conexión con Pipeline

El dashboard corre **localmente** (en la Mac de Alexis) y se conecta al pod de RunPod via:
- **Opción A:** API proxy via RunPod's public URL
- **Opción B:** SSH tunnel al pod
- **Opción C:** Dashboard corre EN el pod (más simple para MVP)

**Recomendación MVP:** Correrlo en el pod con `npm run dev -- -p 3000` y acceder via RunPod proxy.

---

## Verificación

1. `npm run dev` arranca sin errores
2. Galería muestra imágenes de `/content/` 
3. Filtros funcionan (por score, tema, fecha)
4. Click en imagen abre modal fullscreen
5. Botón aprobar/rechazar mueve archivos
6. Dark mode se ve premium

---

## Notas para el Agente

- **SIEMPRE dark mode** - es preferencia del owner
- Usar Lucide Icons (no Heroicons, no FontAwesome)
- Tailwind CSS (configurado por el owner como preferencia)
- El dashboard es para USO PERSONAL, no público. No necesita auth.
- Las imágenes pueden ser NSFW - no agregar filtros de contenido
- Priorizar funcionalidad sobre estética perfecta en MVP
- El filesystem de imágenes está en `content/` relativo al root del proyecto
