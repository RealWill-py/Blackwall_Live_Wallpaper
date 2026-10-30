/* === Blackwall HUD + Voxel Engine (Lines mode) === */
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
   MOTOR LINHAS (Blackwall-style)
   ==============================================================
   Cada pixel da grade vira uma linha vertical fina.
   - Altura proporcional ao brilho (claro = linha alta)
   - Corpo escuro embaixo, topo brilhante em cima
   - Oscilacao vertical (respiracao) da altura
   - Densidade do tray recria as linhas com granularidade diferente
   ============================================================== */

const canvas = document.getElementById('voxel-canvas');
const ctx = canvas.getContext('2d');

// -------- Configuracao --------
const DENSITY_LEVELS = [180, 260, 380, 520, 680];
const REFERENCE_DIM = 380;           // referencia de calibracao
let densityIndex = 2;                // 380 por padrao
let MAX_DIM = DENSITY_LEVELS[densityIndex];

// Imagem na tela
const FIT_PERCENT = 1.0;
const FILL_MODE = 'contain';

// ---- LINHAS ----
// Largura base das linhas (em unidades da grade). 0.22 ~ 1px em 1920.
const LINE_WIDTH_AT_REF = 0.22;

// Altura minima das linhas (para brilho = 0)
const LINE_HEIGHT_MIN_AT_REF = 1.0;

// Quanto a mais de altura cada ponto de brilho adiciona
const LINE_HEIGHT_RANGE_AT_REF = 2.8;

// Oscilacao vertical (respiracao das linhas)
const LINE_PULSE_AMP = 0.18;

// Topo brilhante (0 = sem, 1 = full)
const LINE_TOP_GLOW = 0.85;

// ---- GLOBAIS ----
const Z_RADIAL_FACTOR = 0.08;        // leve variacao radial por brilho
const MOUSE_PARALLAX_PX = 15;        // parallax do mouse
const BRIGHTNESS_THRESHOLD = 4;      // filtra pixels quase pretos

let projMultiplier = 1.0;
let lineWidth = LINE_WIDTH_AT_REF;
let lineHeightMin = LINE_HEIGHT_MIN_AT_REF;
let lineHeightRange = LINE_HEIGHT_RANGE_AT_REF;
let currentImageDims = null;

function recomputeScales() {
    // Escalas ajustam com a densidade para manter tamanho NA TELA
    // constante independente do nivel escolhido.
    const ratio = REFERENCE_DIM / MAX_DIM;
    lineWidth       = LINE_WIDTH_AT_REF          * ratio;
    lineHeightMin   = LINE_HEIGHT_MIN_AT_REF     * ratio;
    lineHeightRange = LINE_HEIGHT_RANGE_AT_REF   * ratio;

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

function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    recomputeScales();
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

function renderVoxels() {
    ctx.fillStyle = '#010204';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    mouseX += (targetMouseX - mouseX) * 0.03;
    mouseY += (targetMouseY - mouseY) * 0.03;

    if (isImageLoaded && voxels.length > 0) {
        const time = Date.now() * 0.001;
        const centerX = (canvas.width / 2) + (mouseX * MOUSE_PARALLAX_PX);
        const centerY = (canvas.height / 2) + (mouseY * MOUSE_PARALLAX_PX);

        // Escuros primeiro, claros por cima
        voxels.sort((a, b) => a.brightness - b.brightness);

        // Pre-calcula escala da largura (constante no frame)
        const baseWidth = Math.max(0.65, lineWidth * projMultiplier);

        for (let i = 0; i < voxels.length; i++) {
            const v = voxels[i];
            const bNorm = v.brightness / 255;
            const z = bNorm - 0.5;
            const radialScale = 1.0 + z * Z_RADIAL_FACTOR;

            const projX = centerX + v.gridX * projMultiplier * radialScale;
            const projY = centerY + v.gridY * projMultiplier * radialScale;

            // Altura: base + brilho * range + oscilacao
            const pulse = 1.0 + Math.sin(time * 2.0 + v.phase) * LINE_PULSE_AMP;
            const heightUnits = lineHeightMin + bNorm * lineHeightRange;
            const height = heightUnits * projMultiplier * pulse;

            const yBottom = projY;
            const yTop = yBottom - height;

            if (projX < -10 || projX > canvas.width + 10) continue;
            if (yBottom < -10 || yTop > canvas.height + 10) continue;

            // Alpha: quanto mais brilhante, mais opaco
            const alpha = Math.min(1.0, (v.brightness + 25) / 200);

            // Cor do corpo: vermelho profundo com toque de magenta
            const r = Math.floor(200 + bNorm * 55);
            const g = Math.floor(bNorm * 25);
            const b = Math.floor(40 + bNorm * 110);

            // ---- Corpo (parte de baixo, mais escuro) ----
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha * 0.55})`;
            ctx.fillRect(projX - baseWidth / 2, yTop, baseWidth, height);

            // ---- Topo brilhante (segundo passa, ~30% de cima) ----
            if (LINE_TOP_GLOW > 0) {
                const topH = height * 0.3;
                const gr = Math.floor(220 + bNorm * 35);
                const gg = Math.floor(80 + bNorm * 90);
                const gb = Math.floor(120 + bNorm * 100);
                ctx.fillStyle = `rgba(${gr}, ${gg}, ${gb}, ${alpha * LINE_TOP_GLOW})`;
                ctx.fillRect(projX - baseWidth / 2, yTop, baseWidth, topH);
            }

            // ---- Realce opcional para pixels muito claros (estrelas) ----
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