const canvas = document.getElementById('canvas');
let renderer = null;
function createDebugDiv() {
  const el = document.createElement('div');
  el.id = 'viewer-debug';
  el.style.position = 'absolute';
  el.style.right = '8px';
  el.style.bottom = '8px';
  el.style.background = 'rgba(255,255,255,0.9)';
  el.style.padding = '6px 8px';
  el.style.borderRadius = '6px';
  el.style.fontSize = '12px';
  el.style.zIndex = 20;
  el.innerText = 'viewer: initializing...';
  document.body.appendChild(el);
  return el;
}
const debugEl = createDebugDiv();

try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.setSize(window.innerWidth, window.innerHeight);
  // test context
  const gl = renderer.getContext && renderer.getContext();
  if (!gl) throw new Error('no WebGL context');
  // report GL info
  try {
    const dbg = gl.getExtension('WEBGL_debug_renderer_info');
    const vendor = dbg ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : 'unknown';
    const rendererStr = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'unknown';
    debugEl.innerText = `viewer: WebGL OK — ${vendor} / ${rendererStr}`;
    console.log('WebGL vendor/renderer:', vendor, rendererStr);
  } catch (e) {
    debugEl.innerText = 'viewer: WebGL OK';
  }
} catch (err) {
  console.warn('Failed to initialize renderer with existing canvas, creating fallback renderer:', err);
  debugEl.innerText = 'viewer: fallback renderer';
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.setSize(window.innerWidth, window.innerHeight);
  document.body.appendChild(renderer.domElement);
}
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xffffff);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 1, 10000);
camera.position.set(200, -350, 180);
camera.lookAt(100, 40, 0);

// Helpers and lighting
scene.add(new THREE.AxesHelper(20));
scene.add(new THREE.GridHelper(200, 40));
scene.add(new THREE.AmbientLight(0xffffff, 0.9));
const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
dirLight.position.set(100, 200, 100);
scene.add(dirLight);

// Red test cube for quick visibility check
const testCube = new THREE.Mesh(
  new THREE.BoxGeometry(5, 5, 5),
  new THREE.MeshStandardMaterial({ color: 0xff0000 })
);
testCube.position.set(0, 2.5, 0);
scene.add(testCube);

const loader = new THREE.GLTFLoader();
// Serve GLBs from viewer assets for easy single-folder distribution
const basePath = 'assets/3d/';
const files = {
  detailed: basePath + 'facility_detailed.glb',
  review: basePath + 'facility_review.glb',
  massing: basePath + 'facility_massing.glb'
};

let current = null;
// Orbit controls
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0, 0);
controls.update();

function loadScene(lod) {
  if (current) {
    scene.remove(current);
    current.traverse((o) => {
      if (o.isMesh && o.geometry) o.geometry.dispose();
      if (o.isMesh && o.material) {
        if (Array.isArray(o.material)) o.material.forEach(m => m.dispose?.());
        else o.material.dispose?.();
      }
    });
    current = null;
  }
  loader.load(files[lod], (gltf) => {
      console.log("GLB loaded:", gltf);

      const model = gltf.scene;
      scene.add(model);

      let meshCount = 0;
      let lineCount = 0;

      model.traverse((o) => {
        if (o.isMesh) {
          meshCount++;
          o.visible = true;
          o.frustumCulled = false;

          // Preserve original materials if present; only fix broken/missing materials
          if (!o.material) {
            o.material = new THREE.MeshStandardMaterial({ color: 0xcccccc });
          } else if (Array.isArray(o.material)) {
            o.material.forEach(m => {
              if (!m) return;
              m.transparent = false;
              m.opacity = 1.0;
              m.needsUpdate = true;
            });
          } else {
            o.material.transparent = false;
            o.material.opacity = 1.0;
            o.material.needsUpdate = true;
          }
        }
        if (o.isLine || o.isLineSegments) lineCount++;
      });

      console.log("meshCount =", meshCount, "lineCount =", lineCount);

      const debugBox = new THREE.Box3().setFromObject(model);
      const size = debugBox.getSize(new THREE.Vector3());
      const center = debugBox.getCenter(new THREE.Vector3());
      console.log("Bounds size:", size, "center:", center);

      // Expose diagnostics for easy Console inspection
      try {
        window.__viewerDiagnostics = {
          meshCount: meshCount,
          lineCount: lineCount,
          boundsSize: { x: size.x, y: size.y, z: size.z },
          boundsCenter: { x: center.x, y: center.y, z: center.z }
        };
      } catch (e) {
        // ignore if window isn't writable in some sandboxed contexts
      }

      // For the rest of the loader logic, use `current = model`
      current = model;


    // --- Ensure consistent orientation (toggle if needed) ---
    // If the model appears sideways, uncomment this:
    // current.rotation.x = -Math.PI / 2;

    // --- Compute bounds and frame camera ---
    const frameBox = new THREE.Box3().setFromObject(current);
    const frameSize = frameBox.getSize(new THREE.Vector3());
    const frameCenter = frameBox.getCenter(new THREE.Vector3());

    // Center model at origin for stable orbit
    current.position.sub(frameCenter);

    // Recompute bounds after centering
    const frameBox2 = new THREE.Box3().setFromObject(current);
    const frameSize2 = frameBox2.getSize(new THREE.Vector3());
    const frameCenter2 = frameBox2.getCenter(new THREE.Vector3());

    const maxDim = Math.max(frameSize2.x, frameSize2.y, frameSize2.z);
    const fov = camera.fov * (Math.PI / 180);

    // Camera distance that fits model in view
    let dist = maxDim / (2 * Math.tan(fov / 2));
    dist *= 1.8; // extra padding

    // Place camera on a diagonal
    camera.position.set(dist, -dist, dist);
    camera.near = Math.max(0.1, maxDim / 1000);
    camera.far = maxDim * 100;
    camera.updateProjectionMatrix();

    controls.target.set(0, 0, 0);
    controls.update();

    // Apply visibility filters
    updateVisibility();

  }, undefined, (err) => {
    console.error('GLB load failed:', err);
  });
}

function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}

document.getElementById('lod').addEventListener('change', (e) => loadScene(e.target.value));

// Simple layer toggle by name substring
function updateVisibility() {
  const arch = document.getElementById('arch').checked;
  const equip = document.getElementById('equip').checked;
  const elec = document.getElementById('elec').checked;
  const mech = document.getElementById('mech').checked;
  const plumb = document.getElementById('plumb').checked;
  if (!current) return;
  current.traverse((o) => {
    if (!o.name) { o.visible = true; return; }
    const n = o.name.toLowerCase();
    if (n.includes('heavy') || n.includes('light') || n.includes('class') || n.includes('slab')) {
      o.visible = arch;
    } else if (n.includes('lift') || n.includes('cabinet') || n.includes('charger') || n.includes('station')) {
      o.visible = equip;
    } else if (n.includes('cable') || n.includes('tray') || n.includes('duct')) {
      // elec/mech overlap in simple export
      o.visible = elec || mech;
    } else {
      // default: keep visible
      o.visible = true;
    }
  });
}

['arch','equip','elec','mech','plumb'].forEach(id => document.getElementById(id).addEventListener('change', updateVisibility));

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  if (controls) controls.update();
});

// initial
loadScene('detailed');
animate();
