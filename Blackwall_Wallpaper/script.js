/* === Blackwall HUD + Voxel Engine (Lines + Background) === */
let bridge;
let mouseX = 0, mouseY = 0;
let targetMouseX = 0, targetMouseY = 0;

window.addEventListener('mousemove', (e) => {
    targetMouseX = (e.clientX - window.innerWidth / 2) / (window.innerWidth / 2);
    targetMouseY = (e.clientY - window.innerHeight / 2) / (window.innerHeight / 2);
});

function updateClock() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    document.getElementById('hud-time').innerText = `${h}:${m}:${s}`;

    const dias = ['DOM', 'SEG', 'TER', 'QUA', 'QUI', 'SEX', 'S\u00c1B'];
    const meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'];
    document.getElementById('hud-date').innerText =
        `${dias[now.getDay()]}, ${String(now.getDate()).padStart(2, '0')} ${meses[now.getMonth()]} ${now.getFullYear()}`;
}
setInterval(updateClock, 1000);
updateClock();

let imagePaths = [];
let currentImageIndex = 0;

document.addEventListener("DOMContentLoaded", function () {
    if (typeof QWebChannel !== "undefined") {
        new QWebChannel(qt.webChannelTransport, function (channel) {
            bridge = channel.objects.bridge;
            setInterval(updateStats, 1000);

            if (bridge.getImagesList) {
                bridge.getImagesList(function (res) {
                    try {
                        imagePaths = JSON.parse(res);
                        if (imagePaths.length > 0) loadNextImage();
                    } catch (e) {}
                });
            }
        });
    } else {
        imagePaths = ['images/joi1.png'];
        loadNextImage();
    }
});

function updateStats() {
    if (!bridge) return;
    bridge.getSystemStats(function (response) {
        try {
            const stats = JSON.parse(response);
            document.getElementById('cpu-bar').style.width = Math.round(stats.cpu) + '%';
            document.getElementById('cpu-val').innerText = Math.round(stats.cpu) + '%';
            document.getElementById('ram-bar').style.width = Math.round(stats.ram) + '%';
            document.getElementById('ram-val').innerText = Math.round(stats.ram) + '%';

            if (stats.title && stats.title !== "AGUARDANDO M\u00cdDIA...") {
                document.getElementById('track-title').innerText = stats.title;
                document.getElementById('track-artist').innerText =
                    (stats.artist || '').toUpperCase();
            } else {
                document.getElementById('track-title').innerText = "AGUARDANDO M\u00cdDIA...";
                document.getElementById('track-artist').innerText = "SYSTEM_STANDBY";
            }

            const wave = document.getElementById('audio-wave');
            if (wave) {
                if (stats.playing) wave.classList.add('playing');
                else wave.classList.remove('playing');
            }

            if (typeof stats.beat === 'number' && stats.beat > 0) {
                const icon = document.querySelector('.album-icon');
                if (icon) {
                    const b = Math.min(1, stats.beat * 2);
                    const g = 10 + b * 22;
                    const a = 0.4 + b * 0.45;
                    icon.style.boxShadow = `0 0 ${g}px rgba(255, 0, 60, ${a})`;
                }
            }
        } catch (e) {}
    });
}

/* ==============================================================
   MOTOR DE LINHAS + BACKGROUND BLACKWALL
   ============================================================== */

const canvas = document.getElementById('voxel-canvas');
const ctx = canvas.getContext('2d');

// -------- Densidade / escala das linhas --------
const DENSITY_LEVELS = [180, 260, 380, 520, 680];
const REFERENCE_DIM = 380;
let densityIndex = 2;
let MAX_DIM = DENSITY_LEVELS[densityIndex];

const FIT_PERCENT = 1.0;
const FILL_MODE = 'contain';

const LINE_WIDTH_AT_REF = 0.22;
const LINE_HEIGHT_MIN_AT_REF = 1.0;
const LINE_HEIGHT_RANGE_AT_REF = 2.8;
const LINE_PULSE_AMP = 0.18;
const LINE_TOP_GLOW = 0.85;

const Z_RADIAL_FACTOR = 0.08;
const MOUSE_PARALLAX_PX = 15;
const BRIGHTNESS_THRESHOLD = 4;

// -------- BACKGROUND --------
// Grid vertical
const BG_GRID_SPACING = 4;            // px entre linhas verticais
const BG_GRID_ALPHA = 0.055;          // opacidade
// Grid horizontal
const BG_GRID_H_SPACING = 40;         // px entre linhas horizontais
const BG_GRID_H_ALPHA = 0.035;
// Atmosfera
const BG_BOTTOM_GLOW = 0.30;          // nevoa vermelha embaixo (0..1)
const BG_TOP_FADE = 0.50;             // escurecimento do topo (0..1)

// -------- CHUVA DIGITAL --------
const RAIN_DENSITY = 40;              // 1 gota a cada N px de largura
const RAIN_SPEED_MIN = 40;
const RAIN_SPEED_MAX = 160;
const RAIN_ALPHA_MIN = 0.08;
const RAIN_ALPHA_MAX = 0.30;

// -------- SCANLINE --------
const SCANLINE_SPEED = 80;            // px/s
const SCANLINE_ALPHA = 0.10;
const SCANLINE_HEIGHT = 120;

// -------- GLITCH --------
const GLITCH_PROBABILITY = 0.02;      // por frame

// -------- Estado --------
let projMultiplier = 1.0;
let lineWidth = LINE_WIDTH_AT_REF;
let lineHeightMin = LINE_HEIGHT_MIN_AT_REF;
let lineHeightRange = LINE_HEIGHT_RANGE_AT_REF;
let currentImageDims = null;

let bgTexture = null;
const rainDrops = [];

function recomputeScales() {
    const ratio = REFERENCE_DIM / MAX_DIM;
    lineWidth       = LINE_WIDTH_AT_REF        * ratio;
    lineHeightMin   = LINE_HEIGHT_MIN_AT_REF   * ratio;
    lineHeightRange = LINE_HEIGHT_RANGE_AT_REF * ratio;

    if (!currentImageDims) {
        projMultiplier = Math.min(canvas.width, canvas.height) * FIT_PERCENT / MAX_DIM;
        return;
    }
    const { sW, sH } = currentImageDims;
    const scaleX = (canvas.width  * FIT_PERCENT) / sW;
    const scaleY = (canvas.height * FIT_PERCENT) / sH;
    projMultiplier = (FILL_MODE === 'cover')
        ? Math.max(scaleX, scaleY)
        : Math.min(scaleX, scaleY);
}

function rebuildBackgroundTexture() {
    bgTexture = document.createElement('canvas');
    bgTexture.width = canvas.width;
    bgTexture.height = canvas.height;
    const bctx = bgTexture.getContext('2d');

    // Base
    bctx.fillStyle = '#010204';
    bctx.fillRect(0, 0, bgTexture.width, bgTexture.height);

    // Grid vertical principal
    bctx.fillStyle = `rgba(200, 0, 60, ${BG_GRID_ALPHA})`;
    for (let x = 0; x < bgTexture.width; x += BG_GRID_SPACING) {
        bctx.fillRect(x, 0, 1, bgTexture.height);
    }

    // Grid vertical secundario (offset, mais sutil)
    bctx.fillStyle = `rgba(255, 0, 60, ${BG_GRID_ALPHA * 0.5})`;
    for (let x = 2; x < bgTexture.width; x += BG_GRID_SPACING * 2) {
        bctx.fillRect(x, 0, 1, bgTexture.height);
    }

    // Grid horizontal
    bctx.fillStyle = `rgba(200, 0, 60, ${BG_GRID_H_ALPHA})`;
    for (let y = 0; y < bgTexture.height; y += BG_GRID_H_SPACING) {
        bctx.fillRect(0, y, bgTexture.width, 1);
    }

    // Atmosfera embaixo
    if (BG_BOTTOM_GLOW > 0) {
        const bottomGrad = bctx.createLinearGradient(
            0, bgTexture.height * 0.5, 0, bgTexture.height
        );
        bottomGrad.addColorStop(0, 'rgba(0, 0, 0, 0)');
        bottomGrad.addColorStop(1, `rgba(100, 0, 40, ${BG_BOTTOM_GLOW})`);
        bctx.fillStyle = bottomGrad;
        bctx.fillRect(0, bgTexture.height * 0.5, bgTexture.width, bgTexture.height * 0.5);
    }

    // Escurecimento no topo
    if (BG_TOP_FADE > 0) {
        const topGrad = bctx.createLinearGradient(0, 0, 0, bgTexture.height * 0.3);
        topGrad.addColorStop(0, `rgba(0, 0, 0, ${BG_TOP_FADE})`);
        topGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        bctx.fillStyle = topGrad;
        bctx.fillRect(0, 0, bgTexture.width, bgTexture.height * 0.3);
    }
}

function initRain() {
    rainDrops.length = 0;
    const count = Math.floor(canvas.width / RAIN_DENSITY);
    for (let i = 0; i < count; i++) {
        rainDrops.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            speed: RAIN_SPEED_MIN + Math.random() * (RAIN_SPEED_MAX - RAIN_SPEED_MIN),
            length: 30 + Math.random() * 80,
            alpha: RAIN_ALPHA_MIN + Math.random() * (RAIN_ALPHA_MAX - RAIN_ALPHA_MIN),
        });
    }
}

function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    recomputeScales();
    rebuildBackgroundTexture();
    initRain();
}
window.addEventListener('resize', resize);
resize();

let voxels = [];
let isImageLoaded = false;
let currentPath = null;

function _loadImageAt(path) {
    const img = new Image();
    img.src = path;
    img.onload = () => {
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');

        let sW = MAX_DIM;
        let sH = Math.round(MAX_DIM * (img.height / img.width));
        if (sH > MAX_DIM) {
            sH = MAX_DIM;
            sW = Math.round(MAX_DIM * (img.width / img.height));
        }

        tempCanvas.width = sW;
        tempCanvas.height = sH;
        tempCtx.drawImage(img, 0, 0, sW, sH);
        const imgData = tempCtx.getImageData(0, 0, sW, sH).data;

        const newVoxels = [];
        for (let y = 0; y < sH; y++) {
            for (let x = 0; x < sW; x++) {
                const idx = (y * sW + x) * 4;
                const r = imgData[idx];
                const g = imgData[idx + 1];
                const b = imgData[idx + 2];
                const alpha = imgData[idx + 3];
                const brightness = (r * 0.299 + g * 0.587 + b * 0.114);

                if (alpha > 10 && brightness > BRIGHTNESS_THRESHOLD) {
                    newVoxels.push({
                        gridX: x - sW / 2,
                        gridY: y - sH / 2,
                        brightness: brightness,
                        phase: Math.random() * Math.PI * 2,
                    });
                }
            }
        }
        voxels = newVoxels;
        isImageLoaded = true;

        currentImageDims = { sW, sH };
        recomputeScales();
    };
}

function loadNextImage() {
    if (imagePaths.length === 0) return;
    currentPath = imagePaths[currentImageIndex];
    _loadImageAt(currentPath);
    currentImageIndex = (currentImageIndex + 1) % imagePaths.length;
}

function reloadCurrentImage() {
    if (currentPath) _loadImageAt(currentPath);
}

window.forceNextImage = loadNextImage;

function applyDensity() {
    const newDim = DENSITY_LEVELS[densityIndex];
    if (newDim === MAX_DIM) return;
    MAX_DIM = newDim;
    recomputeScales();
    if (currentPath) {
        reloadCurrentImage();
    } else if (imagePaths.length > 0) {
        loadNextImage();
    }
}

window.__voxelEngine = {
    nextImage: () => loadNextImage(),
    densityUp: () => {
        if (densityIndex < DENSITY_LEVELS.length - 1) {
            densityIndex++;
            applyDensity();
        }
    },
    densityDown: () => {
        if (densityIndex > 0) {
            densityIndex--;
            applyDensity();
        }
    },
    getDensity: () => MAX_DIM,
};

setInterval(() => { if (imagePaths.length > 1) loadNextImage(); }, 35000);

let lastTime = performance.now();

function renderVoxels() {
    const now = performance.now();
    const dt = Math.min(0.1, (now - lastTime) / 1000);
    lastTime = now;
    const time = now * 0.001;

    // ===== 1. BACKGROUND =====
    if (bgTexture) {
        ctx.drawImage(bgTexture, 0, 0);
    } else {
        ctx.fillStyle = '#010204';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // ===== 2. CHUVA DIGITAL =====
    for (let i = 0; i < rainDrops.length; i++) {
        const drop = rainDrops[i];
        drop.y += drop.speed * dt;
        if (drop.y - drop.length > canvas.height) {
            drop.y = -drop.length;
            drop.x = Math.random() * canvas.width;
        }
        const yNorm = Math.min(1, drop.y / canvas.height);
        const dropAlpha = drop.alpha * (0.4 + yNorm * 0.6);
        ctx.fillStyle = `rgba(255, 0, 80, ${dropAlpha})`;
        ctx.fillRect(drop.x, drop.y - drop.length, 1, drop.length);
        // Cabeca mais brilhante
        ctx.fillStyle = `rgba(255, 100, 150, ${Math.min(1, dropAlpha * 1.6)})`;
        ctx.fillRect(drop.x, drop.y - 4, 1, 4);
    }

    // ===== 3. SCANLINE =====
    const scanY = ((time * SCANLINE_SPEED) % (canvas.height + SCANLINE_HEIGHT * 2)) - SCANLINE_HEIGHT;
    const scanGrad = ctx.createLinearGradient(
        0, scanY - SCANLINE_HEIGHT / 2, 0, scanY + SCANLINE_HEIGHT / 2
    );
    scanGrad.addColorStop(0, 'rgba(255, 0, 60, 0)');
    scanGrad.addColorStop(0.5, `rgba(255, 0, 60, ${SCANLINE_ALPHA})`);
    scanGrad.addColorStop(1, 'rgba(255, 0, 60, 0)');
    ctx.fillStyle = scanGrad;
    ctx.fillRect(0, scanY - SCANLINE_HEIGHT / 2, canvas.width, SCANLINE_HEIGHT);

    // ===== 4. GLITCH OCASIONAL =====
    if (Math.random() < GLITCH_PROBABILITY) {
        const gy = Math.random() * canvas.height;
        const gh = 1 + Math.random() * 3;
        const ga = 0.3 + Math.random() * 0.4;
        ctx.fillStyle = `rgba(255, 0, 60, ${ga})`;
        ctx.fillRect(0, gy, canvas.width, gh);
    }

    // ===== 5. LINHAS DA IMAGEM =====
    mouseX += (targetMouseX - mouseX) * 0.03;
    mouseY += (targetMouseY - mouseY) * 0.03;

    if (isImageLoaded && voxels.length > 0) {
        const centerX = (canvas.width / 2) + (mouseX * MOUSE_PARALLAX_PX);
        const centerY = (canvas.height / 2) + (mouseY * MOUSE_PARALLAX_PX);

        voxels.sort((a, b) => a.brightness - b.brightness);
        const baseWidth = Math.max(0.65, lineWidth * projMultiplier);

        for (let i = 0; i < voxels.length; i++) {
            const v = voxels[i];
            const bNorm = v.brightness / 255;
            const z = bNorm - 0.5;
            const radialScale = 1.0 + z * Z_RADIAL_FACTOR;

            const projX = centerX + v.gridX * projMultiplier * radialScale;
            const projY = centerY + v.gridY * projMultiplier * radialScale;

            const pulse = 1.0 + Math.sin(time * 2.0 + v.phase) * LINE_PULSE_AMP;
            const heightUnits = lineHeightMin + bNorm * lineHeightRange;
            const height = heightUnits * projMultiplier * pulse;

            const yBottom = projY;
            const yTop = yBottom - height;

            if (projX < -10 || projX > canvas.width + 10) continue;
            if (yBottom < -10 || yTop > canvas.height + 10) continue;

            const alpha = Math.min(1.0, (v.brightness + 25) / 200);
            const r = Math.floor(200 + bNorm * 55);
            const g = Math.floor(bNorm * 25);
            const b = Math.floor(40 + bNorm * 110);

            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha * 0.55})`;
            ctx.fillRect(projX - baseWidth / 2, yTop, baseWidth, height);

            if (LINE_TOP_GLOW > 0) {
                const topH = height * 0.3;
                const gr = Math.floor(220 + bNorm * 35);
                const gg = Math.floor(80 + bNorm * 90);
                const gb = Math.floor(120 + bNorm * 100);
                ctx.fillStyle = `rgba(${gr}, ${gg}, ${gb}, ${alpha * LINE_TOP_GLOW})`;
                ctx.fillRect(projX - baseWidth / 2, yTop, baseWidth, topH);
            }

            if (v.brightness > 220) {
                const starGlow = (Math.sin(time * 0.8 + v.phase) + 1) * 0.5;
                if (starGlow > 0.6) {
                    ctx.fillStyle = `rgba(255, 255, 255, ${starGlow * 0.7})`;
                    ctx.fillRect(projX - baseWidth / 2, yTop, baseWidth, Math.min(4, height));
                }
            }
        }
    }

    requestAnimationFrame(renderVoxels);
}
renderVoxels();