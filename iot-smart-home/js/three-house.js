/**
 * 3D Animated Futuristic Smart Villa using Three.js
 */

class SmartHouse3D {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.houseGroup = new THREE.Group();
    this.particles = null;
    this.lights = {};
    this.mouseX = 0;
    this.mouseY = 0;
    this.targetRotationX = 0.25;
    this.targetRotationY = -0.55;
    this.isMouseDown = false;
    this.previousMousePosition = { x: 0, y: 0 };
    this.clock = new THREE.Clock();
    this.roomLightsOn = true;

    this.init();
  }

  init() {
    const width = this.container.clientWidth || 800;
    const height = this.container.clientHeight || 550;

    // Scene
    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(0x0a0e1a, 0.035);

    // Camera
    this.camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 1000);
    this.camera.position.set(16, 12, 22);
    this.camera.lookAt(0, 1.5, 0);

    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.1;
    this.container.appendChild(this.renderer.domElement);

    // Add Scene Content
    this.setupLighting();
    this.buildGround();
    this.buildVilla();
    this.buildSolarRoof();
    this.buildCarportAndEV();
    this.buildLandscaping();
    this.buildParticleConstellation();

    this.scene.add(this.houseGroup);

    // Event Listeners
    this.setupInteractions();

    // Start Loop
    this.animate();
  }

  setupLighting() {
    const ambientLight = new THREE.AmbientLight(0x1e293b, 1.4);
    this.scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.8);
    dirLight.position.set(20, 30, 15);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    dirLight.shadow.camera.near = 0.5;
    dirLight.shadow.camera.far = 60;
    dirLight.shadow.camera.left = -15;
    dirLight.shadow.camera.right = 15;
    dirLight.shadow.camera.top = 15;
    dirLight.shadow.camera.bottom = -15;
    dirLight.shadow.bias = -0.0005;
    this.scene.add(dirLight);

    const rimLight = new THREE.DirectionalLight(0x8b5cf6, 1.5);
    rimLight.position.set(-15, 10, -20);
    this.scene.add(rimLight);

    const livingLight = new THREE.PointLight(0xf59e0b, 2.5, 12);
    livingLight.position.set(0, 2.2, 1);
    livingLight.castShadow = true;
    this.houseGroup.add(livingLight);
    this.lights.living = livingLight;

    const bedroomLight = new THREE.PointLight(0x06b6d4, 2.2, 10);
    bedroomLight.position.set(1.5, 5.2, -0.5);
    this.houseGroup.add(bedroomLight);
    this.lights.bedroom = bedroomLight;

    const patioLight = new THREE.PointLight(0xa855f7, 2.0, 8);
    patioLight.position.set(-3.5, 2.0, 3.2);
    this.houseGroup.add(patioLight);
    this.lights.patio = patioLight;
  }

  buildGround() {
    const baseGeo = new THREE.CylinderGeometry(14, 15, 0.8, 64);
    const baseMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.8,
      metalness: 0.2
    });
    const baseMesh = new THREE.Mesh(baseGeo, baseMat);
    baseMesh.position.y = -0.4;
    baseMesh.receiveShadow = true;
    this.scene.add(baseMesh);

    const ringGeo = new THREE.TorusGeometry(14.05, 0.08, 16, 100);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = Math.PI / 2;
    ringMesh.position.y = -0.01;
    this.scene.add(ringMesh);

    const grid = new THREE.GridHelper(26, 26, 0x06b6d4, 0x1e293b);
    grid.position.y = 0.01;
    grid.material.opacity = 0.35;
    grid.material.transparent = true;
    this.scene.add(grid);

    const pathGeo = new THREE.PlaneGeometry(2.2, 7);
    const pathMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.9,
      metalness: 0.1
    });
    const path = new THREE.Mesh(pathGeo, pathMat);
    path.rotation.x = -Math.PI / 2;
    path.position.set(0, 0.02, 7.5);
    path.receiveShadow = true;
    this.scene.add(path);
  }

  buildVilla() {
    const darkConcrete = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.7,
      metalness: 0.2
    });

    const warmWood = new THREE.MeshStandardMaterial({
      color: 0x78350f,
      roughness: 0.6,
      metalness: 0.1
    });

    const smartGlass = new THREE.MeshPhysicalMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.45,
      roughness: 0.1,
      metalness: 0.1,
      transmission: 0.8,
      ior: 1.5,
      reflectivity: 0.9
    });

    const glowNeonCyan = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });

    // LEVEL 1
    const l1Geo = new THREE.BoxGeometry(8, 3.2, 6.5);
    const l1Mesh = new THREE.Mesh(l1Geo, darkConcrete);
    l1Mesh.position.set(0, 1.6, 0);
    l1Mesh.castShadow = true;
    l1Mesh.receiveShadow = true;
    this.houseGroup.add(l1Mesh);

    const glassGeo = new THREE.BoxGeometry(6.8, 2.6, 0.15);
    const frontGlass = new THREE.Mesh(glassGeo, smartGlass);
    frontGlass.position.set(0, 1.5, 3.28);
    this.houseGroup.add(frontGlass);

    const couchBaseGeo = new THREE.BoxGeometry(3.2, 0.6, 1.2);
    const couchMat = new THREE.MeshStandardMaterial({ color: 0x334155 });
    const couch = new THREE.Mesh(couchBaseGeo, couchMat);
    couch.position.set(0, 0.5, 1.2);
    couch.castShadow = true;
    this.houseGroup.add(couch);

    const tvGeo = new THREE.BoxGeometry(3.0, 1.6, 0.08);
    const tvMat = new THREE.MeshBasicMaterial({ color: 0x0ea5e9 });
    const tv = new THREE.Mesh(tvGeo, tvMat);
    tv.position.set(0, 1.8, -3.15);
    this.houseGroup.add(tv);

    // LEVEL 2
    const l2Geo = new THREE.BoxGeometry(7, 3.0, 7.5);
    const l2Mesh = new THREE.Mesh(l2Geo, darkConcrete);
    l2Mesh.position.set(1.2, 4.7, 0.8);
    l2Mesh.castShadow = true;
    l2Mesh.receiveShadow = true;
    this.houseGroup.add(l2Mesh);

    const woodWallGeo = new THREE.BoxGeometry(0.2, 2.8, 5.0);
    const woodWall = new THREE.Mesh(woodWallGeo, warmWood);
    woodWall.position.set(4.72, 4.7, 0.8);
    this.houseGroup.add(woodWall);

    const bedGlassGeo = new THREE.BoxGeometry(5.4, 2.5, 0.15);
    const bedGlass = new THREE.Mesh(bedGlassGeo, smartGlass);
    bedGlass.position.set(1.2, 4.6, 4.56);
    this.houseGroup.add(bedGlass);

    const stripGeo = new THREE.BoxGeometry(7.0, 0.08, 0.08);
    const stripMesh = new THREE.Mesh(stripGeo, glowNeonCyan);
    stripMesh.position.set(1.2, 3.16, 4.5);
    this.houseGroup.add(stripMesh);

    const railGeo = new THREE.BoxGeometry(3.5, 0.8, 0.05);
    const railMesh = new THREE.Mesh(railGeo, smartGlass);
    railMesh.position.set(-3.2, 3.6, 2.5);
    this.houseGroup.add(railMesh);
  }

  buildSolarRoof() {
    const roofGeo = new THREE.BoxGeometry(7.4, 0.3, 7.9);
    const roofMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.5 });
    const roof = new THREE.Mesh(roofGeo, roofMat);
    roof.position.set(1.2, 6.35, 0.8);
    this.houseGroup.add(roof);

    const panelMat = new THREE.MeshStandardMaterial({
      color: 0x172554,
      roughness: 0.2,
      metalness: 0.8,
      emissive: 0x1d4ed8,
      emissiveIntensity: 0.25
    });

    for (let r = 0; r < 2; r++) {
      for (let c = 0; c < 3; c++) {
        const panelGeo = new THREE.BoxGeometry(1.8, 0.06, 2.2);
        const panel = new THREE.Mesh(panelGeo, panelMat);
        panel.rotation.x = -0.15;
        panel.position.set(-0.6 + c * 2.0, 6.6, -0.6 + r * 2.6);
        this.houseGroup.add(panel);
      }
    }

    const mastGeo = new THREE.CylinderGeometry(0.04, 0.08, 1.8, 12);
    const mastMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.9 });
    const mast = new THREE.Mesh(mastGeo, mastMat);
    mast.position.set(4.0, 7.2, -1.8);
    this.houseGroup.add(mast);

    const beaconGeo = new THREE.SphereGeometry(0.12, 16, 16);
    const beaconMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
    this.beaconMesh = new THREE.Mesh(beaconGeo, beaconMat);
    this.beaconMesh.position.set(4.0, 8.1, -1.8);
    this.houseGroup.add(this.beaconMesh);
  }

  buildCarportAndEV() {
    const canopyGeo = new THREE.BoxGeometry(4.5, 0.25, 6.0);
    const canopyMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.5 });
    const canopy = new THREE.Mesh(canopyGeo, canopyMat);
    canopy.position.set(-5.8, 2.8, 0.5);
    canopy.castShadow = true;
    this.houseGroup.add(canopy);

    const pillarGeo = new THREE.CylinderGeometry(0.08, 0.08, 2.8, 12);
    const pillarMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.8 });
    const p1 = new THREE.Mesh(pillarGeo, pillarMat);
    p1.position.set(-7.8, 1.4, 3.2);
    const p2 = new THREE.Mesh(pillarGeo, pillarMat);
    p2.position.set(-7.8, 1.4, -2.2);
    this.houseGroup.add(p1);
    this.houseGroup.add(p2);

    const carBodyGeo = new THREE.BoxGeometry(2.4, 0.8, 4.4);
    const carBodyMat = new THREE.MeshStandardMaterial({
      color: 0x0284c7,
      roughness: 0.3,
      metalness: 0.7
    });
    const carBody = new THREE.Mesh(carBodyGeo, carBodyMat);
    carBody.position.set(-5.8, 0.6, 0.5);
    carBody.castShadow = true;
    this.houseGroup.add(carBody);

    const cabinGeo = new THREE.BoxGeometry(2.0, 0.65, 2.4);
    const cabinMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.1 });
    const cabin = new THREE.Mesh(cabinGeo, cabinMat);
    cabin.position.set(-5.8, 1.25, 0.2);
    this.houseGroup.add(cabin);

    const lightGeo = new THREE.BoxGeometry(0.6, 0.12, 0.06);
    const headLightMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
    const hl1 = new THREE.Mesh(lightGeo, headLightMat);
    hl1.position.set(-6.5, 0.65, 2.72);
    const hl2 = new THREE.Mesh(lightGeo, headLightMat);
    hl2.position.set(-5.1, 0.65, 2.72);
    this.houseGroup.add(hl1);
    this.houseGroup.add(hl2);

    const chargerGeo = new THREE.BoxGeometry(0.4, 0.8, 0.3);
    const chargerMat = new THREE.MeshStandardMaterial({ color: 0x0f172a });
    const charger = new THREE.Mesh(chargerGeo, chargerMat);
    charger.position.set(-3.9, 1.4, 0.2);
    this.houseGroup.add(charger);

    const ledGeo = new THREE.SphereGeometry(0.06, 12, 12);
    const ledMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
    const chargerLed = new THREE.Mesh(ledGeo, ledMat);
    chargerLed.position.set(-3.7, 1.5, 0.2);
    this.houseGroup.add(chargerLed);
  }

  buildLandscaping() {
    const createTree = (x, z, scale = 1.0) => {
      const treeGroup = new THREE.Group();
      
      const trunkGeo = new THREE.CylinderGeometry(0.12 * scale, 0.16 * scale, 1.2 * scale, 8);
      const trunkMat = new THREE.MeshStandardMaterial({ color: 0x334155 });
      const trunk = new THREE.Mesh(trunkGeo, trunkMat);
      trunk.position.y = 0.6 * scale;
      treeGroup.add(trunk);

      const coneMat = new THREE.MeshStandardMaterial({
        color: 0x065f46,
        roughness: 0.7,
        flatShading: true
      });
      const cone1 = new THREE.Mesh(new THREE.ConeGeometry(1.2 * scale, 1.8 * scale, 7), coneMat);
      cone1.position.y = 1.8 * scale;
      cone1.castShadow = true;
      treeGroup.add(cone1);

      const cone2 = new THREE.Mesh(new THREE.ConeGeometry(0.9 * scale, 1.5 * scale, 7), coneMat);
      cone2.position.y = 2.6 * scale;
      cone2.castShadow = true;
      treeGroup.add(cone2);

      treeGroup.position.set(x, 0, z);
      this.scene.add(treeGroup);
    };

    createTree(8.5, 5.0, 1.1);
    createTree(9.8, -3.5, 1.3);
    createTree(-9.5, -4.5, 0.9);
    createTree(-8.8, 6.2, 1.0);
  }

  buildParticleConstellation() {
    const particleCount = 200;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const c1 = new THREE.Color(0x06b6d4);
    const c2 = new THREE.Color(0x8b5cf6);

    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3;
      positions[i3] = (Math.random() - 0.5) * 35;
      positions[i3 + 1] = Math.random() * 18 + 0.5;
      positions[i3 + 2] = (Math.random() - 0.5) * 35;

      const mixed = c1.clone().lerp(c2, Math.random());
      colors[i3] = mixed.r;
      colors[i3 + 1] = mixed.g;
      colors[i3 + 2] = mixed.b;
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 0.18,
      vertexColors: true,
      transparent: true,
      opacity: 0.75,
      blending: THREE.AdditiveBlending
    });

    this.particles = new THREE.Points(geometry, material);
    this.scene.add(this.particles);
  }

  setupInteractions() {
    this.container.addEventListener("mousedown", (e) => {
      this.isMouseDown = true;
      this.previousMousePosition = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener("mouseup", () => {
      this.isMouseDown = false;
    });

    window.addEventListener("mousemove", (e) => {
      const rect = this.container.getBoundingClientRect();
      const clientX = e.clientX - rect.left;
      const clientY = e.clientY - rect.top;

      if (this.isMouseDown) {
        const deltaX = e.clientX - this.previousMousePosition.x;
        const deltaY = e.clientY - this.previousMousePosition.y;

        this.targetRotationY += deltaX * 0.006;
        this.targetRotationX = Math.max(0.05, Math.min(0.65, this.targetRotationX + deltaY * 0.004));

        this.previousMousePosition = { x: e.clientX, y: e.clientY };
      } else {
        this.mouseX = (clientX / rect.width) * 2 - 1;
        this.mouseY = -(clientY / rect.height) * 2 + 1;
      }
    });

    this.container.addEventListener("touchstart", (e) => {
      if (e.touches.length === 1) {
        this.isMouseDown = true;
        this.previousMousePosition = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      }
    }, { passive: true });

    window.addEventListener("touchend", () => {
      this.isMouseDown = false;
    });

    window.addEventListener("touchmove", (e) => {
      if (this.isMouseDown && e.touches.length === 1) {
        const deltaX = e.touches[0].clientX - this.previousMousePosition.x;
        const deltaY = e.touches[0].clientY - this.previousMousePosition.y;
        this.targetRotationY += deltaX * 0.008;
        this.targetRotationX = Math.max(0.05, Math.min(0.65, this.targetRotationX + deltaY * 0.005));
        this.previousMousePosition = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      }
    }, { passive: true });

    window.addEventListener("resize", () => {
      if (!this.container) return;
      const w = this.container.clientWidth;
      const h = this.container.clientHeight;
      if (w && h) {
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
      }
    });
  }

  toggleLights() {
    this.roomLightsOn = !this.roomLightsOn;
    const targetIntensity = this.roomLightsOn ? 2.5 : 0.2;
    if (this.lights.living) this.lights.living.intensity = targetIntensity;
    if (this.lights.bedroom) this.lights.bedroom.intensity = this.roomLightsOn ? 2.2 : 0.1;
    if (this.lights.patio) this.lights.patio.intensity = this.roomLightsOn ? 2.0 : 0.1;
    return this.roomLightsOn;
  }

  resetView() {
    this.targetRotationX = 0.25;
    this.targetRotationY = -0.55;
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    const delta = this.clock.getDelta();
    const elapsedTime = this.clock.getElapsedTime();

    if (!this.isMouseDown) {
      this.targetRotationY += 0.0015;
      const parallaxX = this.mouseX * 0.1;
      const parallaxY = this.mouseY * 0.05;
      this.houseGroup.rotation.y += (this.targetRotationY + parallaxX - this.houseGroup.rotation.y) * 0.05;
      this.houseGroup.rotation.x += (this.targetRotationX + parallaxY - this.houseGroup.rotation.x) * 0.05;
    } else {
      this.houseGroup.rotation.y += (this.targetRotationY - this.houseGroup.rotation.y) * 0.15;
      this.houseGroup.rotation.x += (this.targetRotationX - this.houseGroup.rotation.x) * 0.15;
    }

    if (this.beaconMesh) {
      const pulse = (Math.sin(elapsedTime * 4) + 1) * 0.5;
      this.beaconMesh.scale.setScalar(0.8 + pulse * 0.5);
    }

    if (this.particles) {
      const positions = this.particles.geometry.attributes.position.array;
      for (let i = 0; i < positions.length; i += 3) {
        positions[i + 1] += delta * 0.4;
        if (positions[i + 1] > 18) {
          positions[i + 1] = 0.5;
        }
      }
      this.particles.geometry.attributes.position.needsUpdate = true;
      this.particles.rotation.y += delta * 0.02;
    }

    this.renderer.render(this.scene, this.camera);
  }
}

window.SmartHouse3D = SmartHouse3D;
